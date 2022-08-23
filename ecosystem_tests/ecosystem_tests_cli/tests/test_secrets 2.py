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
import base64

from testtools import TestCase

from ...ecosystem_tests_cli import secrets
from ..exceptions import EcosystemTestCliException


class SecretsTest(TestCase):

    def setUp(self):
        super(SecretsTest, self).setUp()
        self.secrets = ['key1=value1', 'key2=value2']
        self.encoded_value1 = self._encode('value1')
        self.encoded_value2 = self._encode('value2')
        self.only_key = ['key1']

    @staticmethod
    def _encode(val):
        return base64.b64encode(val.encode('utf-8')).decode('ascii')

    def test_secrets_to_dict_valid(self):
        result = secrets.secrets_to_dict(self.secrets)
        self.assertDictEqual(result,
                             {'key1': self.encoded_value1,
                              'key2': self.encoded_value2})

    def test_secrets_to_dict_no_value(self):
        with self.assertRaisesRegexp(EcosystemTestCliException,
                                     secrets.ERR_MSG.format(self.only_key[0])):
            secrets.secrets_to_dict(self.only_key)

    def test_file_secrets_to_dict_valid(self):
        file_secret = ['key1=' + os.path.join(os.path.dirname(__file__),
                                              'resources',
                                              'secrets',
                                              'file_secret.txt')]
        result = secrets.file_secrets_to_dict(file_secret)
        self.assertDictEqual(result,
                             {'key1': self.encoded_value1})

    def test_file_secrets_to_dict_no_path(self):
        with self.assertRaisesRegexp(EcosystemTestCliException,
                                     secrets.ERR_MSG_FILE_SECRET.format(
                                         self.only_key[0])):
            secrets.file_secrets_to_dict(self.only_key)

    def test_file_secrets_to_dict_no_file(self):
        path_doesnt_exist = os.path.join(os.path.dirname(__file__),
                                         'resources',
                                         'secrets',
                                         'not_existing_file.txt')
        no_file_secret = ['key1=' + path_doesnt_exist]
        with self.assertRaisesRegexp(EcosystemTestCliException,
                                     'Secret file {path} dosen`t '
                                     'exist!'.format(
                                         path=path_doesnt_exist)):
            secrets.file_secrets_to_dict(no_file_secret)

    def test_encoded_secrets_valid(self):
        encoded_secrets = ['key1=' + self.encoded_value1,
                           'key2=' + self.encoded_value2]
        result = secrets.encoded_secrets_to_dict(encoded_secrets)
        self.assertDictEqual(result,
                             {'key1': self.encoded_value1,
                              'key2': self.encoded_value2})

    def test_encoded_secrets_not_encoded_values(self):
        not_encoded_value = ['key1=not_encoded_value']
        with self.assertRaisesRegexp(EcosystemTestCliException,
                                     'string: {val} is not base64 '
                                     'encoded'.format(
                                         val='not_encoded_value')):
            secrets.encoded_secrets_to_dict(not_encoded_value)
