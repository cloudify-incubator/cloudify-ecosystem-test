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
def prepare_test_manager(license,
                         secret,
                         file_secret,
                         encoded_secret,
                         plugin,
                         bundle_path,
                         skip_bundle_upload,
                         container_name):
    """
    This command responsible for prepare test manager.
    """

    secrets_dict = prepare_secrets_dict_for_prepare_test(secret,
                                                         file_secret,
                                                         encoded_secret)
    prepare_test_dev(plugins=plugin,
                     secrets=secrets_dict,
                     execute_bundle_upload=not skip_bundle_upload,
                     bundle_path=bundle_path)
