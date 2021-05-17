from setuptools import setup, find_packages

setup(
    name = "coto",
    url = "https://github.com/sentialabs/coto",
    description = "Undocumented AWS Mananagement Console API Client",
    long_description_content_type='text/x-rst',
    long_description = """
        Some things do not have a documented API but can be set using the
        AWS Mananagement Console. Using this client we access the undocumented
        REST APIs that power the AWS Management Console.
    """,
    author = "Sentia MPC B.V.",
    author_email = "info@sentia.com",
    license = "Apache",
    version = "0.2.5",
    packages = find_packages(),
    install_requires = [
        'requests',
        'furl',
        'ansicolors',
        'beautifulsoup4',
        'pyotp',
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
