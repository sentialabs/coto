class BaseClient:
    REQUIRES_AUTHENTICATION = True

    def __init__(self, session):
        self._session = session

    def session(self):
        return self._session

from . import billing
from . import account
from . import federation
from . import iam
from . import mfa
from . import support
from . import resetpassword
from . import signin
from . import signin_amazon
from . import signin_aws
