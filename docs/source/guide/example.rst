#######
Example
#######

Login as Root
-------------

The iTermSolver will show captchas in iTerm and prompt the user to enter
the guess.

Please find a sample value for metadata1 by inspecting your requests
when you manually interact with the Amazon login. Use that value instead
of "XXXXXXXXX" when constructing the StaticGenerator.

.. code-block:: python

    import coto
    from coto.captcha.iterm_solver import iTermSolver
    from coto.metadata1.static_generator import StaticGenerator

    captcha_solver = iTermSolver()
    metadata1_generator = StaticGenerator("XXXXXXXXX")

    session = coto.Session(
        email="email@example.com",
        password="s3cr3t_p4ssw0rd!",
        mfa_secret="xSECRETxMFAxSEEDxASDFASASAASDFASFDASDF",
        metadata1_generator=metadata1_generator,
        captcha_solver=captcha_solver,
    )


Federated Login
---------------

When using Federated login, AWS will not require metadata1 or captchas
to be solved.

.. code-block:: python

    import boto3
    import coto

    session = coto.Session(
        boto3_session=boto3.Session()
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
    iam.enable_root_mfa_device(
        SerialNumber=virtual_mfa['serialNumber'],
        Base32StringSeed=virtual_mfa['base32StringSeed']
    )
