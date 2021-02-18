from bs4 import BeautifulSoup
from pyotp import TOTP
from datetime import datetime, timedelta
import json
from . import BaseClient


class Client(BaseClient):
    """
    A low-level client representing IAM:

    .. code-block:: python

        import coto

        session = coto.Session()
        client = session.client('iam')

    These are the available methods:

    * General:
        * :py:meth:`get_account_info`

    * Access Keys:
        * :py:meth:`list_root_access_keys`
        * :py:meth:`create_root_access_key`
        * :py:meth:`update_root_access_key`
        * :py:meth:`delete_root_access_key`

    * MFA Devices:
        * :py:meth:`list_root_mfa_devices`
        * :py:meth:`create_virtual_mfa_device`
        * :py:meth:`enable_root_mfa_device`
        * :py:meth:`deactivate_root_mfa_device`
        * :py:meth:`delete_virtual_mfa_device`
    """

    def __init__(self, session):
        super().__init__(session)
        self.__xsrf_token = None

    def _url(self, api):
        return "https://console.aws.amazon.com/iam/{0}".format(api)

    def _xsrf_token(self):
        if self.__xsrf_token is None:
            self._get_xsrf_token()

        return self.__xsrf_token

    def _get_xsrf_token(self):
        r = self.session()._get(
            'https://console.aws.amazon.com/iam/home?&state=hashArgs%23')

        if r.status_code != 200:
            raise Exception("failed get token")

        r = self.session()._get('https://console.aws.amazon.com/iam/home?')

        if r.status_code != 200:
            raise Exception("failed get token")

        soup = BeautifulSoup(r.text, 'html.parser')
        for m in soup.find_all('meta'):
            if 'id' in m.attrs and m['id'] == "xsrf-token":
                self.__xsrf_token = m['data-token']
                return

        raise Exception('unable to obtain IAM xsrf_token')

    def _get(self, api):
        r = self.session()._get(
            self._url(api), headers={'X-CSRF-Token': self._xsrf_token()})

        if 'X-CSRF-Token' in r.headers:
            self.__xsrf_token = r.headers['X-CSRF-Token']

        if r.status_code != 200:
            print(r.text)
            raise Exception("failed get {0}".format(api))

        return json.loads(r.text)

    def _post(self, api, data=None):
        r = self.session()._post(
            self._url(api),
            headers={
                'X-CSRF-Token': self._xsrf_token(),
                'Content-Type': 'application/json',
            },
            data=json.dumps(data) if data is not None else None,
        )

        if 'X-CSRF-Token' in r.headers:
            self.__xsrf_token = r.headers['X-CSRF-Token']

        if r.status_code != 200:
            print(r.text)
            raise Exception("failed post {0}".format(api))

        return json.loads(r.text)

    def _http(self, method, api, data=None):
        r = self.session()._post(
            self._url(api),
            headers={
                'X-CSRF-Token': self._xsrf_token(),
                'x-http-method-override': method.upper(),
            },
            data=json.dumps(data) if data is not None else None,
        )

        if 'X-CSRF-Token' in r.headers:
            self.__xsrf_token = r.headers['X-CSRF-Token']

        if r.status_code != 200:
            print(r.text)
            raise Exception("failed delete {0}".format(api))

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
        return self._get('service/account')

    def list_root_mfa_devices(self):
        """
        Lists enabled root MFA devices.

        Request Syntax:
            .. code-block:: python

                response = client.list_root_mfa_devices()

        Returns:
            dict: Response Syntax

            .. code-block:: python

                {
                    'serialNumber': [
                        str,
                    ],
                    'nextItem': str,
                    'truncated': bool
                }
        """
        r = self._get('api/mfa')
        return r

    def create_virtual_mfa_device(
            self, VirtualMFADeviceName='root-account-mfa-device', Path='/'):
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
        r = self._post('api/mfa/createVirtualMfa', {
            'path': Path,
            'virtualMFADeviceName': VirtualMFADeviceName
        })
        return r

    def enable_root_mfa_device(self,
                               SerialNumber,
                               Base32StringSeed=None,
                               AuthenticationCode1=None,
                               AuthenticationCode2=None):
        """
        Enables the specified MFA device and associates it with the account root
        user. When enabled, the MFA device is required for every subsequent
        login by the account root user.

        Specify either the ``Base32StringSeed``, or both ``AuthenticationCode1``
        and ``AuthenticationCode2``.

        Request Syntax:
            .. code-block:: python

                response = client.enable_root_mfa_device(
                    SerialNumber=str,
                    Base32StringSeed=str,
                )

            or

            .. code-block:: python

                response = client.enable_root_mfa_device(
                    SerialNumber=str,
                    AuthenticationCode1=str,
                    AuthenticationCode2=str,
                )

        Args:
            SerialNumber (str): The serial number that uniquely identifies the
                MFA device. For virtual MFA devices, the serial number is the
                device ARN.
            Base32StringSeed (str): The Base32 seed defined as specified in
                RFC3548. The Base32StringSeed is Base64-encoded. If set, the
                the current values for the ``AuthenticationCode1`` and
                ``AuthenticationCode2`` arguments will be calculated.
            AuthenticationCode1 (str): An authentication code emitted by the
                device. The format for this parameter is a string of 6 digits.
                If ``Base32StringSeed`` is set, it wil override this argument.
            AuthenticationCode2 (str): An authentication code emitted by the
                device. The format for this parameter is a string of 6 digits.
                If ``Base32StringSeed`` is set, it wil override this argument.

        """
        if Base32StringSeed:
            current = datetime.now()
            previous = current - timedelta(seconds=30)
            totp = TOTP(Base32StringSeed)
            AuthenticationCode1 = totp.at(previous)
            AuthenticationCode2 = totp.at(current)

        r = self._post(
            'api/mfa/enableMfaDevice', {
                'userName': '',
                'serialNumber': SerialNumber,
                'authenticationCode1': AuthenticationCode1, 
                'authenticationCode2': AuthenticationCode2
            })
        return r

    def deactivate_root_mfa_device(self, SerialNumber):
        """
        Deactivates the specified MFA device and removes it from association
        with the account root user.

        Request Syntax:
            .. code-block:: python

                response = client.deactivate_root_mfa_device(
                    SerialNumber=str
                )

        Args:
            SerialNumber (str): The serial number that uniquely identifies the
                MFA device. For virtual MFA devices, the serial number is the
                device ARN.
        """
        r = self._post('api/mfa/deactivateMfaDevice', {'serialNumber': SerialNumber, 'userName': ''})
        return r

    def list_root_access_keys(self, Deleted=False):
        """
        List the access key pairs associated with the account root user.

        Request Syntax:
            .. code-block:: python

                response = client.list_root_access_keys(
                    Deleted=bool,
                )

        Args:
            Deleted (bool): List the deleted access key pairs
        Returns:
            dict: Response Syntax

            .. code-block:: python

                [
                    {
                        'createDate': int,
                        'deleteDate': int,
                        'id': int,
                        'lastUsedDetails': {
                            'lastDateUsed': int,
                            'region': str,
                            'serviceName': str,
                        },
                        'status': 'Active' | 'Inactive' | 'Deleted',
                    },
                ]
        """
        if Deleted:
            r = self._get('service/root/keys/?deleted=1')
        else:
            r = self._get('service/root/keys')
        return r

    def create_root_access_key(self):
        """
        Creates a new AWS secret access key and corresponding AWS access key ID
        for the account root user. The default status for new keys is Active.

        Request Syntax:
            .. code-block:: python

                response = client.create_root_access_key()

        Returns:
            dict: Response Syntax

            .. code-block:: python

                {
                    "id": str,
                    "status": "Active",
                    "secret": str,
                    "createDate": int,
                    "deleteDate": int
                }
        """
        r = self._post('service/root/keys')
        return r

    def update_root_access_key(self, AccessKeyId, Status='Inactive'):
        """
        Changes the status of the specified access key from Active to Inactive,
        or vice versa. This action can be used to disable a account root user's
        key as part of a key rotation work flow.

        Request Syntax:
            .. code-block:: python

                response = client.activate_root_access_key(
                    AccessKeyId=str,
                    Status='Active' | 'Inactive',
                )

        Args:
            AccessKeyId (str): The access key ID for the access key ID and
                secret access key you want to activate.
            Status (str): The status you want to assign to the secret access
                key. Active means the key can be used for API calls to AWS,
                while Inactive means the key cannot be used.

        Returns:
            bool: success
        """
        if Status.lower() == 'active':
            r = self._http('service/activate', "root/keys/{0}".format(AccessKeyId))
        else:
            r = self._http('service/deactivate', "root/keys/{0}".format(AccessKeyId))
        return r['success']

    def delete_root_access_key(self, AccessKeyId):
        """
        Deletes the access key pair associated with the account root user.

        Request Syntax:
            .. code-block:: python

                response = client.delete_root_access_key(
                    AccessKeyId=str,
                )

        Args:
            AccessKeyId (str): The access key ID for the access key ID and
                secret access key you want to delete.

        Returns:
            bool: success
        """
        r = self._http('delete', "service/root/keys/{0}".format(AccessKeyId))
        return r['success']
