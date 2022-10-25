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
import json
import shutil

from ..logger import logger
from ...ecosystem_tests_cli import ecosystem_tests

from ecosystem_cicd_tools.new_cicd import bundles


@ecosystem_tests.command(name='create-bundle',
                         short_help='create plugins bundle.')
@ecosystem_tests.options.plugins_yaml_version
@ecosystem_tests.options.json_path
@ecosystem_tests.options.directory
@ecosystem_tests.options.workspace
def create_bundle(plugins_yaml_version=None,
                  json_path=None,
                  directory=None,
                  workspace=None):
    logger.error(
        'The "create-bundle" command is deprecated. '
        'Upload plugins from the Cloudify Marketplace.')
    json_content = get_json_content(json_path)
    mappings, bundle_name = bundles.get_metadata_mapping(
        json_content,
        workspace,
        get_plugin_yaml_name(plugins_yaml_version)
    )
    bundle_path = bundles.package_archive(
        mappings,
        bundle_name,
        directory,
        workspace,
        plugins_yaml_version=plugins_yaml_version)
    if workspace:
        shutil.copyfile(
            bundle_path,
            os.path.join(workspace, os.path.basename(bundle_path)))
    logger.info("bundle path is {}".format(bundle_path))


def get_json_content(json_path):
    f = open(json_path)
    data = json.load(f)
    f.close()
    return data


def get_plugin_yaml_name(version):
    plugin_yaml = None
    if version == 'v1':
        plugin_yaml = 'plugin.yaml'
    elif version == 'v2':
        plugin_yaml = 'v2_plugin.yaml'
    return plugin_yaml
