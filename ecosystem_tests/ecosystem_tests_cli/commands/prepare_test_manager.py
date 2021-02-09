
from ..utilities import prepare_test_env
from ...dorkl.runners import prepare_test_dev
from ...ecosystem_tests_cli import ecosystem_tests
from ..secrets import prepare_secrets_dict_for_prepare_test

@ecosystem_tests.command(name='prepare-test-manager',
                         short_help='Prepare test manager(licence, '
                                    'secrets, etc.)')
@ecosystem_tests.options.license
@ecosystem_tests.options.secret
@ecosystem_tests.options.file_secret
@ecosystem_tests.options.encoded_secrets
@ecosystem_tests.options.plugin
@ecosystem_tests.options.plugins_bundle
@ecosystem_tests.options.no_bundle
@ecosystem_tests.options.container_name
def prepare_test_manager(license,
                         secret,
                         file_secret,
                         encoded_secret,
                         plugin,
                         bundle_path,
                         no_bundle_upload,
                         container_name):
    """
    This command responsible for prepare test manager.
    """
    with prepare_test_env(license,
                          secret,
                          file_secret,
                          encoded_secret,
                          container_name):

        secrets_dict = prepare_secrets_dict_for_prepare_test(secret,
                                                             file_secret,
                                                             encoded_secret)
        prepare_test_dev(plugins=plugin,
                         secrets=secrets_dict,
                         execute_bundle_upload= not no_bundle_upload,
                         bundle_path=bundle_path)


