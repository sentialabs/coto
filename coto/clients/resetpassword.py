from bs4 import BeautifulSoup
from pyotp import TOTP
from urllib import parse
import json
from . import BaseClient


class Client(BaseClient):
    REQUIRES_AUTHENTICATION = False
    _REDIRECT_URL = "https://console.aws.amazon.com/console/home?state=hashArgs%23&isauthcode=true"

    def __init__(self, session):
        super().__init__(session)
        self.__csrf_token = None

    def _csrf_token(self):
        if self.__csrf_token == None:
            self._get_tokens()

        return self.__csrf_token

    def _get_tokens(self):
        r = self.session()._get(
            'https://signin.aws.amazon.com/resetpassword'
        )

        if r.status_code != 200:
            raise Exception("failed get tokens")

        soup = BeautifulSoup(r.text, 'html.parser')
        meta = {
            m['name']: m['content']
            for m in soup.find_all('meta') if 'name' in m.attrs
        }

        if not 'csrf_token' in meta:
            raise Exception("failed get csrf_token")
        self.__csrf_token = meta['csrf_token']

    def _action(self, action, data=None, api="signin"):
        """
        Execute an action on the signin API.

        Args:
            action: Action to execute.
            data: Arguments for the action.

        Returns:
            dict: Action response.
        """
        if not data:
            data = {}

        data['action'] = action
        # data['redirect_uri'] = self._REDIRECT_URL
        data['csrf'] = self._csrf_token()

        r = self.session()._post(
            "https://signin.aws.amazon.com/{0}".format(api),
            data=data,
        )

        if r.status_code != 200:
            print(r.text)
            raise Exception("failed action {0}".format(action))

        out = json.loads(r.text)
        if out['state'].lower() != 'success':
            if 'Message' in out['properties']:
                raise Exception("failed action {0}: {1}".format(action, out['properties']['Message']))
            else:
                raise Exception("failed action {0}".format(action))

        return out['properties']

    def reset_password(self, reset_token_url, password):
        """
        Performs a password reset.
        """
        query = parse.parse_qs(parse.urlparse(reset_token_url).query)
        return self._action('resetPasswordSubmitForm', {
            'token': query['token'][0],
            'key': query['key'][0],
            'newpassword': password,
            'confirmpassword': password,
        }, api='resetpassword')
