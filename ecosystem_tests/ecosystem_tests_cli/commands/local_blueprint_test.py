import click
from ...ecosystem_tests_cli import ecosystem_tests

@ecosystem_tests.command(name='local-blueprint-test', short_help='Test blueprint locally.')
@ecosystem_tests.options.blueprint_path
@ecosystem_tests.options.test_id
@ecosystem_tests.options.inputs
@ecosystem_tests.options.timeout
@ecosystem_tests.options.license
@ecosystem_tests.options.secret
@ecosystem_tests.options.file_secret
@ecosystem_tests.options.encoded_secrets
def local_blueprint_test(blueprint_path,
                         test_id,
                         inputs,
                         timeout,
                         license,
                         secret,
                         file_secret,
                         encoded_secret):
    pass



click.command()