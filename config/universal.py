try:
    import urllib.parse
    quote = urllib.parse.quote
except:
    import urllib
    quote = urllib.quote_plus


from . import constants


BASE_URL = 'https://' + constants.HOST if constants.HTTPS else 'http://' + constants.HOST

BUSINESS_NAME = 'Origin Protocol'
CONTACT_EMAIL = 'info@originprotocol.com'

WHITEPAPER_URL = BASE_URL + '/whitepaper'

GITHUB_URL = 'https://github.com/originprotocol'
SLACK_URL = 'https://slack.originprotocol.com/'
DISCORD_URL = 'https://discord.gg/jyxpUSe'
TELEGRAM_URL = 'https://t.me/originprotocol'
TWITTER_URL = 'https://twitter.com/originprotocol'
FACEBOOK_URL = 'https://www.facebook.com/originprotocol'
IOS_URL = 'https://itunes.apple.com/app/origin-wallet/id1446091928'
ANDROID_URL = 'https://play.google.com/store/apps/details?id=com.origincatcher'
DAPP_URL = 'https://www.shoporigin.com'
REWARDS_URL = 'https://www.shoporigin.com/#/welcome'
FAUCET_URL = 'https://faucet.originprotocol.com'

DEFAULT_SHARE_MSG = quote('Check out ' + BUSINESS_NAME + ', an exciting blockchain project that will decentralize the sharing economy.')
DEFAULT_PARTICLE_ICON = constants.DEFAULT_PARTICLE_ICON
