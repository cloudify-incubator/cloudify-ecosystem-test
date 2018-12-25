
from setuptools import setup

setup(
    name='cloudify-ecosystem-test',
    version='2.1.2',
    license='LICENSE',
    packages=[
        'ecosystem_tests',
    ],
    description='Stuff that Ecosystem Tests Use',
    install_requires=[
        'testtools',
        'cloudify-common'
    ]
)
