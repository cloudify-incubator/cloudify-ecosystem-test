########
# Copyright (c) 2014-2021 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import click
import base64

from .inputs import inputs_to_dict
from .plugins import create_plugins_list
from ..ecosystem_tests_cli import helptexts
from .exceptions import EcosystemTestCliException
from .utilities import validate_string_is_base64_encoded
from .secrets import (secrets_to_dict,
                      file_secrets_to_dict,
                      encoded_secrets_to_dict)
from .constants import (RERUN,
                        RESUME,
                        UPDATE,
                        CANCEL,
                        TIMEOUT,
                        DONOTHING,
                        ROLLBACK_FULL,
                        UNINSTALL_FORCE,
                        ROLLBACK_PARTIAL,
                        DEFAULT_LICENSE_PATH,
                        DEFAULT_BLUEPRINT_PATH,
                        DEFAULT_CONTAINER_NAME,
                        DEFAULT_UNINSTALL_ON_SUCCESS,
                        DEFAULT_DIRECTORY_PATH,
                        DEFAULT_REPO,
                        DEFAULT_BRANCH)

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
            'License not found in default location: {path}'.format(
                path=DEFAULT_LICENSE_PATH))
    validate_string_is_base64_encoded(value)
    return value


def secrets_callback(ctx, param, value):
    """
    Prepare secrets as base64 encoded string for dorkl
    :return dictonary contains {secret_key:secret_base_64_encoded}
    """
    if not value or ctx.resilient_parsing:
        return {}
    return secrets_to_dict(value)


def file_secrets_callback(ctx, param, value):
    """Prepare secrets from file as base64 encoded string for dorkl
    return dictonary contains {secret_key:file_content_base_64_encoded}
    """
    if not value or ctx.resilient_parsing:
        return {}
    return file_secrets_to_dict(value)


def encoded_secrets_callback(ctx, param, value):
    """Prepare encoded secrets for dorkl
    :return dictonary contains {secret_key:secret_base_64_encoded}
    """
    if not value or ctx.resilient_parsing:
        return {}
    return encoded_secrets_to_dict(value)


def plugins_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return []
    return create_plugins_list(value)


def yum_packages_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return []
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
        self.json_path = click.option('-j',
                                      '--json-path',
                                      default=None,
                                      type=click.Path(),
                                      help=helptexts.JSON_PATH)
        self.plugin_version = click.option('-PV',
                                           '--plugin-version',
                                           type=click.STRING,
                                           help=helptexts.VERSION)
        self.package = click.option('-P',
                                    '--package',
                                    multiple=True,
                                    type=click.STRING,
                                    help=helptexts.PACKAGE)
        self.blueprint_path = click.option('-b',
                                           '--blueprint-path',
                                           default=[DEFAULT_BLUEPRINT_PATH],
                                           type=click.Path(),
                                           multiple=True,
                                           show_default=DEFAULT_BLUEPRINT_PATH,
                                           help=helptexts.BLUEPRINT_PATH)

        self.directory = click.option('-d',
                                      '--directory',
                                      default=os.getcwd(),
                                      type=click.Path(),
                                      show_default=DEFAULT_DIRECTORY_PATH,
                                      help=helptexts.DIRECTORY_PATH)

        self.name = click.option('-n',
                                 '--name',
                                 type=click.STRING,
                                 help=helptexts.PLUNGIN_NAME)

        self.v2_plugin = click.option('-v2',
                                      '--v2-plugin',
                                      type=click.BOOL,
                                      is_flag=True,
                                      help=helptexts.V2_PLUGIN)

        self.repo = click.option('-R',
                                 '--repo',
                                 default=None,
                                 type=click.STRING,
                                 show_default=DEFAULT_REPO,
                                 help=helptexts.REPO)

        self.branch = click.option('-B',
                                   '--branch',
                                   default=None,
                                   type=click.STRING,
                                   show_default=DEFAULT_BRANCH,
                                   help=helptexts.BRANCH)

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
                                        multiple=True,
                                        help=helptexts.NESTED_TEST)

        self.license = click.option('-l',
                                    '--license',
                                    type=click.STRING,
                                    help=helptexts.LICENSE,
                                    callback=license_callback,
                                    default=DEFAULT_LICENSE_PATH,
                                    show_default=DEFAULT_LICENSE_PATH)

        self.secret = click.option('-s',
                                   '--secret',
                                   multiple=True,
                                   type=click.STRING,
                                   help=helptexts.SECRETS,
                                   callback=secrets_callback)

        self.file_secret = click.option('-fs',
                                        '--file-secret',
                                        type=click.STRING,
                                        multiple=True,
                                        help=helptexts.FILE_SECRETS,
                                        callback=file_secrets_callback)

        self.encoded_secrets = click.option('-es',
                                            '--encoded-secret',
                                            multiple=True,
                                            type=click.STRING,
                                            help=helptexts.ENCODED_SECRETS,
                                            callback=encoded_secrets_callback,
                                            )

        self.container_name = click.option('-c',
                                           '--container-name',
                                           type=click.STRING,
                                           default='cfy_manager',
                                           show_default=DEFAULT_CONTAINER_NAME,
                                           help=helptexts.CONTAINER_NAME)

        self.plugin = click.option('-p',
                                   '--plugin',
                                   multiple=True,
                                   nargs=2,
                                   type=click.STRING,
                                   help=helptexts.PLUGINS,
                                   callback=plugins_callback)

        self.plugins_bundle = click.option('--bundle-path',
                                           type=click.Path(exists=True),
                                           default=None,
                                           help=helptexts.BUNDLE)

        self.skip_bundle_upload = click.option('--skip-bundle-upload',
                                               is_flag=True,
                                               default=False,
                                               show_default='False',
                                               help=helptexts.NO_BUNDLE)

        self.on_subsequent_invoke = click.option(
            '--on-subsequent-invoke',
            type=click.Choice([RESUME, RERUN, UPDATE],
                              case_sensitive=False),
            default=RERUN,
            show_default=RERUN,
            help=helptexts.SUBSEQUENT_INVOKE)

        self.on_failure = click.option('--on-failure',
                                       type=click.Choice([CANCEL,
                                                          DONOTHING,
                                                          ROLLBACK_FULL,
                                                          ROLLBACK_PARTIAL,
                                                          UNINSTALL_FORCE],
                                                         case_sensitive=False),
                                       default=ROLLBACK_PARTIAL,
                                       show_default=ROLLBACK_PARTIAL,
                                       help=helptexts.ON_FAILURE)

        self.uninstall_on_success = click.option(
            '--uninstall-on-success',
            type=click.BOOL,
            default=DEFAULT_UNINSTALL_ON_SUCCESS,
            show_default=DEFAULT_UNINSTALL_ON_SUCCESS,
            help=helptexts.UNINSTALL_ON_SUCCESS)

        self.dry_run = click.option('--dry-run',
                                    is_flag=True,
                                    default=False,
                                    show_default=False)

        self.yum_packages = click.option('--yum-package',
                                         multiple=True,
                                         type=click.STRING,
                                         help=helptexts.YUM_PACKAGES,
                                         callback=yum_packages_callback)


options = Options()
