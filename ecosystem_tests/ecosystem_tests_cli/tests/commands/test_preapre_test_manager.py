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

import base64
from mock import patch

from . import ERROR_EXIT_CODE
from ...exceptions import EcosystemTestCliException
from ..commands import BaseCliCommandTest
from ...commands.prepare_test_manager import prepare_test_manager

DEMO_LICENCE = 'ZGVtbyBsaWNlbnNlCg=='


class PrepareTestManagerTest(BaseCliCommandTest):

    @patch('ecosystem_tests.ecosystem_tests_cli.commands.prepare_test_manager'
           '.prepare_test_dev')
    def test_prepare_manager_license_only(self, mock_prepare_test_dev):
        self.runner.invoke(prepare_test_manager, ['--license', DEMO_LICENCE])
        mock_prepare_test_dev.assert_called_once_with(
            plugins=[],
            secrets={},
            execute_bundle_upload=True,
            bundle_path=None,
            yum_packages=[])

    def test_prepare_manager_not_base64_encoded_licence(self):
        with self.assertRaisesRegexp(EcosystemTestCliException,
                                     'is not base64 encoded.'):
            self.runner.invoke(prepare_test_manager,
                               ['--license', 'not base64 encoded string'],
                               catch_exceptions=False)

    @patch('ecosystem_tests.ecosystem_tests_cli.commands.prepare_test_manager'
           '.prepare_test_dev')
    def test_prepare_manager_test_multiple_secrets(self,
                                                   mock_prepare_test_dev,
                                                   *_):
        encoded_value = _encode('value3')
        self.runner.invoke(prepare_test_manager,
                           ['--license', DEMO_LICENCE, '-s', 'key1=value1',
                            '-s', 'key2=value2', '-es',
                            'key3=' + encoded_value], catch_exceptions=False)
        expected_secrets_dict = {'key1': False, 'key2': False, 'key3': True}
        mock_prepare_test_dev.assert_called_once_with(
            plugins=[],
            secrets=expected_secrets_dict,
            execute_bundle_upload=True,
            bundle_path=None,
            yum_packages=[])

    def test_prepare_manager_missing_arg_plugin(self):
        res = self.runner.invoke(prepare_test_manager,
                                 ['--license', DEMO_LICENCE, '--plugin',
                                  'wagon_url'])
        self.assertEqual(res.exit_code, ERROR_EXIT_CODE)

    @patch(
        'ecosystem_tests.ecosystem_tests_cli.ecosystem_tests'
        '.create_plugins_list',
        return_value=[('wagon', 'yaml')])
    @patch('ecosystem_tests.ecosystem_tests_cli.commands.prepare_test_manager'
           '.prepare_test_dev')
    def test_prepare_manager_multiple_plugins(self, mock_prepare_test_dev, *_):
        self.runner.invoke(prepare_test_manager,
                           ['--license', DEMO_LICENCE, '--plugin',
                            'wagon1_url', 'plugin_yaml1_url', '--plugin',
                            'wagon2_url', 'plugin_yaml2_url'],
                           catch_exceptions=False)
        mock_prepare_test_dev.assert_called_once_with(
            plugins=[('wagon', 'yaml')],
            secrets={},
            execute_bundle_upload=True,
            bundle_path=None,
            yum_packages=[])

    def test_prepare_test_bundle_path_not_exists(self):
        res = self.runner.invoke(prepare_test_manager,
                                 ['--license', DEMO_LICENCE, '--bundle-path',
                                  '/fake/path'])
        self.assertEqual(res.exit_code, ERROR_EXIT_CODE)


def _encode(string_to_encode):
    return base64.b64encode(string_to_encode.encode('utf-8')).decode('ascii')
