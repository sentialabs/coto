from bs4 import BeautifulSoup
from pyotp import TOTP
from datetime import datetime, timedelta
import json
from . import BaseClient

import os

SUPPORT_URL = os.environ.get('SUPPORT_URL', 'https://console.aws.amazon.com/support/')
SUPPORT_REGION = os.environ.get('SUPPORT_REGION', 'eu-central-1')

class ReauthException(Exception):
    pass


class Client(BaseClient):
    """
    A low-level client representing Support:

    .. code-block:: python

        import coto

        session = coto.Session()
        client = session.client('support')

    These are the available methods:

    * :py:meth:`get_support_level`
    * :py:meth:`update_support_level`
    """
    def __init__(self, session):
        super().__init__(session)
        self.__xsrf_token = None

    def _url(self, api):
        return SUPPORT_URL + "plans/service/{0}?state=hashArgs%23".format(api)

    def _xsrf_token(self):
        if self.__xsrf_token is None:
            self._get_xsrf_token()

        return self.__xsrf_token

    def _get_xsrf_token(self):
        r = self.session()._get(
            SUPPORT_URL + 'plans/home?region=' + SUPPORT_REGION + '&state=hashArgs%23'
        )
        
        if r.status_code != 200:
            raise Exception("failed get support xsrf token")

        for cookie in r.cookies:
            if cookie.name == 'XSRF-TOKEN':
                self.__xsrf_token = cookie.value
                break

    def _get(self, api):
        r = self.session()._get(
            self._url(api), headers={'X-XSRF-TOKEN': self._xsrf_token()})

        if 'X-CSRF-TOKEN' in r.headers:
            self.__xsrf_token = r.headers['X-CSRF-Token']

        if r.status_code != 200:
            raise Exception("failed get {0}".format(api))

        return json.loads(r.text)

    def _post(self, api, data=None):
        r = self.session()._post(
            self._url(api),
            headers={
                'Content-Type': 'application/json',
                'X-XSRF-TOKEN': self._xsrf_token(),
            },
            data=json.dumps(data) if data is not None else None,
        )

        if 'X-CSRF-Token' in r.headers:
            self.__xsrf_token = r.headers['X-CSRF-TOKEN']

        if r.status_code != 200:
            raise Exception("failed post {0}".format(api))

        return json.loads(r.text)

    def get_support_level(self):
        """
        Lists the current support contract level for the account.

        Request Syntax:
            .. code-block:: python

                response = client.get_support_level()

        Returns:
            dict: Response Syntax

            .. code-block:: python

                {
                    'supportLevel': str,
                    'canChange': bool
                }
        """
        r = self._post('describeSupportLevelSummary', { "lang": "en" })
        return {
            'supportLevel': r['response']['supportLevel'],
            'canChange': r['response']['canChange']
        }

    def update_support_level(self, support_level):
        """
        Change the support contract level for the account.

        Request Syntax:
            .. code-block:: python

                response = client.set_tax_registration(
                    support_level=str,
                )

        Args:
            support_level (str): Desired support contract level.

        Returns:
            dict: Response Syntax

            .. code-block:: python

                {
                    'supportLevel': str
                }
        """
        r = self._post('updateSupportLevel', { "supportLevel": support_level })
        return {
            'supportLevel': r['response']['supportLevel']
        }
