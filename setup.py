
from setuptools import setup

setup(
    name='cloudify-ecosystem-test',
    version='2.2.95',
    license='LICENSE',
    packages=[
        'ecosystem_tests',
        'ecosystem_cicd_tools',
    ],
    description='Stuff that Ecosystem Tests Use',
    install_requires=[
        'testtools',
        'cloudify-common',
        'PyGithub',
        'wagon>=0.10.0',
        'boto3',
        'progressbar',
        'pyyaml'
    ]
)
