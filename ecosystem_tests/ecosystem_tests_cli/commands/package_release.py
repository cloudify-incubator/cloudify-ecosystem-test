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
        version = find_version_in_files(directory)
        plugin_release_with_latest(name, version, v2_plugin=v2_plugin)
    except (RuntimeError, FileNotFoundError):
        plugin_yaml = os.path.join(directory, 'plugin.yaml')
        plugin_release_with_latest(
            name, get_plugin_yaml_version(plugin_yaml), v2_plugin=v2_plugin)


def find_version_in_files(directory):
    __version__py = find_version_file(directory)
    try:
        return find_version(__version__py)
    except (TypeError, RuntimeError):
        return find_version(os.path.join(directory, 'setup.py'))


def find_version_file(directory):
    return find('__version__.py', directory)


def find(name, path):
    for root, _, files in walklevel(path, depth=2):
        if name in files:
            return os.path.join(root, name)


def walklevel(path, depth=1):
    """It works just like os.walk, but you can pass it a level parameter
       that indicates how deep the recursion will go.
       If depth is 1, the current directory is listed.
       If depth is 0, nothing is returned.
       If depth is -1 (or less than 0), the full depth is walked.
    """
    # Borrowed: https://gist.githubusercontent.com/TheMatt2/
    # faf5ca760c61a267412c46bb977718fa/raw/
    # ad5643dd1fedf0fd3addcbbd4e22a05136edca02/walklevel.py

    if depth < 0:
        for root, dirs, files in os.walk(path):
            yield root, dirs[:], files
        return
    elif depth == 0:
        return

    base_depth = path.rstrip(os.path.sep).count(os.path.sep)
    for root, dirs, files in os.walk(path):
        yield root, dirs[:], files
        cur_depth = root.count(os.path.sep)
        if base_depth + depth <= cur_depth:
            del dirs[:]
