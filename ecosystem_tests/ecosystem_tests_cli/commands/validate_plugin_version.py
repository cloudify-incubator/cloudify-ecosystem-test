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

import re
from ecosystem_cicd_tools.validations import \
    validate_plugin_version as validate

from .validate_branch import get_branch

from ...ecosystem_tests_cli import ecosystem_tests

# Semantic versioning pattern
SEMVER_PATTERN = '^([0-9]+)\\.([0-9]+)\\.([0-9]+)(?:-([0-9A-Za-z-]+(?:\\.' \
                 '[0-9A-Za-z-]+)*))?(?:\\+[0-9A-Za-z-]+)?\\-build$'


@ecosystem_tests.command(name='validate-plugin-version',
                         short_help='Validate plugin version.')
@ecosystem_tests.options.directory
def validate_plugin_version(directory):
    branch_name = get_branch()
    pattern = re.compile(SEMVER_PATTERN)
    if pattern.search(branch_name):
        validate(directory, branch_name)
    else:
        validate(directory)
