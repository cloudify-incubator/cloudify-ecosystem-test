import click
import random
import string

from ..exceptions import EcosystemTestCliException
from ...ecosystem_tests_cli import ecosystem_tests
from ...dorkl.runners import (blueprint_validate,
                              basic_blueprint_test_dev)


@ecosystem_tests.command(name='local-blueprint-test',
                         short_help='Test blueprint locally.')
@ecosystem_tests.options.blueprint_path
@ecosystem_tests.options.test_id
@ecosystem_tests.options.inputs
@ecosystem_tests.options.timeout
@ecosystem_tests.options.on_failure
@ecosystem_tests.options.uninstall_on_success
@ecosystem_tests.options.on_subsequent_invoke
@ecosystem_tests.options.validate_only
def local_blueprint_test(blueprint_path,
                         test_id,
                         inputs,
                         timeout,
                         on_failure,
                         uninstall_on_success,
                         on_subsequent_invoke,
                         validate_only
                         ):
    on_failure = False if on_failure == 'False' else on_failure
    bp_test_ids = validate_and_generate_test_ids(blueprint_path, test_id)
    for blueprint, test_id in bp_test_ids:
        if validate_only:
            blueprint_validate(blueprint_file_name=blueprint,
                               blueprint_id=test_id)
        else:
            basic_blueprint_test_dev(blueprint_file_name=blueprint,
                                     test_name=test_id,
                                     inputs=inputs,
                                     timeout=timeout,
                                     on_subsequent_invoke=on_subsequent_invoke,
                                     on_failure=on_failure,
                                     uninstall_on_success=uninstall_on_success)


def validate_and_generate_test_ids(blueprint_path, test_id):
    """
    Validate that if user pass mupltiple bluprints paths so test_id is not
    provided.
    If the user pass multiple blueprints to test , generate list of tuples:
    [(bp1,id1),(bp2,id2)].
    """
    if test_id:
        if len(blueprint_path) > 1:
            raise EcosystemTestCliException(
                'Please not provide test-id with multiple blueprints to test.')
        test_ids = [test_id]

    else:
        # Generate test ids for all blueprints.
        test_ids = [id_generator() for _ in range(len(blueprint_path))]

    return list(zip(blueprint_path, test_ids))


def id_generator(size=6, chars=string.ascii_lowercase + string.digits):
    return 'test_' + ''.join(random.choice(chars) for _ in range(size))
