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

from ecosystem_cicd_tools.github_stuff import merge_documentation_pulls
from ...ecosystem_tests_cli import ecosystem_tests


@ecosystem_tests.command(name='merge-docs',
                         short_help='merge docs.')
@ecosystem_tests.options.repo
def merge_docs(repo):
    if 'CIRCLE_BRANCH' in os.environ:
        merge_documentation_pulls(repo, branch=os.environ['CIRCLE_BRANCH'])
    else:
        merge_documentation_pulls(repo)
