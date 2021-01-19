
from setuptools import setup

setup(
    name='cloudify-ecosystem-test',
    version='2.2.112',
    license='LICENSE',
    packages=[
        'ecosystem_tests',
        'ecosystem_cicd_tools',
    ],
    description='Stuff that Ecosystem Tests Use',
    install_requires=[
        'testtools',
        'cloudify-common>=5.1.0',
        'PyGithub',
        'wagon>=0.10.0',
        'boto3',
        'urllib3>=1.25.4',
        'progressbar',
        'pyyaml',
        'requests',
    ]
)
