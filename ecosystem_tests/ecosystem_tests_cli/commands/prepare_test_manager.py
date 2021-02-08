import click
from ...ecosystem_tests_cli import ecosystem_tests

@ecosystem_tests.command(name='remote-blueprint-test', short_help='Test blueprint remotely (CircleCI).')
#TODO: Add options
def remote_blueprint_test():
    pass