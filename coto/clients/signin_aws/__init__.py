from bs4 import BeautifulSoup
from pyotp import TOTP
from urllib import parse
import json
from .. import BaseClient
from . import exceptions
import time


def captcha_decorator(func):
    def wrapper(*args, **kwargs):
        self = args[0]

        captcha_guess = kwargs.get('captcha_guess')
        solver = self.session()._captcha_solver
        guess_uuid = None

        while True:
            try:
                _kwargs = {k: v for k, v in kwargs.items()}
                if captcha_guess:
                    _kwargs['captcha_guess'] = captcha_guess
                return func(*args, **_kwargs)
            except exceptions.CaptchaRequiredException as e:
                if solver is None:
                    raise

                if guess_uuid and captcha_guess and captcha_guess.action == e.action:
                    solver.incorrect(guess_uuid)

                guess_uuid = solver.solve(url=e.CaptchaURL)

                while True:
                    guess = solver.result(guess_uuid)

                    if guess is None:
                        time.sleep(5)
                    else:
                        break
                captcha_guess = e.guess(guess)
                continue
            break

    return wrapper


class Client(BaseClient):
    REQUIRES_AUTHENTICATION = False
    _REDIRECT_URL = "https://console.aws.amazon.com/console/home?state=hashArgs%23&isauthcode=true"

    def __init__(self, session):
        super().__init__(session)
        self.__csrf_token = None
        self.__session_id = None

    def _csrf_token(self):
        if self.__csrf_token == None:
            self._get_tokens()

        return self.__csrf_token

    def _session_id(self):
        if self.__session_id == None:
            self._get_tokens()

        return self.__session_id

    def _get_tokens(self):
        r = self.session()._get(
            "https://signin.aws.amazon.com/signin?redirect_uri=https%3A%2F%2Fconsole.aws.amazon.com%2Fconsole%2Fhome%3Fstate%3DhashArgs%2523%26isauthcode%3Dtrue&client_id=arn%3Aaws%3Aiam%3A%3A015428540659%3Auser%2Fhomepage&forceMobileApp=0"
        )

        if r.status_code != 200:
            raise Exception("failed get tokens")

        soup = BeautifulSoup(r.text, 'html.parser')
        meta = {
            m['name']: m['content']
            for m in soup.find_all('meta') if 'name' in m.attrs
        }
        self.__csrf_token = meta['csrf_token']
        self.__session_id = meta['session_id']

    def _action(self, action, data=None, api="signin", captcha_guess=None):
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
        data['redirect_uri'] = self._REDIRECT_URL
        data['csrf'] = self._csrf_token()
        data['sessionId'] = self._session_id()

        if captcha_guess and captcha_guess.action == action:
            data['captcha_token'] = captcha_guess.captcha_token
            data['captchaObfuscationToken'] = \
                captcha_guess.captchaObfuscationToken
            data['captcha_guess'] = captcha_guess.guess

        r = self.session()._post(
            "https://signin.aws.amazon.com/{}".format(api),
            data=data,
        )

        if r.status_code != 200:
            raise Exception("failed action {}: {}".format(action, r.text))

        out = json.loads(r.text)
        state = out.get('state', 'none').lower()
        properties = out.get('properties', {})

        if properties.get('Captcha',
                          'false') == 'true' and action != "captcha":
            raise exceptions.CaptchaRequiredException(
                properties['CES'], properties['CaptchaURL'],
                properties['captchaObfuscationToken'], action)

        if state != 'success':
            if 'Message' in properties:
                raise Exception("failed action {}: {}".format(
                    action, properties['Message']))
            else:
                raise Exception("failed action {}: {}".format(action, r.text))

        return properties

    @captcha_decorator
    def get_account_type(self, email, captcha_guess=None):
        """
        Determine the type of account.

        Account Types:
            Coupled: Coupled to an amazon.com account.
            Decoupled: Independend from amazon.com.
            Unknown: Non-existent account.

        Request Syntax:

            .. code-block:: python

                response = client.get_account_type(
                    email=str,
                )

        Args:
            email: Account email address.

        Returns:
            str: Account type
        """
        response = self._action(
            'resolveAccountType', {'email': email},
            captcha_guess=captcha_guess)
        return response['resolvedAccountType']

    def mfa_required(self, email):
        mfa_client = self.session().client('mfa')
        mfa = mfa_client.get_mfa_status(email)
        if 'mfaType' in mfa:
            if mfa['mfaType'] == 'NONE':
                return False
            else:
                return True

            return True

        return True

    def signin(self, email, password, mfa_secret=None):
        # check mfa
        mfa_required = self.mfa_required(email)
        if mfa_required and (mfa_secret is None or len(mfa_secret) == 0):
            raise Exception("account mfa protected but no secret provided")

        if not mfa_required:
            mfa_secret = None

        return self.signin_decoupled(email, password, mfa_secret)

    @captcha_decorator
    def signin_decoupled(self,
                         email,
                         password,
                         mfa_secret=None,
                         captcha_guess=None):
        """
        Signin into the AWS Management Console using account root user.

        Request Syntax:

            .. code-block:: python

                response = client.signin_decoupled(
                    email=str,
                    password=str,
                    mfa_secret=str,
                )

        Args:
            email: Account email address.
            password: Account password.
            mfa_secret: Account mfa secret. The Base32 seed defined as specified
                in RFC3548. The Base32StringSeed is Base64-encoded.

        Returns:
            bool: Signin successful
        """
        data = {
            'email': email,
            'password': password,
            'client_id': 'arn:aws:iam::015428540659:user/homepage',
        }

        if mfa_secret is not None:
            data['mfaType'] = 'OTP'
            data['mfa1'] = TOTP(mfa_secret).now()
            data['mfaSerial'] = 'undefined'

        # an exception is thrown if authentication was unsuccessful
        self._action('authenticateRoot', data, captcha_guess=captcha_guess)
        self.session().authenticated = True
        self.session().root = True
        return True

    def get_password_recovery_captcha(self):
        """
        Obtains a captcha for password recovery.

        The value ``CES`` must be used as ``captcha_token`` in
        :py:meth:`get_reset_password_token`.

        Returns:
            dict: Response Syntax

            .. code-block:: python

                {
                    'CES': str,
                    'Captcha': bool,
                    'CaptchaURL': str,
                    'captchaObfuscationToken': str,
                }
        """
        return self._action('captcha', {'forgotpassword': True})

    def raise_password_recovery_captcha(self):
        """
        Obtains a captcha for password recovery and raises a
        CaptchaRequiredException.
        """
        captcha = self.get_password_recovery_captcha()
        raise exceptions.CaptchaRequiredException(
            captcha['CES'], captcha['CaptchaURL'],
            captcha['captchaObfuscationToken'], 'getResetPasswordToken')

    @captcha_decorator
    def get_reset_password_token(self, email, captcha_guess=None):
        """
        Asks for a password reset token to be sent to the registered email
        address.

        The value token url from the resulting email must be used as
        ``reset_token_url`` in :py:meth:`reset_password`.

        Returns:
            dict: Response Syntax

            .. code-block:: python

                {
                    'recovery_result': 'email_sent'
                }
        """

        if not captcha_guess:
            self.raise_password_recovery_captcha()

        try:
            return self._action(
                'getResetPasswordToken', {'email': email},
                captcha_guess=captcha_guess)
        except Exception as e:
            if str(
                    e
            ) == "failed action getResetPasswordToken: Enter the characters and try again":
                self.raise_password_recovery_captcha()
