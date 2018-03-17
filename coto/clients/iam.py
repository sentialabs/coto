from bs4 import BeautifulSoup
from pyotp import TOTP
from datetime import datetime, timedelta
import json


class Iam:
    """
    A low-level client representing IAM:

    .. code-block:: python

        import coto

        session = coto.Session()
        client = session.client('iam')

    These are the available methods:

    * :py:meth:`create_virtual_mfa_device`
    * :py:meth:`deactivate_mfa_device`
    * :py:meth:`enable_mfa_device`
    * :py:meth:`get_account_info`
    """

    def __init__(self, console):
        self.console = console
        self.xsrf_token = self._xsrf_token()


    def _url(self, api):
        return "https://console.aws.amazon.com/iam/service/{0}".format(api)


    def _xsrf_token(self):
        r = self.console._get(
            'https://console.aws.amazon.com/iam/home?&state=hashArgs%23'
        )

        if r.status_code != 200:
            raise Exception("failed get token")

        r = self.console._get('https://console.aws.amazon.com/iam/home?')

        if r.status_code != 200:
            raise Exception("failed get token")

        soup = BeautifulSoup(r.text, 'html.parser')
        for m in soup.find_all('meta'):
            if 'id' in m.attrs and m['id'] == "xsrf-token":
                return m['data-token']

        raise Exception('unable to obtain IAM xsrf_token')


    def _get(self, api):
        r = self.console._get(
            self._url(api),
            headers={'X-CSRF-Token': self.xsrf_token})

        if 'X-CSRF-Token' in r.headers:
            self.xsrf_token = r.headers['X-CSRF-Token']

        if r.status_code != 200:
            print(r.text)
            raise Exception("failed get {0}".format(api))

        return json.loads(r.text)


    def _post(self, api, data):
        r = self.console._post(
            self._url(api),
            headers={
                'X-CSRF-Token': self.xsrf_token,
                'Content-Type': 'application/json',
            },
            data=json.dumps(data))

        if 'X-CSRF-Token' in r.headers:
            self.xsrf_token = r.headers['X-CSRF-Token']

        if r.status_code != 200:
            print(r.text)
            raise Exception("failed post {0}".format(api))

        return json.loads(r.text)


    # iam api

    def get_account_info(self):
        """
        Retrieves a summary of account information.

        Request Syntax:
            .. code-block:: python

                response = client.get_account_info()

        Returns:
            dict: Response Syntax

            .. code-block:: python

                {
                    'aliases': [],
                    'checklistSummary': {
                        'checklistItems': [
                            {
                                'complete': bool,
                                'fetchSucceeded': bool,
                                'identifier': str,
                            },
                        ],
                        'error': bool,
                        'errorCount': int,
                        'totalCompletedCount': int,
                        'totalCount': int
                    },
                    'errorMap': {},
                    'errors': [],
                    'invalidPolicyExist': bool,
                    'summaryMap': {
                        'AccessKeysPerUserQuota': int,
                        'AccountAccessKeysPresent': int,
                        'AccountMFAEnabled': int,
                        'AccountSigningCertificatesPresent': int,
                        'AssumeRolePolicySizeQuota': int,
                        'AttachedPoliciesPerGroupQuota': int,
                        'AttachedPoliciesPerRoleQuota': int,
                        'AttachedPoliciesPerUserQuota': int,
                        'GroupPolicySizeQuota': int,
                        'Groups': int,
                        'GroupsPerUserQuota': int,
                        'GroupsQuota': int,
                        'InstanceProfiles': int,
                        'InstanceProfilesQuota': int,
                        'MFADevices': int,
                        'MFADevicesInUse': int,
                        'Policies': int,
                        'PoliciesQuota': int,
                        'PolicySizeQuota': int,
                        'PolicyVersionsInUse': int,
                        'PolicyVersionsInUseQuota': int,
                        'Providers': int,
                        'RolePolicySizeQuota': int,
                        'Roles': int,
                        'RolesQuota': int,
                        'ServerCertificates': int,
                        'ServerCertificatesQuota': int,
                        'SigningCertificatesPerUserQuota': int,
                        'UserPolicySizeQuota': int,
                        'Users': int,
                        'UsersQuota': int,
                        'VersionsPerPolicyQuota': int,
                    }
                }
        """
        return self._get('account')


    def create_virtual_mfa_device(self, VirtualMFADeviceName = 'root-account-mfa-device', Path = '/'):
        """
        Creates a new virtual MFA device for the AWS account. After creating the
        virtual MFA, use :py:meth:`enable_mfa_device` to attach the MFA device to the
        account root user.

        Request Syntax:
            .. code-block:: python

                response = client.create_virtual_mfa_device(
                    VirtualMFADeviceName=str,
                    Path=str
                )

        Args:
            VirtualMFADeviceName (str): The name of the virtual MFA device. Use with path to uniquely identify a virtual MFA device.
                This parameter is optional. If it is not included, it defaults to ``root-account-mfa-device``.
            Path (str): The path for the virtual MFA device. For more information about paths, see IAM Identifiers in the IAM User Guide.
                This parameter is optional. If it is not included, it defaults to a slash (/).

        Returns:
            dict: Response Syntax

            .. code-block:: python

                {
                    "serialNumber": str,
                    "qrCodePNG": str,
                    "base32StringSeed": str
                }

            **serialNumber** (*str*) -- The serial number associated with VirtualMFADevice.

            **qrCodePNG** (*str*) -- A QR code PNG image that encodes
            ``otpauth://totp/$virtualMFADeviceName@$AccountName?secret=$Base32String``
            where ``$virtualMFADeviceName`` is one of the create call arguments,
            ``$AccountName`` is the user name if set (otherwise, the account
            ID), and ``$Base32String`` is the seed in Base32 format. The
            ``$Base32String`` value is Base64-encoded.

            **base32StringSeed** (*str*) -- The Base32 seed defined as specified
            in RFC3548 . The Base32StringSeed is Base64-encoded.
        """
        r = self._post('mfa/createVirtualMfa', {
            'path': Path,
            'deviceName': VirtualMFADeviceName
        })
        return r


    def enable_mfa_device(self, SerialNumber, Base32StringSeed):
        """
        Enables the specified MFA device and associates it with the account root
        user. When enabled, the MFA device is required for every subsequent
        login by the account root user.

        Request Syntax:
            .. code-block:: python

                response = client.enable_mfa_device(
                    SerialNumber='string',
                    Base32StringSeed=string
                )

        Args:
            SerialNumber (str): The serial number that uniquely identifies the
                MFA device. For virtual MFA devices, the serial number is the
                device ARN.
            Base32StringSeed (str): The Base32 seed defined as specified in
                RFC3548. The Base32StringSeed is Base64-encoded.

        Returns:
            dict: Response Syntax

            .. code-block:: python

                {
                    'success': bool
                }
        """
        totp = TOTP(Base32StringSeed)
        r = self._post('root/mfa/associate', {
            'serial': SerialNumber,
            'codes': [
                totp.at(datetime.now() - timedelta(seconds=30)),
                totp.at(datetime.now())
            ]
        })
        return r


    def deactivate_mfa_device(self, SerialNumber):
        """
        Deactivates the specified MFA device and removes it from association
        with the account root user.

        Request Syntax:
            .. code-block:: python

                response = client.deactivate_mfa_device(
                    SerialNumber='string'
                )

        Args:
            SerialNumber (str): The serial number that uniquely identifies the
                MFA device. For virtual MFA devices, the serial number is the
                device ARN.
        """
        r = self._post('root/mfa/disassociate', {
            'serial': SerialNumber
        })
        return r
