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

from mock import patch

from . import ERROR_EXIT_CODE
from ...exceptions import EcosystemTestCliException
from ..commands import BaseCliCommandTest
from ...commands.local_blueprint_test import local_blueprint_test
from ...constants import (TIMEOUT,
                          DEFAULT_ON_FAILURE,
                          DEFAULT_BLUEPRINT_PATH,
                          DEFAULT_ON_SUBSEQUENT_INVOKE,
                          DEFAULT_UNINSTALL_ON_SUCCESS)


class LocalBlueprintTest(BaseCliCommandTest):
    def setUp(self):
        super(LocalBlueprintTest, self).setUp()
        self.basic_blueprint_test_defaults = {
            'blueprint_file_name': DEFAULT_BLUEPRINT_PATH,
            'test_name': self.test_id,
            'inputs': {},
            'timeout': TIMEOUT,
            'on_subsequent_invoke': DEFAULT_ON_SUBSEQUENT_INVOKE,
            'on_failure': DEFAULT_ON_FAILURE,
            'uninstall_on_success': DEFAULT_UNINSTALL_ON_SUCCESS}

    @patch('ecosystem_tests.ecosystem_tests_cli.utilities.id_generator')
    @patch('ecosystem_tests.ecosystem_tests_cli.commands.local_blueprint_test'
           '.basic_blueprint_test_dev')
    def test_default_values(self,
                            mock_basic_blueprint_test,
                            mock_id_generator):
        mock_id_generator.return_value = self.test_id
        self.runner.invoke(local_blueprint_test, [])
        mock_basic_blueprint_test.assert_called_once_with(
            **self.basic_blueprint_test_defaults)

    def test_string_timeout(self):
        res = self.runner.invoke(local_blueprint_test, ['--timeout=str'])
        self.assertEqual(res.exit_code, ERROR_EXIT_CODE)

    def test_multiple_test_ids_inputs(self):
        res = self.runner.invoke(local_blueprint_test,
                                 ['--test_id=test1', '--test_id=test2'])
        self.assertEqual(res.exit_code, ERROR_EXIT_CODE)

    @patch('ecosystem_tests.ecosystem_tests_cli.commands.local_blueprint_test'
           '.basic_blueprint_test_dev')
    @patch('ecosystem_tests.ecosystem_tests_cli.commands.local_blueprint_test'
           '.pytest.main')
    def test_multiple_nested_tests(self,
                                   fake_pytest_main,
                                   *_):
        self.runner.invoke(local_blueprint_test,
                           ['--nested-test=/path/to/test1.py',
                            '--nested-test=/path/to/test2.py'])
        self.assertEqual(fake_pytest_main.call_count, 2)
        fake_pytest_main.assert_any_call(['-s', '/path/to/test1.py'])
        fake_pytest_main.assert_any_call(['-s', '/path/to/test2.py'])

    def test_on_subsequent_invoke_forbidden_value(self):
        res = self.runner.invoke(local_blueprint_test,
                                 ['--on_subsequent_invoke=not_allowed_val'])
        self.assertEqual(res.exit_code, ERROR_EXIT_CODE)

    def test_on_failure_forbidden_value(self):
        res = self.runner.invoke(local_blueprint_test,
                                 ['--on_failure=not_allowed_val'])
        self.assertEqual(res.exit_code, ERROR_EXIT_CODE)

    @patch('ecosystem_tests.ecosystem_tests_cli.utilities.id_generator')
    @patch('ecosystem_tests.ecosystem_tests_cli.commands.local_blueprint_test'
           '.handle_dry_run')
    def test_dry_run(self,
                     dry_run_mock,
                     mock_id_generator):
        mock_id_generator.return_value = self.test_id
        self.runner.invoke(local_blueprint_test, ['--dry-run'])
        dry_run_mock.assert_called_once()

    @patch('ecosystem_tests.ecosystem_tests_cli.utilities.id_generator')
    @patch('ecosystem_tests.ecosystem_tests_cli.commands.local_blueprint_test'
           '.basic_blueprint_test_dev')
    def test_single_input(self,
                          mock_basic_blueprint_test,
                          mock_id_generator):
        mock_id_generator.return_value = self.test_id
        self.runner.invoke(local_blueprint_test, ['--inputs', 'key1=value1'])
        self.basic_blueprint_test_defaults['inputs'] = {'key1': 'value1'}
        mock_basic_blueprint_test.assert_called_once_with(
            **self.basic_blueprint_test_defaults)

    @patch('ecosystem_tests.ecosystem_tests_cli.utilities.id_generator')
    @patch('ecosystem_tests.ecosystem_tests_cli.commands.local_blueprint_test'
           '.basic_blueprint_test_dev')
    def test_multiple_inputs(self,
                             mock_basic_blueprint_test,
                             mock_id_generator):
        mock_id_generator.return_value = self.test_id
        self.runner.invoke(local_blueprint_test,
                           ['-i', 'key1=value1', '-i', 'key2=value2'])
        self.basic_blueprint_test_defaults['inputs'] = {'key1': 'value1',
                                                        'key2': 'value2'}
        mock_basic_blueprint_test.assert_called_once_with(
            **self.basic_blueprint_test_defaults)

    def test_multiple_blueprints_and_test_id(self):
        with self.assertRaisesRegexp(EcosystemTestCliException,
                                     'Please not provide test-id with '
                                     'multiple blueprints to test.'):
            self.runner.invoke(local_blueprint_test,
                               ['--blueprint-path', '/path/to/bp1.yaml',
                                '--blueprint-path', '/path/to/bp2.yaml',
                                '--test-id', self.test_id],
                               catch_exceptions=False)
