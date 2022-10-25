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

from testtools import TestCase

from ...ecosystem_tests_cli import inputs
from ..exceptions import EcosystemTestCliException


class InputsToDictTest(TestCase):

    def test_valid_inline(self):
        resources = ['key1=value1;key2=value2']
        result = inputs.inputs_to_dict(resources)
        self.assertDictEqual(result, {'key1': 'value1',
                                      'key2': 'value2'})

    def test_no_value_inline(self):
        resources = ['key1_without_value']
        self._assert_raise_not_dict_error(resources)

    def test_valid_yaml(self):
        resources = [os.path.join(os.path.dirname(__file__),
                                  'resources',
                                  'inputs',
                                  'valid_inputs.yaml')]
        result = inputs.inputs_to_dict(resources)
        self.assertDictEqual(result, {'key1': 'value1',
                                      'key2': 'value2'})

    def test_not_valid_yaml_format(self):
        resources = [os.path.join(os.path.dirname(__file__),
                                  'resources',
                                  'inputs',
                                  'invalid_yaml_format.yaml')]
        with self.assertRaisesRegexp(EcosystemTestCliException,
                                     'is not a valid YAML.'):
            inputs.inputs_to_dict(resources)

    def test_yaml_not_dict(self):
        resources = [os.path.join(os.path.dirname(__file__),
                                  'resources',
                                  'inputs',
                                  'not_dict.yaml')]
        self._assert_raise_not_dict_error(resources)

    def _assert_raise_not_dict_error(self, resources):
        with self.assertRaisesRegexp(EcosystemTestCliException,
                                     'does not represent a dictionary'):
            inputs.inputs_to_dict(resources)
