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

import time
from mock import patch
from testtools import TestCase

from ..ecosystem_tests_cli import utilities
from ..ecosystem_tests_cli.exceptions import EcosystemTestCliException  # noqa
from ..ecosystem_tests_cli.commands import create_manager  # noqa

docker_module_path = 'ecosystem_tests.ecosystem_tests_cli.' \
                     'commands.create_manager.docker.docker'


def fake_docker(*_, **kwargs):
    time.sleep(0.1)
    if kwargs.get('json_format'):
        return {}
    return 'valid result'


class UtilitiesTest(TestCase):

    def setUp(self):
        super(UtilitiesTest, self).setUp()
        self.blueprints = ['/fake/path/one', '/fake/path/two']
        self.test_id = 'test'

    def test_validate_and_generate_test_ids_success(self):
        result = utilities.validate_and_generate_test_ids(
            blueprint_path=self.blueprints, test_id=None)
        self.assertEqual(len(result), len(self.blueprints))
        self.assertEqual(result[0][0], self.blueprints[0])
        self.assertEqual(len(result[0][1]), 11)
        self.assertEqual(result[1][0], self.blueprints[1])

    def test_validate_and_generate_test_ids_multiple_bps_one_test_id(self):
        with self.assertRaisesRegexp(EcosystemTestCliException,
                                     'Please do not provide test-id with '
                                     'multiple blueprints to test.'):
            utilities.validate_and_generate_test_ids(self.blueprints,
                                                     self.test_id)

    @patch(docker_module_path, new=fake_docker)
    def test_progress_bar(self, *_, **__):
        test_url = 'https://github.com/docker-library/' \
                   'hello-world/archive/refs/heads/master.zip'
        create_manager.docker.download_and_load_docker_image(
            test_url, 'hello-world')
