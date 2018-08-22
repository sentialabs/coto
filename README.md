# coto: An AWS Management Console Client

[![Documentation Status](https://readthedocs.org/projects/coto/badge/?version=latest)](http://coto.readthedocs.io/en/latest/?badge=latest)
[![Version](http://img.shields.io/pypi/v/coto.svg?style=flat)](https://pypi.python.org/pypi/coto/)

Almost any AWS service can be fully controlled using the AWS API, for this we strongly recommend the use of [boto3](http://boto3.readthedocs.io/). The problem is, that there exist some administrative tasks for which there is no public API, and there exist some [AWS tasks that still require the AWS Account Root User](https://docs.aws.amazon.com/general/latest/gr/aws_tasks-that-require-root.html).

For example when creating a new account in an AWS Organization, there are some things that you are unable to do using the documented APIs, such as:

  * set tax registration information (no documented API)
  * set additional contacts (no documented API)
  * reset AWS Account Root User password (no documented API)
  * setup MFA for the AWS Account Root User (requires root user)

> **Note:**
>
> This project provides a client for the undocumented APIs that are used by the AWS Management Console. **These APIs will be changing without any upfront warning!** As a result of this, coto can break at any moment.


## Examples


### Login using a boto session.

```python
import boto3
import coto

session = coto.Session(
    boto3_session=boto3.Session()
)
```


### Login using root user password.

```python
import coto

session = coto.Session(
    email='email@example.com',
    password='s3cur3 p4ssw0rd!'
)
```


### Login using root user password with virtual MFA.

```python
import coto

session = coto.Session(
    email='email@example.com',
    password='s3cur3 p4ssw0rd!',
    mfa_secret='MFAxSECRETxSEEDxXXXXXXXXXXXXXXXXXX'
)
```


### Get account information

```python
iam = session.client('iam')
iam.get_account_info()
```


### Set tax registration

```python
billing = session.client('billing')
billing.set_tax_registration(
    TaxRegistration={
        'address': {
            'addressLine1': 'Adresweg 1',
            'addressLine2': None,
            'city': 'Delft',
            'countryCode': 'NL',
            'postalCode': '2600 AA',
            'state': 'Zuid-Holland',
        },
        'authority': {'country': 'NL', 'state': None},
        'legalName': 'Besloten Venootschap B.V.',
        'localTaxRegistration': False,
        'registrationId': 'NL000000000B01',
    }
)
```

## Development

```
pipenv install -d
pipenv run nosetests tests
cd docs
pipenv run make html
```
