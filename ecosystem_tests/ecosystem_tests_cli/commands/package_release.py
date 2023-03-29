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

from ...ecosystem_tests_cli import ecosystem_tests
from ecosystem_cicd_tools.validations import get_plugin_yaml_version
from ecosystem_cicd_tools.release import (
  plugin_release_with_latest, find_version)


@ecosystem_tests.command(name='package-release',
                         short_help='package release.')
@ecosystem_tests.options.directory
@ecosystem_tests.options.name
@ecosystem_tests.options.v2_plugin
def package_release(directory, name, v2_plugin=False):
    # TODO: Rewrite all this.
    # The process should be as follows:
    # Validate Plugin YAML
    # Create a new numbered release.
    # Create new plugins.json and v2_plugins.json
    # Build a new Bundle.
    # Update the "latest" release.
    if not name:
        raise ValueError('Argument name can not be "NoneType"')
    try:
        __version__py = find_version_file(directory)
        plugin_release_with_latest(
            name, find_version(__version__py), v2_plugin=v2_plugin)
    except (RuntimeError, FileNotFoundError):
        plugin_yaml = os.path.join(directory, 'plugin.yaml')
        plugin_release_with_latest(
            name, get_plugin_yaml_version(plugin_yaml), v2_plugin=v2_plugin)


def find_version_file(directory):
    return find('__version__.py', directory)


def find(name, path):
    for root, _, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
