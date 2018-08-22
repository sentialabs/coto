from bs4 import BeautifulSoup
from pyotp import TOTP
import json
from . import BaseClient


class Client(BaseClient):
    REQUIRES_AUTHENTICATION = False
    _REDIRECT_URL = "https://console.aws.amazon.com/console/home?state=hashArgs%23&isauthcode=true"

    def __init__(self, session):
        super().__init__(session)
        self._signin = self.session().client('signin_aws')

    def get_mfa_status(self, email):
        r = self.session()._post(
            "https://signin.aws.amazon.com/mfa",
            data={
                'email': email,
                '_redirect_url': self._REDIRECT_URL,
                'csrf': self._signin._csrf_token(),
                'sessionId': self._signin._session_id(),
            })

        if r.status_code != 200:
            raise Exception("failed get mfa status for {0}".format(email))

        return json.loads(r.text)
