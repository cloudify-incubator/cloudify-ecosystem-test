import click
from ...ecosystem_tests_cli import ecosystem_tests

@ecosystem_tests.command(name='local-blueprint-test', short_help='Test blueprint locally.')
#TODO: Add options
def local_blueprint_test():
    pass



click.command()