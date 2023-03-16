from setuptools import setup, find_packages

setup(
    name='cloudify-ecosystem-test',
    version='2.8.27',
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
        'pytest==4.6.11',
        'wagon>=0.10.0',
        'progressbar',
        'click>8,<9',
        'testtools',
        'nose>=1.3',
        'PyGithub',
        'requests',
        'pyyaml',
        'boto3',
    ]
)
