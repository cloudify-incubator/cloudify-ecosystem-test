
from setuptools import setup

setup(
    name='cloudify-ecosystem-test',
    version='2.2.13.1',
    license='LICENSE',
    packages=[
        'ecosystem_tests',
        'ecosystem_cicd_tools',
    ],
    description='Stuff that Ecosystem Tests Use',
    install_requires=[
        'testtools',
        'cloudify-common'
    ]
)
