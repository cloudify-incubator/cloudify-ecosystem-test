import os
import re
import pathlib
from setuptools import setup, find_packages


def get_version():
    current_dir = pathlib.Path(__file__).parent.resolve()
    with open(os.path.join(current_dir,
                           'ecosystem_tests/__version__.py'),
              'r') as outfile:
        var = outfile.read()
        return re.search(r'\d+.\d+.\d+', var).group()


setup(
    name='cloudify-ecosystem-test',
    version=get_version(),
    license='LICENSE',
    packages=find_packages(),
    description='Stuff that Ecosystem Tests Use',
    entry_points={
        "console_scripts": [
            "ecosystem-test = ecosystem_tests.ecosystem_tests_cli.main:_ecosystem_test",
            "ecosystem-tests = ecosystem_tests.ecosystem_tests_cli.main:_ecosystem_test"
        ]
    },
    install_requires=[
        'cloudify-common>=5.1.0',
        'urllib3>=1.25.4',
        'deepdiff==5.7.0',
        'pytest',
        'wagon>=0.10.0',
        'progressbar',
        'click>8,<9',
        'testtools',
        'nose>=1.3',
        'PyGithub',
        'gitpython',
        'requests',
        'pyyaml',
        'boto3',
        'tqdm'
    ]
)
