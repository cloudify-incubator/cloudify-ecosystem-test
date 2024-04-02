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
import sys
import deepdiff
from copy import deepcopy
from yaml import safe_load

from ..logger import logger
from ...ecosystem_tests_cli import ecosystem_tests

exit_codes = []
PLUGIN_YAML = 'plugin.yaml'
content = {
    'plugin.yaml': {}
}
TAG_PLUGINS = set('aws')


@ecosystem_tests.command(name='validate-plugin-yamls',
                         short_help='Validate Plugin YAMLs.')
@ecosystem_tests.options.directory
def validate_plugin_yamls(directory):
    directory = directory or os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

    logger.info(f'Checking for plugin.yaml in {directory}')
    check_required_plugin_yaml(directory, PLUGIN_YAML)
    if any(exit_codes):
        sys.exit(1)


def check_required_plugin_yaml(directory, filename):
    """Check that we have plugin yaml that are expected. """
    fullpath = os.path.join(directory, filename)
    if not os.path.exists(fullpath):
        logger.info('The file {} does not exist.'.format(filename))
        exit_codes.append(1)
    else:
        content[filename] = safe_load(open(fullpath)) or {}


def ignore_plugin_yaml_differences(v1, v2, directory):
    str_diff = ''
    path = os.path.join(directory, 'ignore_plugin_yaml_differences')
    diff = deepdiff.DeepDiff(v1, v2)
    str_diff = str(diff)
    if os.path.exists(path):
        with open(path) as outfile:
            current = outfile.read()
            if current.strip('\n') == str_diff:
                return True
            logger.debug('current {}'.format(current))
    if str_diff:
        logger.debug('strdiff {}'.format(str_diff))
    logger.debug('If those differences are expected, '
                 'please update the file ignore_plugin_yaml_differences')
