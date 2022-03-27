from setuptools import setup, find_packages

setup(
    name='cloudify-ecosystem-test',
    version='2.6.20',
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
        'testtools',
        'cloudify-common>=5.1.0',
        'PyGithub',
        'wagon>=0.10.0',
        'boto3',
        'urllib3>=1.25.4',
        'progressbar',
        'pyyaml',
        'requests',
        'click>7,<8',
        'nose>=1.3',
        'pytest==4.6.11'
    ]
)
