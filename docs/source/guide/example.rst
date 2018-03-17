#######
Example
#######

Login as Root
-------------

.. code-block:: python

    import coto

    session = coto.Session(
        email = "email@example.com",
        password = "s3cr3t_p4ssw0rd!",
        mfa_secret = "xSECRETxMFAxSEEDxASDFASASAASDFASFDASDF"
    )


Federated Login
---------------

.. code-block:: python

    import boto3
    import coto

    session = coto.Session(
        boto_session = boto3.Session()
    )


List Tax Registrations
----------------------

.. code-block:: python

    billing = session.client("billing")
    billing.list_tax_registrations()


Set Root MFA Device
-------------------

*Requires root login!*

Please don't forget to safely store the value of ``virtual_mfa['base32StringSeed']``, or you will be locked out of your account!
You could consider encrypting it using KMS and storing it in S3 or a DynamoDB table.

.. code-block:: python

    iam = session.client("iam")
    virtual_mfa = iam.create_virtual_mfa_device()
    # store ``virtual_mfa['base32StringSeed']`` somewhere!
    iam.enable_mfa_device(
        SerialNumber = virtual_mfa['serialNumber'],
        Base32StringSeed = virtual_mfa['base32StringSeed']
    )
