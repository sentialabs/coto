import json


class Billing:
    """
    A low-level client representing Biling:

    .. code-block:: python

        import coto

        session = coto.Session()
        client = session.client('billing')

    These are the available methods:

    * :py:meth:`delete_tax_registration`
    * :py:meth:`list_alternate_contacts`
    * :py:meth:`list_tax_registrations`
    * :py:meth:`set_alternate_contacts`
    * :py:meth:`set_tax_registration`
    """

    def __init__(self, session):
        self.session = session
        self.xsrf_token = self._xsrf_token()


    def _xsrf_token(self):
        r = self.session._get(
            'https://console.aws.amazon.com/billing/home?region=eu-central-1&state=hashArgs%23'
        )

        if r.status_code != 200:
            raise Exception("failed get billing xsrf token")

        return r.headers['x-awsbc-xsrf-token']


    def _get(self, api):
        r = self.session._get(
            "https://console.aws.amazon.com/billing/rest/v1.0/{0}?state=hashArgs%23".
            format(api),
            headers={'x-awsbc-xsrf-token': self.xsrf_token})

        if r.status_code != 200:
            raise Exception("failed get {0}".format(api))

        return r


    def _put(self, api, data):
        r = self.session._put(
            "https://console.aws.amazon.com/billing/rest/v1.0/{0}?state=hashArgs%23".
            format(api),
            headers={
                'x-awsbc-xsrf-token': self.xsrf_token,
                'Content-Type': 'application/json',
            },
            data=json.dumps(data))

        if r.status_code != 200:
            raise Exception("failed put {0}".format(api))

        return r


    # billing api

    def list_alternate_contacts(self):
        """
        Lists the alternate contacts set for the account. In order to keep the
        right people in the loop, you can add an alternate contact for Billing,
        Operations, and Security communications.

        Request Syntax:
            .. code-block:: python

                response = client.list_alternate_contacts()

        Returns:
            dict: Response Syntax

            .. code-block:: python

                [
                    {
                        'contactId': int,
                        'contactType': 'billing' | 'operations' | 'security',
                        'email': str,
                        'name': str,
                        'phoneNumber': str,
                        'title': str
                    },
                ]
        """
        r = self._get('additionalcontacts')
        return json.loads(r.text)


    def set_alternate_contacts(self, AlternateContacts):
        """
        Sets the alternate contacts set for the account. In order to keep the
        right people in the loop, you can add an alternate contact for Billing,
        Operations, and Security communications.

        Please note that, the primary account holder will continue to receive
        all email communications.

        Contact Types:
            ``billing``:
                The alternate Billing contact will receive billing-related
                notifications, such as invoice availability notifications.
            ``operations``:
                The alternate Operations contact will receive
                operations-related notifications.
            ``security``:
                The alternate Security contact will receive
                security-related notifications. For additional AWS
                security-related notifications, please access the Security
                Bulletins RSS Feed.

        Request Syntax:
            .. code-block:: python

                response = client.set_alternate_contacts(
                    AlternateContacts = [
                        {
                            'contactType': 'billing',
                            'email': str,
                            'name': str,
                            'phoneNumber': str,
                            'title': str
                        },
                        {
                            'contactType': 'operations',
                            'email': str,
                            'name': str,
                            'phoneNumber': str,
                            'title': str
                        },
                        {
                            'contactType': 'security',
                            'email': str,
                            'name': str,
                            'phoneNumber': str,
                            'title': str
                        },
                    ]
                )
        Args:
            AlternateContacts (list): List of alternate contacts.
        """
        self._put('additionalcontacts', AlternateContacts)


    def list_tax_registrations(self):
        """
        Lists the tax registrations set for the account.
        Set your tax information so that your 1099K or W-88EN is generated
        appropriately. Setting this information up also allows you to sell more
        than 200 transactions or $20,000 in Reserved Instances.

        Status:
            ``Verified``:
                Verified
            ``Pending``:
                Pending
            ``Deleted``:
                Deleted

        Request Syntax:
            .. code-block:: python

                response = client.list_tax_registrations()

        Returns:
            dict: Response Syntax

            .. code-block:: python

                [
                    {
                        'address': {
                            'addressLine1': str,
                            'addressLine2': str,
                            'city': str,
                            'countryCode': str,
                            'postalCode': str,
                            'state': str,
                        },
                        'authority': {
                            'country': str,
                            'state': str
                        },
                        'currentStatus': 'Verified' | 'Pending',
                        'legalName': str,
                        'localTaxRegistration': bool,
                        'registrationId': str
                    },
                ]
        """
        r = self._get('taxexemption/eu/vat/information')
        return json.loads(r.text)['taxRegistrationList']


    def set_tax_registration(self, TaxRegistration):
        """
        Set the tax registrations for the account.
        Set your tax information so that your 1099K or W-88EN is generated
        appropriately. Setting this information up also allows you to sell more
        than 200 transactions or $20,000 in Reserved Instances.

        Request Syntax:
            .. code-block:: python

                response = client.set_tax_registration(
                    TaxRegistration = {
                        'address': {
                            'addressLine1': str,
                            'addressLine2': str,
                            'city': str,
                            'countryCode': str,
                            'postalCode': str,
                            'state': str,
                        },
                        'authority': {
                            'country': str,
                            'state': str
                        },
                        'legalName': str,
                        'localTaxRegistration': bool,
                        'registrationId': str,
                    }
                )

        Args:
            TaxRegistration (dict): Desired tax registration.
        """
        self._put('taxexemption/eu/vat/information', TaxRegistration)


    def delete_tax_registration(self, TaxRegistration):
        """
        Delete the given tax registrations from the account.

        Request Syntax:
            .. code-block:: python

                response = client.delete_tax_registration(
                    TaxRegistration = {
                        'address': {
                            'addressLine1': str,
                            'addressLine2': str,
                            'city': str,
                            'countryCode': str,
                            'postalCode': str,
                            'state': str,
                        },
                        'authority': {
                            'country': str,
                            'state': str
                        },
                        'legalName': str,
                        'localTaxRegistration': bool,
                        'registrationId': str,
                    }
                )

        Args:
            TaxRegistration (dict): Tax registration to delete.
        """
        TaxRegistration['currentStatus'] = 'Deleted'
        return self.set_tax_registration(TaxRegistration)
