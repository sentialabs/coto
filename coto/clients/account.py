from bs4 import BeautifulSoup
from pyotp import TOTP
from datetime import datetime, timedelta
import json
from . import BaseClient

import os

ACCOUNT_CONSOLE_URL = os.environ.get('ACCOUNT_CONSOLE_URL', 'https://console.aws.amazon.com/console/')
ACCOUNT_SIGNIN_URL = os.environ.get('ACCOUNT_SIGNIN_URL', 'https://signin.aws.amazon.com/updateaccount')

class ReauthException(Exception):
    pass


class Client(BaseClient):
    """
    A low-level client representing Account:

    .. code-block:: python

        import coto

        session = coto.Session()
        client = session.client('account')

    These are the available methods:

    * :py:meth:`get_account_info`
    * :py:meth:`update_account_name`
    * :py:meth:`update_account_email`
    * :py:meth:`update_account_password`
    """
    _REDIRECT_URL = ACCOUNT_CONSOLE_URL + "home?state=hashArgs%23&isauthcode=true"

    def __init__(self, session):
        super().__init__(session)
        self.__csrf_token = None

    def _csrf_token(self):
        if self.__csrf_token == None:
            self._get_tokens()

        return self.__csrf_token

    def _get_tokens(self):
        r = self.session()._get(
            ACCOUNT_SIGNIN_URL + '?redirect_uri=https%3A%2F%2Fconsole.aws.amazon.com%2Fbilling%2Fhome%23%2Faccount'
        )

        if r.status_code != 200:
            raise Exception("failed get tokens")

        soup = BeautifulSoup(r.text, 'html.parser')
        meta = {
            m['name']: m['content']
            for m in soup.find_all('meta') if 'name' in m.attrs
        }
        self.__csrf_token = meta['csrf_token']

    def _action(self, action, data=None):
        """
        Execute an action on the updateaccount API.

        Args:
            action: Action to execute.
            data: Arguments for the action.

        Returns:
            dict: Action response.

        Raises:
            :py:class:`coto.clients.decoupled_account.ReauthException`: You have to
                reauthenticate, then try again.
        """
        if not data:
            data = {}

        data['action'] = action
        data['redirect_uri'] = self._REDIRECT_URL
        data['csrf'] = self._csrf_token()

        r = self.session()._post(
            ACCOUNT_SIGNIN_URL,
            data=data,
        )

        if r.status_code != 200:
            print(r.text)
            raise Exception("failed action {0}".format(action))

        out = json.loads(r.text)
        if out['state'] == 'FAIL' and out['properties']['action'] == 'reAuth':
            raise ReauthException()

        if out['state'].lower() != 'success':
            if 'Message' in out['properties']:
                raise Exception("failed action {0}: {1}".format(action, out['properties']['Message']))
            else:
                raise Exception("failed action {0}".format(action))

        return out['properties']

    def get_account_info(self):
        """
        Gets the account name and email address.

        Request Syntax:
            .. code-block:: python

                response = client.get_auth_state()

        Returns:
            dict: Response Syntax

            .. code-block:: python

                {
                    'accountEmail': str,
                    'Message': str,
                    'accountName': str,
                    'Title': str,
                }

        Raises:
            :py:class:`coto.clients.decoupled_account.ReauthException`: You have to
                reauthenticate, then try again.
        """
        return self._action('getAuthState')

    def update_account_name(self, AccountName):
        """
        Sets a new account name.

        Request Syntax:
            .. code-block:: python

                response = client.update_account_name(
                    AccountName=str,
                )

        Returns:
            dict: Response Syntax

            .. code-block:: python

                {
                    'Message': str,
                    'Title': str,
                    'updatedAccountName': str
                }

        Raises:
            :py:class:`coto.clients.decoupled_account.ReauthException`: You have to
                reauthenticate, then try again.
        """
        return self._action('updateAccountName', {
            'newAccountName': AccountName,
        })

    def update_account_email(self, Password, AccountEmail):
        """
        Sets a new account email address.

        Request Syntax:
            .. code-block:: python

                response = client.update_account_email(
                    Password=str,
                    AccountEmail=str,
                )

        Args:
            Password (str): Current account password.
            AccountEmail (str): New account email.

        Returns:
            dict: Response Syntax

            .. code-block:: python

                {
                    'Message': str,
                    'Title': str,
                    'updatedAccountEmail': str
                }

        Raises:
            :py:class:`coto.clients.decoupled_account.ReauthException`: You have to
                reauthenticate, then try again.
        """
        return self._action('updateAccountEmail', {
            'password': Password,
            'newEmailAddress': AccountEmail,
        })

    def update_account_password(self, Password, NewPassword):
        """
        Sets a new account password.

        Request Syntax:
            .. code-block:: python

                response = client.update_account_password(
                    Password=str,
                    NewPassword=str,
                )

        Args:
            Password (str): Current account password.
            NewPassword (str): New account password.

        Returns:
            dict: Response Syntax

            .. code-block:: python

                {
                    'Message': str,
                    'Title': str,
                }

        Raises:
            :py:class:`coto.clients.decoupled_account.ReauthException`: You have to
                reauthenticate, then try again.
        """
        return self._action(
            'updateAccountPassword', {
                'oldpassword': Password,
                'newpassword': NewPassword,
                'newpassword1': NewPassword,
            })
