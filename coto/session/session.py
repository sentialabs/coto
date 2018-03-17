import requests
import json
from urllib.parse import unquote
from colors import color
from coto.session.signin import Federation, Root
from coto.clients import Billing, Iam


def dr(r):
    for i in r.history + [r]:
        if i.status_code < 400:
            fg = 'green'
        else:
            fg = 'red'

        print()

        print(color(
            str(i.status_code) + " " + i.request.url,
            fg=fg,
            style='underline'
        ))

        for k, v in i.request.headers.items():
            if k == 'Cookie':
                print(
                    color(k+':', fg='blue')
                )
                for c in v.split(";"):
                    c = c.strip()
                    (n, c) = c.split('=', maxsplit=1)
                    print(
                        color('    ' + n + ': ', fg='blue')
                        + unquote(c)
                    )
            else:
                print(
                    color(k+':', fg='blue'),
                    v
                )

        for k, v in i.headers.items():
            print(
                color(k+':', fg='yellow'),
                v
            )


class Session:
    """
    The Session class represents a session with the AWS Management Console.

    Use the `client` method to obtain a client for one of the supported
    services.
    """

    def __init__(self, **kwargs):
        """
        Args:
            You can pass arguments for the signin method here.

            debug: bool, enable debugging
        """
        self.debug = kwargs.get('debug', False)
        self.root = False
        self.session = requests.Session()
        self.authenticated = False

        self.timeout = (3.1, 10)
        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'

        if len(kwargs) > 0:
            self.signin(**kwargs)


    def signin(self, **kwargs):
        """
        Signin to the AWS Management Console.

        There are various ways to sign in:

          * Using a boto.Session object, pass the `boto_session` argument.
          * Using the Account Root User, pass the `email`, `password`, and
            optionally `mfa_secret` arguments.

        Args:

            boto_session: A boto.Session object, the credentials of this session
                are retrieved and used to signin to the console
            email: Email address to
        """
        if 'boto_session' in kwargs:
            boto_session = kwargs.get('boto_session')
            return Federation(self).signing(boto_session)

        elif 'email' in kwargs and 'password' in kwargs:
            email = kwargs.get('email')
            password = kwargs.get('password')
            mfa_secret = kwargs.get('mfa_secret')
            return Root(self).signin(email, password, mfa_secret)


    # http requests
    def _set_defaults(self, kwargs):
        if not 'timeout' in kwargs:
            kwargs['timeout'] = self.timeout

        if not 'headers' in kwargs:
            kwargs['headers'] = {}

        kwargs['headers']['Accept'] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
        kwargs['headers']['User-Agent'] = self.user_agent


    def _get(self, url, **kwargs):
        self._set_defaults(kwargs)
        r = self.session.get(url, **kwargs)
        if self.debug:
            dr(r)
        return r


    def _post(self, url, **kwargs):
        self._set_defaults(kwargs)
        r = self.session.post(url, **kwargs)
        if self.debug:
            dr(r)
        return r


    def _put(self, url, **kwargs):
        self._set_defaults(kwargs)
        r = self.session.put(url, **kwargs)
        if self.debug:
            dr(r)
        return r


    def _delete(self, url, **kwargs):
        self._set_defaults(kwargs)
        r = self.session.delete(url, **kwargs)
        if self.debug:
            dr(r)
        return r


    # mimic boto3 :)
    def client(self, service):
        """
        Create a client for a service.

        Supported services:

          * `billing`
          * `iam`

        Args:
            service: name of the service, eg., `billing`

        Returns:
            object: service client
        """
        if not self.authenticated:
            raise Exception('please signin before calling client')

        if service == 'billing':
            return Billing(self)
        elif service == 'iam':
            return Iam(self)
        else:
            raise Exception("service {0} unsupported".format(service))
