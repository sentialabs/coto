from furl import furl
import json
import requests
from . import BaseClient


class Client(BaseClient):
    REQUIRES_AUTHENTICATION = False

    def __init__(self, session):
        super().__init__(session)

    def signin(self, boto3_session):
        """
        Signin using a boto3 session.

        This method uses the federation endpoint to obtain a signin token using
        the credentials in your boto3 session. The signin token is then used
        to signin into the AWS Management Console.

        Although possible, you are not encouraged to call this method directly,
        instead follow the following example.

        Example:
            .. code-block:: python

                import boto3
                import coto

                session = coto.Session(
                    boto3_session=boto3.Session()
                )

        Request Syntax:
            .. code-block:: python

                response = client.signin(
                    boto3_session=boto3.session.Session,
                )

        Args:
            boto3_session (boto3.session.Session): The boto3 session to use as
                provider for AWS credentials.

        Returns:
            bool: Signin succeeded.
        """
        r = self.session()._get(self.get_signin_url(boto3_session))
        if r.status_code != 200:
            raise Exception("failed session signin")

        self.session().authenticated = True
        return True

    def get_signin_url(self, boto3_session):
        """
        Signin using a boto3 session.

        This method uses the federation endpoint to obtain a signin token using
        the credentials in your boto3 session. The signin token is then used
        to signin into the AWS Management Console.

        Although possible, you are not encouraged to call this method directly,
        instead follow the following example.

        Example:
            .. code-block:: python

                import boto3
                import coto

                session = coto.Session(
                    boto3_session=boto3.Session()
                )

        Request Syntax:
            .. code-block:: python

                response = client.signin(
                    boto3_session=boto3.session.Session,
                )

        Args:
            boto3_session (boto3.session.Session): The boto3 session to use as
                provider for AWS credentials.

        Returns:
            bool: Signin succeeded.
        """
        url = furl('https://signin.aws.amazon.com/federation')

        url.args['Action'] = "login"
        url.args['Issuer'] = None
        url.args['Destination'] = "https://console.aws.amazon.com/"
        url.args['SigninToken'] = self.get_signin_token(boto3_session)

        return url.url

    def get_signin_token(self, boto3_session):
        """
        Obtain a signin token for a boto3 session.

        This method uses the federation endpoint to obtain a signin token using
        the credentials in your boto3 session.

        Request Syntax:
            .. code-block:: python

                response = client.get_signin_token(
                    boto3_session=boto3.session.Session,
                )

        Args:
            boto3_session (boto3.session.Session): The boto3 session to use as
                provider for AWS credentials.

        Returns:
            str: Signin token.
        """
        credentials = boto3_session.get_credentials()

        url = "https://signin.aws.amazon.com/federation"
        response = self.session()._get(
            url,
            params={
                "Action":
                "getSigninToken",
                "Session":
                json.dumps({
                    "sessionId": credentials.access_key,
                    "sessionKey": credentials.secret_key,
                    "sessionToken": credentials.token,
                })
            }
        )
        return json.loads(response.text)["SigninToken"]
