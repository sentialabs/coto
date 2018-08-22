from .. import BaseClient


class Client(BaseClient):
    REQUIRES_AUTHENTICATION = False

    def __init__(self, session):
        super().__init__(session)

        self._signin_aws = self.session().client('signin_aws')
        self._signin_amazon = self.session().client('signin_amazon')

    def signin(self, email, password, mfa_secret=None):
        # check account type
        account_type = self._signin_aws.get_account_type(email)

        if account_type == 'Decoupled':
            return self._signin_aws.signin(
                email,
                password,
                mfa_secret,
            )
        elif account_type == 'Coupled':
            return self._signin_amazon.signin(
                email,
                password,
                mfa_secret,
            )
        elif account_type == 'Unknown':
            raise Exception("account {0} not active".format(email))
        else:
            raise Exception("unsupported account type {0}".format(email))
