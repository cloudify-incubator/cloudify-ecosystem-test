########
# Copyright (c) 2014-2023 Cloudify Platform Ltd. All rights reserved
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

import io
import json
import mock
import unittest

from ..new_cicd import marketplace as mod


@mock.patch('ecosystem_cicd_tools.utils.urllib.request.urlopen')
class TestNewMarketplace(unittest.TestCase):

    @staticmethod
    def get_resp(json_resp):
        return io.StringIO(json.dumps(json_resp))

    def test_delete_node_type(self, m):
        m.return_value = self.get_resp({'status': 200})
        mod.delete_node_type('foo')
        expected = {
            'url': 'https://marketplace.cloudify.co/node-types/foo',
            'method': 'DELETE'
            }
        m.assert_called_with(**expected)

    def test_delete_plugin_version(self, m):
        m.return_value = self.get_resp({'status': 200})
        mod.delete_plugin_version('foo', 'bar')
        expected = {
            'url': 'https://marketplace.cloudify.co/plugins/foo/bar',
            'method': 'DELETE'
            }
        m.assert_called_with(**expected)

    def test_get_plugin_id(self, m):
        m.return_value = self.get_resp(
            {
                'status': 200,
                'items': [
                    {
                        'id': 'bar'
                    }
                ]
            }
        )
        result = mod.get_plugin_id('foo')
        expected = {
            'url': 'https://marketplace.cloudify.co/plugins?name=foo',
        }
        m.assert_called_with(**expected)
        assert result == 'bar'

    @mock.patch(
        'ecosystem_cicd_tools.new_cicd.marketplace'
        '.urllib.request.urlopen')
    def test_list_versions(self, *_):
        m = _[1]
        m.return_value = self.get_resp(
            {
                'status': 200,
                'items': [
                    {
                        'id': 'bar',
                        'version': '1.0.1',
                    },
                    {
                        'id': 'baz',
                        'version': '0.100.0',
                    },
                    {
                        'id': 'qux',
                        'version': '2.0.0',
                    },
                ]
            }
        )
        result = mod.list_versions('foo')
        expected = 'https://marketplace.cloudify.co/plugins/foo/versions'
        m.assert_called_with(expected)
        assert result == ['0.100.0', '1.0.1', '2.0.0']

    def test_get_node_types_diff(self, m):
        old_resp = self.get_resp(
            {
                'status': 200,
                'items': [
                    {
                        'type': 'foo',
                        'derived_from': 'zerosandones'
                    },
                    {
                        'type': 'bar',
                        'derived_from': 'zerosandones'
                    },
                ]
            }
        )
        new_resp = self.get_resp(
            {
                'status': 200,
                'items': [
                    {
                        'type': 'foo',
                        'derived_from': 'zerosandones'
                    },
                    {
                        'type': 'bar',
                        'derived_from': 'zerosandones'
                    },
                    {
                        'type': 'baz',
                        'derived_from': 'zerosandones'
                    },
                ]
            }
        )
        m.side_effect = [old_resp, new_resp]
        result = mod.get_node_types_diff('foo', '0.0.1', '0.0.2')
        old_expected = {
            'url': 'https://marketplace.cloudify.co/node-types?'
                   '&plugin_name=foo&plugin_version=0.0.1'
        }
        new_expected = {
            'url': 'https://marketplace.cloudify.co/node-types?'
                   '&plugin_name=foo&plugin_version=0.0.2'
        }
        m.assert_has_calls(
            [
                mock.call(**old_expected),
                mock.call(**new_expected)
            ]
        )
        assert result == {
            'baz': {
                'type': 'baz',
                'derived_from': 'zerosandones'
            }
        }
