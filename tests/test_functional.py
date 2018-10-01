# test_app.py
import random
from faker import Faker

from flask import url_for

from config.constants import LANGUAGES
from database.db_models import EmailList, Presale, Interest

from .factories import PresaleFactory, InterestFactory


fake = Faker()

def test_root_with_default_langs_returns_200(client):
    res = client.get(url_for('root'))
    assert res.status_code == 200


def test_root_without_default_lang_returns_302(client):
    res = client.get(url_for('root'), headers={"Accept-Language": "fr"}   )
    assert res.status_code == 302


def test_index_returns_200(client):
    res = client.get(url_for('index', lang_code=random.choice(LANGUAGES)))
    assert res.status_code == 200


def test_join_mailing_and_unsubscribe(mock_send_message, session, client):
    data = {
        "email": fake.safe_email(),
        "ip_addr": fake.ipv4(),
    }
    res = client.post(url_for('join_mailing_list'),
                      data=data)

    assert res.status_code == 200
    assert EmailList.query.filter_by(email=data['email']).first() is not None

    # try to unsubscribe the created EmailList object above
    res = client.get("{url}?email={param}".
                     format(url=url_for('unsubscribe'),
                            param=data['email']))

    assert res.status_code == 302
    assert EmailList.query.filter_by(email=data['email'],
                                     unsubscribed=True).first() is not None


def test_join_presale(mock_send_message, mock_captcha, session, client):
    data = PresaleFactory.stub().__dict__
    data['confirm'] = True

    res = client.post(url_for('join_presale'), data=data)
    created_obj = Presale.query.filter_by(email=data['email']).first()

    assert created_obj.id is not None
    assert res.status_code == 200


def test_partners_interest(mock_send_message, mock_captcha, session, client):
    data = InterestFactory.stub().__dict__
    data['confirm'] = True

    res = client.post(url_for('partners_interest'), data=data)
    created_obj = Interest.query.filter_by(email=data['email']).first()

    assert created_obj.id is not None
    assert res.status_code == 200
