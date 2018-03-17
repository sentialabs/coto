from bs4 import BeautifulSoup
from pyotp import TOTP
import json


class Root:
    REDIRECT_URL = "https://console.aws.amazon.com/console/home?state=hashArgs%23&isauthcode=true"


    def __init__(self, session):
        self.session = session
        self._csrf_token = None
        self._session_id = None


    def csrf_token(self):
        if self._csrf_token == None:
            self.get_tokens()

        return self._csrf_token


    def session_id(self):
        if self._session_id == None:
            self.get_tokens()

        return self._session_id


    def get_tokens(self):
        r = self.session._get(
            "https://signin.aws.amazon.com/signin?redirect_uri=https%3A%2F%2Fconsole.aws.amazon.com%2Fconsole%2Fhome%3Fstate%3DhashArgs%2523%26isauthcode%3Dtrue&client_id=arn%3Aaws%3Aiam%3A%3A015428540659%3Auser%2Fhomepage&forceMobileApp=0"
        )

        if r.status_code != 200:
            raise Exception("failed get tokens")

        soup = BeautifulSoup(r.text, 'html.parser')
        meta = {
            m['name']: m['content']
            for m in soup.find_all('meta')
            if 'name' in m.attrs
        }
        self._csrf_token = meta['csrf_token']
        self._session_id = meta['session_id']


    def get_account_type(self, email):
        r = self.session._post(
            "https://signin.aws.amazon.com/signin",
            data={
                'action': 'resolveAccountType',
                'redirect_uri': self.REDIRECT_URL,
                'email': email,
                'csrf': self.csrf_token(),
                'sessionId': self.session_id(),
            }
        )

        if r.status_code != 200:
            raise Exception("failed get mfa status for {0}".format(email))

        result = json.loads(r.text)

        if not result['state'] == 'SUCCESS':
            raise Exception("unable to find account type for {0}".format(email))

        return result['properties']['resolvedAccountType']


    def get_mfa_status(self, email):
        r = self.session._post(
            "https://signin.aws.amazon.com/mfa",
            data={
                'email': email,
                'redirect_url': self.REDIRECT_URL,
                'csrf': self.csrf_token(),
                'sessionId': self.session_id(),
            }
        )

        if r.status_code != 200:
            raise Exception("failed get mfa status for {0}".format(email))

        return json.loads(r.text)


    def mfa_required(self, email):
        mfa = self.get_mfa_status(email)
        if 'mfaType' in mfa:
            if mfa['mfaType'] != 'SW':
                raise Exception("cannot handle hardware mfa tokens")

            return True

        return False


    def signin(self, email, password, mfa_secret=None):
        # check account type
        account_type = self.get_account_type(email)

        # check mfa
        mfa_required = self.mfa_required(email)
        if mfa_required and (mfa_secret is None or len(mfa_secret) == 0):
           raise Exception("account mfa protected but no secret provided")

        if not mfa_required:
            mfa_secret = None

        if account_type == 'Decoupled':
            return self.signin_decoupled(email, password, mfa_secret)
        elif account_type == 'Coupled':
            raise Exception("coupled account signin not supported {0}".format(email))
        elif account_type  == 'Unknown':
            raise Exception("account {0} not active".format(email))
        else:
            raise Exception("unsupported account type {0}".format(email))


    def signin_decoupled(self, email, password, mfa_secret=None):
        data = {
            'action': 'authenticateRoot',
            'email': email,
            'password': password,
            'redirect_uri': self.REDIRECT_URL,
            'client_id': 'arn:aws:iam::015428540659:user/homepage',
            'csrf': self.csrf_token(),
            'sessionId': self.session_id()
        }

        if mfa_secret is not None:
            data['mfa1'] = TOTP(mfa_secret).now()

        r = self.session._post("https://signin.aws.amazon.com/signin", data=data)
        if r.status_code != 200:
            raise Exception("failed to login {0}".format(email))

        result = json.loads(r.text)
        if result['state'] == 'SUCCESS':
            self.session.authenticated = True
            self.session.root = True
            return True
        else:
            raise Exception("failed to login {0}".format(email))
