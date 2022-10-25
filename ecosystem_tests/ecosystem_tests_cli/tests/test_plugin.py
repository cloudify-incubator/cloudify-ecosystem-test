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

from ...ecosystem_tests_cli import plugins
from ..exceptions import EcosystemTestCliException

TEST_PLUGIN_WAGON_URL = 'https://github.com/cloudify-cosmo/cloudify-aws' \
                        '-plugin/releases/download/2.5.11/cloudify_aws_' \
                        'plugin-2.5.11-centos-Core-py27.py36-none-linux_' \
                        'x86_64.wgn'
TEST_PLUGIN_YAML_URL = 'https://github.com/cloudify-cosmo/cloudify-aws' \
                       '-plugin/releases/download/2.5.11/plugin.yaml'

GOOGLE = 'https://www.google.com'


class CreatePluginListTest(TestCase):

    def setUp(self):
        super(CreatePluginListTest, self).setUp()
        self.plugins_input_ordered = [
            (TEST_PLUGIN_WAGON_URL, TEST_PLUGIN_YAML_URL)]

    def test_valid_urls(self):
        result = plugins.create_plugins_list(self.plugins_input_ordered)
        self.assertListEqual(result, self.plugins_input_ordered)

    def test_valid_urls_reverse_order(self):
        plugins_input = [(TEST_PLUGIN_YAML_URL, TEST_PLUGIN_WAGON_URL)]
        result = plugins.create_plugins_list(plugins_input)
        self.assertListEqual(result, self.plugins_input_ordered)

    def test_invalid_url(self):
        # Ruin wagon url.
        invalid_wagon_url = TEST_PLUGIN_WAGON_URL + 'n'
        plugins_input = [(invalid_wagon_url, TEST_PLUGIN_YAML_URL)]
        with self.assertRaisesRegexp(EcosystemTestCliException,
                                     'plugin url {url} is not valid!'.format(
                                         url=invalid_wagon_url)):
            plugins.create_plugins_list(plugins_input)

    def test_no_wagon_url(self):
        plugins_input = [(GOOGLE, TEST_PLUGIN_YAML_URL)]
        with self.assertRaisesRegexp(EcosystemTestCliException,
                                     'Plugin input - Could not find which '
                                     'url is for wagon and which is for '
                                     'plugin.yaml'):
            plugins.create_plugins_list(plugins_input)
