########
# Copyright (c) 2014-2022 Cloudify Platform Ltd. All rights reserved
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
import base64
from boto3 import client
from cloudify import ctx
from tempfile import NamedTemporaryFile

from ecosystem_tests.nerdl.api import (
    list_plugins,
    upload_plugin,
    create_secret,
)
from ecosystem_tests.ecosystem_tests_cli import (
    logger,
    secrets,
    decorators,
    ecosystem_tests
)

CLOUDIFY_HOST = 'CLOUDIFY_HOST'

HELP = """Ensure that the Cloudify Manager is ready for the test.
Create Secrets.
Upload Plugins (verify versions).
"""


@ecosystem_tests.command(name='prepare-remote-test-manager',
                         short_help=HELP)
@decorators.prepare_test_env
@ecosystem_tests.options.plugin
@ecosystem_tests.options.secret
@ecosystem_tests.options.file_secret
@ecosystem_tests.options.encoded_secrets
@ecosystem_tests.options.generate_new_aws_token
@ecosystem_tests.options.cloudify_token
@ecosystem_tests.options.cloudify_tenant
@ecosystem_tests.options.cloudify_hostname
@ecosystem_tests.options.timeout
def prepare_remote_test_manager(plugin,
                                secret,
                                file_secret,
                                encoded_secret,
                                generate_new_aws_token,
                                cloudify_token,
                                cloudify_tenant,
                                cloudify_hostname,
                                timeout):
    """
    This command responsible for prepare remote test manager.
    """

    if cloudify_hostname and (CLOUDIFY_HOST not in os.environ or
                              os.environ[CLOUDIFY_HOST] != cloudify_hostname):
        os.environ[CLOUDIFY_HOST] = cloudify_hostname
    if cloudify_token and (CLOUDIFY_TOKEN not in os.environ or
                           os.environ[CLOUDIFY_TOKEN] != cloudify_token):
        os.environ[CLOUDIFY_TOKEN] = cloudify_token
    if cloudify_tenant and (CLOUDIFY_TENANT not in os.environ or
                            os.environ[CLOUDIFY_TENANT] != cloudify_tenant):
        os.environ[CLOUDIFY_TENANT] = cloudify_tenant

    handle_secrets(timeout,
                   generate_new_aws_token,
                   secret,
                   file_secret,
                   encoded_secret)
    handle_plugins(plugin)


def generate_new_credentials(timeout):
    if timeout < 1200:
        timeout = 1200
        ctx.logger.info('Minimum timeout 900, setting to 900')

    if 'aws_access_key_id' in os.environ:
        os.environ['aws_access_key_id'.upper()] = str(base64.b64decode(
            os.environ['aws_access_key_id']), 'utf-8').strip('\n')
    if 'aws_secret_access_key' in os.environ:
        os.environ['aws_secret_access_key'.upper()] = str(base64.b64decode(
            os.environ['aws_secret_access_key']), 'utf-8').strip('\n')

    sts = client('sts')
    response = sts.get_session_token(DurationSeconds=timeout)

    os.environ['aws_access_key_id'] = base64.b64encode(
        response['Credentials']['AccessKeyId'].encode('utf-8')).decode()
    os.environ['aws_secret_access_key'] = base64.b64encode(
        response['Credentials']['SecretAccessKey'].encode('utf-8')).decode()
    os.environ['aws_session_token'] = base64.b64encode(
        response['Credentials']['SessionToken'].encode('utf-8')).decode()

    return \
        os.environ['aws_access_key_id'], \
        os.environ['aws_secret_access_key'], \
        os.environ['aws_session_token']


def handle_plugins(plugin):
    logger.logger.info('plugin: {}'.format(plugin))
    current_plugins = list_plugins()

    plugins_to_cleanup = []

    for item in plugin:
        upload = True
        split_item = item[0].split('-')
        package_name_str = split_item[2]
        package_version_str = split_item[3]
        for value in current_plugins:
            if value['package_version'] == package_version_str and \
                    value['package_name'].replace('-',
                                                  '_') in package_name_str:
                logger.logger.error(
                    'Not Uploading {}, '
                    'because similar plugin already uploaded: {}'.format(
                        item, value))
                upload = False
                continue
        if upload:
            result = upload_plugin(item[0], item[1])
            plugins_to_cleanup.append(result['id'])
    logger.logger.info('Plugins to delete: {}'.format(plugins_to_cleanup))


def create_secrets(name, is_file=False):
    """
    Create a secret on the manager.
    :param name: The secret key.
    :param is_file: Whether to create the secret from a file.
    :return:
    """
    logger.logger.info('Creating secret: {0}.'.format(name))
    try:
        value = base64.b64decode(os.environ[name].
                                 encode('utf-8')).decode('ascii')
        value = value.rstrip('\n')
    except KeyError:
        raise EcosystemTestException(
            'Secret env var not set {0}.'.format(name))
    if is_file:
        outfile = NamedTemporaryFile(
            mode='w+', dir=os.path.expanduser('~'), delete=False)
        try:
            outfile.write(value)
            outfile.flush()
            outfile.close()
            create_secret(name, filepath=outfile.name)
        finally:
            os.remove(outfile.name)
    else:
        create_secret(name, value)


def handle_secrets(timeout,
                   generate_new_aws_token,
                   secret,
                   file_secret,
                   encoded_secret):

    if generate_new_aws_token:
        aws_access_key_id, aws_secret_access_key, aws_session = \
            generate_new_credentials(timeout)

        encoded_secret.update({'aws_access_key_id': aws_access_key_id})
        encoded_secret.update({'aws_secret_access_key': aws_secret_access_key})
        encoded_secret.update({'aws_session_token': aws_session})

    secrets_dict = secrets.prepare_secrets_dict_for_prepare_test(
        secret,
        file_secret,
        encoded_secret)

    logger.logger.info('These are the secrets to do: {}'.format(secrets_dict))
    for s, f in secrets_dict.items():
        create_secrets(s, f)
