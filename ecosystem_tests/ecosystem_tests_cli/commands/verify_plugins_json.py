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
import json
import yaml

from ecosystem_cicd_tools.new_cicd import s3
from ecosystem_cicd_tools.new_cicd import actions
from ...ecosystem_tests_cli import (logger, ecosystem_tests)


@ecosystem_tests.command(name='verify-plugins-json',
                         short_help='Create a new plugins JSON file.')
@ecosystem_tests.options.name
@ecosystem_tests.options.plugin_version
@ecosystem_tests.options.plugins_yaml_version
def verify_plugins_json(name, plugin_version, plugins_yaml_version):
    plugin_version = plugin_version or get_plugin_version()
    plugins_json_content = download_file(plugins_yaml_version)
    if not actions.check_plugins_json(
            name,
            plugin_version,
            plugins_json_content,
            plugins_yaml_version):
        raise RuntimeError(
            'Failed to find {} {}'.format(name, plugin_version))


def download_file(plugins_yaml_version):
    if plugins_yaml_version == 'v1':
        filename = 'plugins.json'
    elif plugins_yaml_version == 'v2':
        filename = 'v2_plugins.json'
    remote_name = '{}/{}'.format(
            s3.BUCKET_FOLDER,
            os.path.basename(filename),
        )
    logger.logger.info('Downloading {} to s3.'.format(remote_name))
    s3.download_from_s3(
        filename,
        remote_name
    )
    with open(filename, 'r') as outf:
        return json.load(outf)


def get_plugin_version():
    plugin_yaml = os.path.join(
        '.',
        'plugin.yaml'
    )
    with open(plugin_yaml, 'r') as outf:
        plugin_yaml_content = yaml.safe_load(outf)
        for _, v in plugin_yaml_content['plugins'].items():
            return v['package_version']
