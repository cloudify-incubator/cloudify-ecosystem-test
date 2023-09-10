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

import mock
import unittest

from ..new_cicd import s3 as mod


@mock.patch('ecosystem_cicd_tools.new_cicd.s3.get_boto_service')
class TestNewS3(unittest.TestCase):

    def test_delete_object(self, m):
        delete = mock.MagicMock()
        bucket = mock.Mock()
        bucket.delete_objects.return_value = delete
        s3 = mock.Mock()
        s3.Bucket.return_value = bucket
        m.return_value = s3

        object_name = 'foo'
        expected = {
            'Delete': {
                'Objects': [
                    {
                        'Key': object_name
                    }
                ]
            }
        }
        mod.delete_object_from_s3(object_name)
        s3.Bucket.assert_called_with(mod.BUCKET_NAME)
        bucket.delete_objects.assert_called_with(**expected)
