from bs4 import BeautifulSoup
from pyotp import TOTP
from datetime import datetime, timedelta
import json
from . import BaseClient


class ReauthException(Exception):
    pass


class Client(BaseClient):
    """
    A low-level client representing Account:

    .. code-block:: python

        import coto

        session = coto.Session()
        client = session.client('support')

    These are the available methods:

    * :py:meth:`get_support_plan`
    * :py:meth:`update_support_plan`
    """
    def __init__(self, session):
        super().__init__(session)
        self.__xsrf_token = None

    def _url(self, api):
        return "https://console.aws.amazon.com/support/plans/service/{0}?state=hashArgs%23".format(api)

    def _xsrf_token(self):
        if self.__xsrf_token is None:
            self._get_xsrf_token()

        return self.__xsrf_token

    def _get_xsrf_token(self):
        r = self.session()._get(
            'https://console.aws.amazon.com/support/plans/home?region=eu-central-1&state=hashArgs%23'
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

    def get_support_plan(self):
        r = self._post('describeSupportLevelSummary', { "lang": "en" })
        return {
            'supportLevel': r['response']['supportLevel'],
            'canChange': r['response']['canChange']
        }

    def update_support_plan(self, support_plan):
        r = self._post('updateSupportLevel', { "supportLevel": support_plan })
        return {
            'supportLevel': r['response']['supportLevel']
        }