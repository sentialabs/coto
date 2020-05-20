import requests
import json
from urllib.parse import unquote
from colors import color
from .. import clients


def dr(r):
    for i in r.history + [r]:
        if i.status_code < 400:
            fg = 'green'
        else:
            fg = 'red'

        print(
            color(
                str(i.status_code) + \
                    " " + i.request.method + \
                    " " + i.request.url,
                fg=fg,
                style='underline'))

        for k, v in i.request.headers.items():
            if k == 'Cookie':
                print(color(k + ':', fg='blue'))
                for c in v.split(";"):
                    c = c.strip()
                    (n, c) = c.split('=', maxsplit=1)
                    print(color('    ' + n + ': ', fg='blue') + unquote(c))
            else:
                print(color(k + ':', fg='blue'), v)

        for k, v in i.headers.items():
            print(color(k + ':', fg='yellow'), v)

        if i.request.body and len(i.request.body) > 0:
            print(color('Body:', fg='blue'))
            print(i.request.body)
            print(color('EOF', fg='blue'))


class Session:
    """
    The Session class represents a session with the AWS Management Console.

    Use the `client` method to obtain a client for one of the supported
    services.
    """

    def __init__(
        self, debug=False, verify=True,
        metadata1_generator=None,
        captcha_solver=None, **kwargs
    ):
        """
        Args:
            debug (bool): Enable debug messages.
            verify (str | bool): Requests SSL certificate checking. Path to
                CA certificates file. ``False`` to ignore certificate errors.
                ``True`` to use defaults (default).
            captcha_solver (coto.captcha.Solver): Class implementing a way to solve captchas (e.g., send them to Slack for you to solve).
            metadata1_generator (coto.metadata1.Generator): Class implementing a way to generate metadata1.
            **kwargs: You can pass arguments for the signin method here.
        """
        self.debug = debug
        self._metadata1_generator = metadata1_generator
        self._captcha_solver = captcha_solver
        self.root = False
        self.coupled = None
        self.session = requests.Session()
        self.session.verify = verify
        self.authenticated = False
        self._clients = {}

        self.timeout = (3.1, 10)
        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'

        if len(kwargs) > 0:
            self.signin(**kwargs)

    def signin(self, **kwargs):
        """
        Signin to the AWS Management Console.

        There are various ways to sign in:
            * Using a boto3.Session object, pass the ``boto3_session`` argument.
            * Using the Account Root User, pass the ``email``, ``password``, and
              optionally ``mfa_secret`` arguments.

        Args:
            boto3_session (boto3.session.Session): The credentials of this
                session are retrieved and used to signin to the console.
            email (str): AWS account root user email to use for login.
            password (str): AWS account root user password to use for login.
            mfa_secret (str): AWS account root user mfa secret to use for login.
                The Base32 seed defined as specified in RFC3548.
                The Base32StringSeed is Base64-encoded.
        """
        if 'boto3_session' in kwargs:
            boto3_session = kwargs.get('boto3_session')
            return self.client('federation').signin(boto3_session)

        elif 'email' in kwargs and 'password' in kwargs:
            args = {}
            for key in ['email', 'password', 'mfa_secret']:
                if key in kwargs:
                    args[key] = kwargs.get(key)
            return self.client('signin').signin(**args)

    # http requests
    def _set_defaults(self, kwargs):
        if not 'timeout' in kwargs:
            kwargs['timeout'] = self.timeout

        if not 'headers' in kwargs:
            kwargs['headers'] = {}

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

    def client(self, service):
        """
        Create a client for a service.

        Supported services:
          * ``account``
          * ``billing``
          * ``federation``
          * ``iam``
          * ``mfa``
          * ``resetpassword``
          * ``signin``
          * ``signin_amazon``
          * ``signin_aws``

        Args:
            service: name of the service, eg., `billing`

        Returns:
            object: service client
        """
        service = service.lower()

        if service not in self._clients:
            if not hasattr(clients, service):
                raise Exception("service {0} unsupported".format(service))

            klass = getattr(clients, service).Client

            if klass.REQUIRES_AUTHENTICATION and not self.authenticated:
                raise Exception(
                    "signin before creating {0} service client".format(
                        service))

            self._clients[service] = klass(self)

        return self._clients[service]
