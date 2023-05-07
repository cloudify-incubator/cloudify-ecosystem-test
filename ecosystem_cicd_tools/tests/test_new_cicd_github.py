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
import os
import json
import mock
import unittest

from ..new_cicd import github as mod


class mockCommit(object):
    pass


@mock.patch('ecosystem_cicd_tools.new_cicd.github.github')
class TestNewGithub(unittest.TestCase):

    def test_delete_release(self, m):
        os.environ.update(
            {
                'RELEASE_BUILD_TOKEN': 'foo',
                'CIRCLE_PROJECT_REPONAME': 'bar',
                'CIRCLE_PROJECT_USERNAME': 'baz',
                'CIRCLE_SHA1': 'taco',
            }
        )
        repo_mock = mock.MagicMock()
        release_mock = mock.MagicMock()
        ref_mock = mock.MagicMock()
        repo_mock.get_releases.return_value = [
            {
                'name': '0.0.2',
                'id': 'foo',
            },
            {
                'name': '0.0.1',
                'id': 'bar'
            }
        ]
        repo_mock.get_release.return_value = release_mock
        repo_mock.get_git_ref.return_value = ref_mock
        mockGithub = mock.MagicMock()
        mockGithub.get_repo.return_value = repo_mock
        m.Github.return_value = mockGithub
        commit_mock = mock.MagicMock()
        commit_mock.Commit = mockCommit
        m.Commit = commit_mock
        mod.delete_release(
            '0.0.2',
            repository_name='foo',
            organization_name='bar'
        )
        repo_mock.get_releases.assert_called()
        repo_mock.get_release.assert_called_with('foo')
        release_mock.delete_release.assert_called()
        repo_mock.get_git_ref.assert_called_with('tags/0.0.2')
        ref_mock.delete.assert_called()
