import io
import os
from setuptools import setup, find_packages


NAME = 'aa'
DESCRIPTION = 'Data analysis code for survey answer agreement (aa)'
URL = 'https://github.com/jkpr/AnswerAgreement/'
EMAIL = 'jpringle@jhu.edu'
AUTHOR = 'James K. Pringle'
REQUIRES_PYTHON = '>=3.6.0'
VERSION = None


# What packages are required for this module to be executed?
REQUIRED = [
    'xlrd',
    'pandas'
]


# ---------------------------------------------------------------------------- #
here = os.path.abspath(os.path.dirname(__file__))


# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in the MANIFEST.in file!
with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()


# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    with open(os.path.join(here, NAME, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION


# ----- Where the magic happens: --------------------------------------------- #
setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=('test',)),
    install_requires=REQUIRED,
    include_package_data=True,
    license='MIT',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
