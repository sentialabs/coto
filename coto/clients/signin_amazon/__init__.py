from bs4 import BeautifulSoup
from pyotp import TOTP
from urllib import parse
import json
from .. import BaseClient
import time
from furl import furl


# import os
# import webbrowser

# def view_html(html):
#     path = os.path.abspath('temp.html')
#     url = 'file://' + path
#     with open(path, 'w') as f:
#         f.write(html)
#     webbrowser.open(url)

def ap_url(email, path='signin'):
    url = furl(f"https://www.amazon.com/ap/{path}")

    url.args["openid.assoc_handle"] = "aws"
    url.args["openid.return_to"] = "https://signin.aws.amazon.com/oauth?coupled_root=true&response_type=code&redirect_uri=https%3A%2F%2Fconsole.aws.amazon.com%2Fconsole%2Fhome%3Fstate%3DhashArgs%2523%26isauthcode%3Dtrue&client_id=arn%3Aaws%3Aiam%3A%3A015428540659%3Auser%2Fhomepage"
    url.args["openid.mode"] = "checkid_setup"
    url.args["openid.ns"] = "http://specs.openid.net/auth/2.0"
    url.args["openid.identity"] = "http://specs.openid.net/auth/2.0/identifier_select"
    url.args["openid.claimed_id"] = "http://specs.openid.net/auth/2.0/identifier_select"
    url.args["action"] = ""
    url.args["disableCorpSignUp"] = ""
    url.args["clientContext"] = ""
    url.args["marketPlaceId"] = ""
    url.args["poolName"] = ""
    url.args["authCookies"] = ""
    url.args["pageId"] = "aws.login"
    url.args["siteState"] = "registered,EN_US"
    url.args["accountStatusPolicy"] = "P1"
    url.args["sso"] = ""
    url.args["openid.pape.preferred_auth_policies"] = "MultifactorPhysical"
    url.args["openid.pape.max_auth_age"] = "120"
    url.args["openid.ns.pape"] = "http://specs.openid.net/extensions/pape/1.0"
    url.args["server"] = "/ap/signin?ie=UTF8"
    url.args["accountPoolAlias"] = ""
    url.args["forceMobileApp"] = "1"
    url.args["language"] = "EN_US"
    url.args["forceMobileLayout"] = "0"
    url.args["awsEmail"] = email

    return url.url


class Client(BaseClient):
    REQUIRES_AUTHENTICATION = False
    _REDIRECT_URL = "https://console.aws.amazon.com/console/home?state=hashArgs%23&isauthcode=true"

    def __init__(self, session):
        super().__init__(session)

    def find_and_submit_form(self, soup, email, password, mfa_secret=None):
        error = soup.find(id="message_error")
        if error:
            message = error.get_text()
            # Enter the characters as they are given in the challenge.
            raise Exception(message)

        form = soup.find(id="ap_signin_form")

        if not form:
            mfa_form = soup.find(id="auth-mfa-form")
            if mfa_form:
                raise Exception("accounts with Amazon MFA not supported")

        data = {'metadata1': self.session()._metadata1_generator.generate()}

        for field in form.find_all('input'):
            name = field.get('name')
            if not name:
                continue
            value = field.get('value')
            data[name] = value
                
        if "guess" in data:
            if not self.session()._captcha_solver:
                raise Exception("captcha solver required")

            captcha = soup.find(id="ap_captcha_img")
            img = captcha.find("img")
            src = img.get("src")
            guess_uuid = self.session()._captcha_solver.solve(url=src)

            while True:
                guess = self.session()._captcha_solver.result(guess_uuid)

                if guess is None:
                    time.sleep(5)
                else:
                    data["guess"] = guess
                    break

        if "tokenCode" in data and mfa_secret:
            data['tokenCode'] = TOTP(mfa_secret).now()

        overrides = {
            "password": password,
            "email": email,
        }

        for k, v in data.items():
            if v is None:
                _v = overrides.get(k)
                if _v:
                    data[k] = _v

        return self.session()._post(
            form.get("action"),
            data=data
        )

    def signin(self, email, password, mfa_secret=None):
        """
        Signin into the AWS Management Console using account root user.

        Request Syntax:

            .. code-block:: python

                response = client.get_account_type(
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

        # first post password
        response = self.session()._get(ap_url(email))
        soup = BeautifulSoup(response.text, 'html.parser')
        response = self.find_and_submit_form(soup, email, password, mfa_secret)
        # view_html(response.text)

        counter = 0

        while counter < 10 and response.url != "https://console.aws.amazon.com/console/home":
            counter += 1
            soup = BeautifulSoup(response.text, 'html.parser')
            response = self.find_and_submit_form(soup, email, password, mfa_secret)

        if response.url == "https://console.aws.amazon.com/console/home":
            self.session().authenticated = True
            self.session().root = True
            return True
        else:
            return False
