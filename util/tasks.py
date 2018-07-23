# -*- coding: utf-8 -*-
"""
This file handles asyncronous tasks.
Tasks are performed using Celery (http://www.celeryproject.org/)
Task functions are at bottom of file, and decorated with `@celery.task()`
"""

import os
import sendgrid
from celery import Celery
from config import constants
from flask import Flask
from database import db, db_models
from database.db_models import EmailList
from fullcontact import FullContact


def make_celery(app):
    celery = Celery(app.import_name, backend=os.environ['REDIS_URL'],
                    broker=os.environ['REDIS_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

flask_app = Flask(__name__)


# TODO: (Gzing) - A lot of celery configuration level stuff can be moved to app_config
# instead of being defined at multiple places.

flask_app.config.update(
    broker_url=os.environ['REDIS_URL'],
    result_backend=os.environ['REDIS_URL'],
    task_always_eager=(os.environ.get('CELERY_DEBUG') == 'True'),
    SQLALCHEMY_DATABASE_URI=constants.SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ECHO=False,
)

db.init_app(flask_app)
celery = make_celery(flask_app)


@celery.task()
def send_email(body):
    flask_app.logger.fatal("Sending email from Celery...")
    sg_api = sendgrid.SendGridAPIClient(apikey=constants.SENDGRID_API_KEY)
    sg_api.client.mail.send.post(request_body=body)


@celery.task()
def subscribe_email_list(**kwargs):
    email = kwargs.get('email')
    ip_addr = kwargs.get('ip_addr')
    if not email and ip_addr:
        return
    is_subscriber = EmailList.query.filter_by(email=email).first()
    if not is_subscriber:
        db.session.add(EmailList(email=email,
                                 ip_addr=ip_addr,
                                 unsubscribed=False))
        db.session.commit()


@celery.task(rate_limit='300/m', max_retries=3)
def full_contact_request(email):
    """ Request fullcontact info based on email """

    if (constants.FULLCONTACT_KEY is None):
        flask_app.logger.fatal("constants.FULLCONTACT_KEY is not set.")
        return

    flask_app.logger.info('Looking up %s', email)

    fc = FullContact(constants.FULLCONTACT_KEY)
    r = fc.person(email=email)

    MIN_RETRY_SECS = 300
    MAX_RETRY_SECS = 600

    code = int(r.status_code)
    if (code == 200) or (code == 404):
        # Success or not found
        # (We "not found" results in db too, so that we know we tried
        # and to move on to next email.)
        contact_json = r.json()
        fc_row = db_models.FullContact()
        fc_row.email = email
        fc_row.fullcontact_response = contact_json

        if 'socialProfiles' in contact_json:
            profiles = contact_json['socialProfiles']
            for profile in profiles:
                if 'typeId' in profile and 'username' in profile:
                    network = profile['typeId']
                    username = profile['username']
                    if network == 'angellist':
                        fc_row.angellist_handle = username
                    if network == 'github':
                        fc_row.github_handle = username
                    if network == 'twitter':
                        fc_row.twitter_handle = username
        flask_app.logger.info('%s logged in successfully', email)
        db.session.add(fc_row)
        db.session.commit()
    elif code == 403:
        # Key fail
        flask_app.logger.fatal("constants.FULLCONTACT_KEY is not set or is invalid.")
    elif code == 202:
        # We're requesting too quickly, randomly back off
        full_contact_request.retry(countdown=randint(MIN_RETRY_SECS, MAX_RETRY_SECS))
    else:
        flask_app.logger.fatal("FullContact request %s with status code %s",
                               email, r.status_code)
        flask_app.logger.fatal(r.json())
