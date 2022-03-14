from setuptools import setup, find_packages

with open("README.md") as fp:
    long_description = fp.read()

setup(
    name = "coto",
    url = "https://github.com/sentialabs/coto",
    description = "Undocumented AWS Mananagement Console API Client",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author = "Sentia MPC B.V.",
    author_email = "info@sentia.com",
    license = "Apache",
    version = "0.4.2",
    packages = find_packages(),
    install_requires = [
        'ansicolors==1.1.8',
        'appdirs==1.4.4',
        'beautifulsoup4==4.9.3',
        'botocore==1.23.23',
        'certifi==2020.12.5',
        'chardet==4.0.0',
        'distlib==0.3.1',
        'filelock==3.0.12',
        'furl==2.1.0',
        'idna==2.10',
        'jmespath==0.10.0',
        'orderedmultidict==1.0.1',
        'pyotp==2.5.1',
        'python-dateutil==2.8.1',
        'requests==2.25.1',
        'six==1.15.0',
        'soupsieve==2.1',
        'urllib3==1.26.3',
        'Pillow==8.4.0',
    ],
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: Apache Software License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3 :: Only',
    ],
    keywords="aws boto",
    project_urls={
        'Documentation': 'http://coto.readthedocs.io/',
        'Source': 'https://github.com/sentialabs/coto',
    },
)
