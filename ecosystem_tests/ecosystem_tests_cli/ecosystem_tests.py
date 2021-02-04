import os
import click
import base64

from .inputs import inputs_to_dict
from ..ecosystem_tests_cli import helptexts
from .exceptions import EcosystemTestCliException
from .constants import (TIMEOUT,
                        DEFAULT_LICENSE_PATH,
                        DEFAULT_BLUEPRINT_PATH,
                        MANAGER_CONTAINER_NAME)

CLICK_CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'])


def init():
    pass


def group(name):
    return click.group(name=name, context_settings=CLICK_CONTEXT_SETTINGS)


def command(*args, **kwargs):
    return click.command(*args, **kwargs)


def inputs_callback(ctx, param, value):
    """Allow to pass any inputs we provide to a command as
    processed inputs instead of having to call `inputs_to_dict`
    inside the command.
    `@ecoststem_tests.options.inputs` already calls this callback so that
    every time you use the option it returns the inputs as a
    dictionary.
    """
    if not value or ctx.resilient_parsing:
        return {}
    return inputs_to_dict(value)


def license_callback(ctx, param, value):
    """
    Prepare Licence as base64 encoded string for dorkl.
    :param value: Base64 encoded license or path to licence.
    """
    if os.path.isfile(value):
        with open(value, 'r') as licence_file:
            content = licence_file.read()
        return base64.b64encode(content.encode('utf-8')).decode('ascii')
    elif value == DEFAULT_LICENSE_PATH:
        raise EcosystemTestCliException(
            'Liscence not found in default location: {path}'.format(
                path=DEFAULT_LICENSE_PATH))
    return value


def secrets_callback(ctx, param, value):
    """Prepare secrets as base64 encoded string for dorkl"""
    # TODO: Handle not base64 secrets
    if not value or ctx.resilient_parsing:
        return {}
    return value


def file_secrets_callback(ctx, param, value):
    """Prepare secrets from file as base64 encoded string for dorkl"""
    if not value or ctx.resilient_parsing:
        return {}
    return value


def encoded_secrets_callback(ctx, param, value):
    """Prepare encoded secrets from file as base64 encoded string for dorkl"""
    if not value or ctx.resilient_parsing:
        return {}
    return value


class Options(object):
    def __init__(self):
        """The options api is nicer when you use each option by calling
        `@ecosystem_tests.options.some_option` instead of
        `@ecosystem_tests.some_option`.
        Note that some options are attributes and some are static methods.
        The reason for that is that we want to be explicit regarding how
        a developer sees an option. It it can receive arguments, it's a
        method - if not, it's an attribute.
        """
        # TODO: Maybe not multiple because of test id? or ignore the test id
        #  from user in case of some blueprints??
        self.blueprint_path = click.option('-p',
                                           '--blueprint-path',
                                           default=[DEFAULT_BLUEPRINT_PATH],
                                           type=click.Path(exists=True),
                                           multiple=True,
                                           show_default=DEFAULT_BLUEPRINT_PATH)

        # TODO:handle inputs!
        self.inputs = click.option(
            '-i',
            '--inputs',
            multiple=True,
            callback=inputs_callback,
            type=click.STRING,
            help=helptexts.INPUTS)

        self.timeout = click.option('-t',
                                    '--timeout',
                                    type=int,
                                    default=TIMEOUT,
                                    help=helptexts.TEST_TIMEOUT,
                                    show_default=TIMEOUT)
        self.test_id = click.option('--test-id',
                                    type=click.STRING,
                                    help=helptexts.TEST_ID)
        self.nested_test = click.option('--nested-test',
                                        type=click.STRING,
                                        help=helptexts.NESTED_TEST)

        # TODO: consider add this option as a command.
        self.validate_only = click.option('--validate-only',
                                          type=click.BOOL,
                                          default=False,
                                          help=helptexts.VALIDATE_ONLY)

        self.license = click.option('-l', '--license',
                                    type=click.STRING,
                                    help=helptexts.LICENSE,
                                    callback=license_callback,
                                    default=DEFAULT_LICENSE_PATH,
                                    show_default=DEFAULT_LICENSE_PATH)

        self.secret = click.option('-s', '--secret',
                                   multiple=True,
                                   type=click.STRING,
                                   help=helptexts.SECRETS,
                                   callback=secrets_callback)

        self.file_secret = click.option('-fs', '--file-secret',
                                        type=click.STRING,
                                        multiple=True,
                                        help=helptexts.FILE_SECRETS,
                                        callback=file_secrets_callback)

        # TODO: Add note that we Assume all secrets that encoded are from
        #  file(even if they are not), need to test that .
        self.encoded_secrets = click.option('-es', '--encoded-secret',
                                            multiple=True,
                                            type=click.STRING,
                                            help=helptexts.ENCODED_SECRETS,
                                            # callback=encoded_secrets_callback,
                                            )

        self.container_name = click.option('-c',
                                           '--container-name',
                                           type=click.STRING,
                                           default=MANAGER_CONTAINER_NAME,
                                           help=helptexts.CONTAINER_NAME)


options = Options()
