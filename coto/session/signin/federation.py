from furl import furl
import json
import requests


def get_signin_url(session):
    url = furl('https://signin.aws.amazon.com/federation')

    url.args['Action'] = "login"
    url.args['Issuer'] = None
    url.args['Destination'] = "https://console.aws.amazon.com/"
    url.args['SigninToken'] = get_signin_token(session)

    return url.url


def get_signin_token(session):
    credentials = session.get_credentials()

    url = "https://signin.aws.amazon.com/federation"
    response = requests.get(url,
        params={
            "Action": "getSigninToken",
            "Session": json.dumps({
                "sessionId": credentials.access_key,
                "sessionKey": credentials.secret_key,
                "sessionToken": credentials.token,
            })
        },
        timeout=(3.1, 5)
    )
    return json.loads(response.text)["SigninToken"]


class Federation:
    def __init__(self, session):
        self.session = session


    def signing(self, boto_session):
        r = self.session._get(get_signin_url(boto_session))
        if r.status_code != 200:
            raise Exception("failed session signin")

        self.session.authenticated = True
        return True
