import click
import random
import string
from ..exceptions import EcosystemTestCliException
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
@ecosystem_tests.options.plugin
@ecosystem_tests.options.plugins_bundle
@ecosystem_tests.options.no_bundle
def local_blueprint_test(blueprint_path,
                         test_id,
                         inputs,
                         timeout,
                         license,
                         secret,
                         file_secret,
                         encoded_secret,
                         plugin,
                         bundle_path,
                         no_bundle_upload):

    bp_test_ids = validate_and_generate_test_ids(blueprint_path,test_id)


def validate_and_generate_test_ids(blueprint_path,test_id):
    """
    Validate that if user pass mupltiple bluprints paths so test_id is not provided.
    If the user pass multiple blueprints to test , generate list of test_ids.
    """
    if test_id:
        if len(blueprint_path) > 1:
            raise EcosystemTestCliException(
                'Please not provide test-id with multiple blueprints to test.')
        test_ids=[test_id]

    else:
        # Generate test ids for all blueprints.
        test_ids= [id_generator() for _ in range(len(blueprint_path)) ]
        click.echo("test_ids: {}".format(test_ids))

    return list(zip(blueprint_path, test_ids))


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

