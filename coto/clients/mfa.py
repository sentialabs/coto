from bs4 import BeautifulSoup
from pyotp import TOTP
import json
from . import BaseClient

import os

MFA_CONSOLE_URL = os.environ.get('MFA_CONSOLE_URL', 'https://console.aws.amazon.com/console/')
MFA_SIGNIN_URL = os.environ.get('MFA_SIGNIN_URL', 'https://signin.aws.amazon.com/mfa')

class Client(BaseClient):
    REQUIRES_AUTHENTICATION = False
    _REDIRECT_URL = MFA_CONSOLE_URL + "home?state=hashArgs%23&isauthcode=true"

    def __init__(self, session):
        super().__init__(session)
        self._signin = self.session().client('signin_aws')

    def get_mfa_status(self, email):
        r = self.session()._post(
            MFA_SIGNIN_URL,
            data={
                'email': email,
                '_redirect_url': self._REDIRECT_URL,
                'csrf': self._signin._csrf_token(),
                'sessionId': self._signin._session_id(),
            })

        if r.status_code != 200:
            raise Exception("failed get mfa status for {0}".format(email))

        return json.loads(r.text)
