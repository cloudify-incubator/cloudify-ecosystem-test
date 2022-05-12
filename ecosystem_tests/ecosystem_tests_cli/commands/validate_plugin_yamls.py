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
import sys
from copy import deepcopy
from yaml import safe_load

from ..logger import logger
from ...ecosystem_tests_cli import ecosystem_tests

exit_codes = []
plugin_yamls = ['plugin.yaml', 'v2_plugin.yaml']
content = {
    'plugin.yaml': {},
    'v2_plugin.yaml': {}
}
V2_KEYS = ['labels', 'blueprint_labels', 'resource_tags']
TAG_PLUGINS = set('aws')


@ecosystem_tests.command(name='validate-plugin-yamls',
                         short_help='Validate Plugin YAMLs.')
@ecosystem_tests.options.directory
def validate_plugin_yamls(directory):
    directory = directory or os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

    for plugin_yaml in plugin_yamls:
        check_required_plugin_yaml(directory, plugin_yaml)

    check_content_rules()

    if any(exit_codes):
        sys.exit(1)


def check_required_plugin_yaml(directory, filename):
    """Check that we have all plugin yamls that are expected. """
    fullpath = os.path.join(directory, filename)
    if not os.path.exists(fullpath):
        logger.info('The file {} does not exist.'.format(filename))
        exit_codes.append(1)
    else:
        content[filename] = safe_load(open(fullpath)) or {}


def check_content_rules():
    check_v1_plugin_yaml_no_forbidden_keys()
    check_v2_plugin_yaml_required_keys()
    compare_v2_v1_plugin_yaml()


def check_v1_plugin_yaml_no_forbidden_keys():
    """Check that plugin.yaml does not contain any incompatible keys."""
    v1_plugin_yaml_keys = content['plugin.yaml'].keys()
    for forbidden in V2_KEYS:
        if forbidden in v1_plugin_yaml_keys:
            logger.error('plugin.yaml '
                         'contains forbidden key {}'.format(forbidden))
            exit_codes.append(1)


def check_v2_plugin_yaml_required_keys():
    """Make sure that v2_plugin.yaml has expected keys."""
    if not content['v2_plugin.yaml']:
        return
    plugins = set(content['v2_plugin.yaml']['plugins'])
    v2_plugin_yaml_keys = content['v2_plugin.yaml'].keys()
    for expected in V2_KEYS:
        if expected == 'resource_tags' and not plugins.issubset(TAG_PLUGINS):
            continue
        if expected not in v2_plugin_yaml_keys:
            logger.error('v2_plugin.yaml '
                         'does not contain expected key {}'.format(expected))
            exit_codes.append(1)


def compare_v2_v1_plugin_yaml():
    """Make sure that plugin.yaml and v2_plugin.yaml are the same core."""
    if not content['v2_plugin.yaml']:
        return
    cp_v2_plugin_yaml = deepcopy(content['v2_plugin.yaml'])
    for expected in V2_KEYS:
        if expected in cp_v2_plugin_yaml:
            del cp_v2_plugin_yaml[expected]
    if not cp_v2_plugin_yaml == content['plugin.yaml']:
        logger.error('plugin.yaml and v2_plugin.yaml '
                     'are not equivalent after removing v2 features.')
        exit_codes.append(1)
