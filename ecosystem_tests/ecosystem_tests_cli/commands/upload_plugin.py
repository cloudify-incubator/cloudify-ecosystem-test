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

import sys
import logging
from ecosystem_cicd_tools.new_cicd.marketplace import (
    get_plugin_id,
    get_plugin_versions,
    get_plugin_release_spec_from_marketplace)
from ..logger import logger
from ...dorkl.cloudify_api import plugins_upload
from ..decorators import prepare_test_env
from ...ecosystem_tests_cli import ecosystem_tests


@ecosystem_tests.command(name='upload-plugin',
                         short_help='Upload plugins.')
@prepare_test_env
@ecosystem_tests.options.plugin_name
@ecosystem_tests.options.plugin_version
def upload_plugin(plugin_name, plugin_version):
    """
    Upload wagon and yamls to Cfy Manager.
    """
    repo = 'cloudify-{}-plugin'.format(plugin_name)
    plugin_id = get_plugin_id(repo)
    plugin_version = plugin_version or get_latest_version(
        plugin_id, repo)
    spec = get_plugin_release_spec_from_marketplace(
        plugin_id, plugin_version)
    yaml_url_dict = get_spec_item(
        spec['yaml_urls'], 'dsl_version', 'cloudify_dsl_1_4')
    wagon_url_dict = get_spec_item(
        spec['wagon_urls'], 'release', 'Centos Core')
    if not yaml_url_dict['url'] or not wagon_url_dict['url']:
        logging.error('Unable to find wagon or yaml for {} {} in {} {}'.format(
            repo, plugin_version, yaml_url_dict, wagon_url_dict
        ))
        sys.exit(1)
    plugins_upload(wagon_url_dict['url'], yaml_url_dict['url'])


def get_latest_version(plugin_id, name):
    versions = get_plugin_versions(plugin_id)
    if not versions:
        logging.error(
            'Unable to find plugin version for plugin {}'.format(name))
        sys.exit(1)
    return versions.pop()


def get_spec_item(items, key, value):
    for item in items:
        if item[key] == value:
            return item
