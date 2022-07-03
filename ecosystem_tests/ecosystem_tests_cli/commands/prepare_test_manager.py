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

from boto3 import client
from cloudify import ctx

from ..utilities import prepare_test_env
from ...dorkl.runners import prepare_test_dev
from ...ecosystem_tests_cli import ecosystem_tests
from ..secrets import prepare_secrets_dict_for_prepare_test


@ecosystem_tests.command(name='prepare-test-manager',
                         short_help='Prepare test manager(licence, '
                                    'secrets, etc.)')
@prepare_test_env
@ecosystem_tests.options.license
@ecosystem_tests.options.secret
@ecosystem_tests.options.file_secret
@ecosystem_tests.options.encoded_secrets
@ecosystem_tests.options.plugin
@ecosystem_tests.options.plugins_bundle
@ecosystem_tests.options.skip_bundle_upload
@ecosystem_tests.options.container_name
@ecosystem_tests.options.yum_packages
@ecosystem_tests.options.generate_new_aws_token
@ecosystem_tests.options.timeout
def prepare_test_manager(license,
                         secret,
                         file_secret,
                         encoded_secret,
                         plugin,
                         bundle_path,
                         skip_bundle_upload,
                         container_name,
                         yum_package,
                         generate_new_aws_token,
                         timeout):
    """
    This command responsible for prepare test manager.
    """
    if generate_new_aws_token:
        aws_access_key_id, aws_secret_access_key, aws_session = \
            generate_new_credentials(timeout)
        encoded_secret.append({'aws_acces_key_id': aws_access_key_id})
        encoded_secret.append({'aws_secret_access_key': aws_secret_access_key})
        encoded_secret.append({'aws_session': aws_session})

    secrets_dict = prepare_secrets_dict_for_prepare_test(secret,
                                                         file_secret,
                                                         encoded_secret)
    prepare_test_dev(plugins=plugin,
                     secrets=secrets_dict,
                     execute_bundle_upload=not skip_bundle_upload,
                     bundle_path=bundle_path,
                     yum_packages=yum_package)


def generate_new_credentials(timeout):
    if timeout < 900:
        timeout = 900
        ctx.logger.info('Minimum timeout 900, setting to 900')
    sts = client('sts')
    response = sts.get_session_token(DurationSeconds=timeout)
    aws_access_key_id = response['Credentials']['AccessKeyId']
    aws_secret_access_key = response['Credentials']['SecretAccessKey']
    aws_session_token = response['Credentials']['SessionToken']
    return aws_access_key_id, aws_secret_access_key, aws_session_token
