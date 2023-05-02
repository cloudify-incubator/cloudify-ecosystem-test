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

import os
import sys

from ecosystem_cicd_tools import new_cicd

from ..logger import logger
from ...ecosystem_tests_cli import ecosystem_tests


@ecosystem_tests.command(
    name='yank',
    short_help='Roll back a release. '
               'Need plugin_name, '
               'plugin_version, '
               'and maybe org. '
               'The function does the rest.')
@ecosystem_tests.options.plugin_name
@ecosystem_tests.options.plugin_version
@ecosystem_tests.options.org
def yank(plugin_name, plugin_version, org):
    plugin_id = new_cicd.marketplace.get_plugin_id(plugin_name)
    plugin_versions = new_cicd.marketplace.list_versions(plugin_id)
    if plugin_version not in plugin_versions:
        logger.info('The marketplace has not received {}'.format(
            plugin_version))
        sys.exit(1)
    plugin_versions.remove(plugin_version)
    if plugin_versions:
        old_version = plugin_versions.pop()
        logger.info('The previous version is {}'.format(old_version))
        # Get the list of node types that were added in plugin_version.
        node_types_to_remove = new_cicd.marketplace.get_node_types_diff(
            plugin_name, old_version, plugin_version)
    logger.info('Deleting {} {}'.format(plugin_name, plugin_version))
    new_cicd.marketplace.delete_plugin_version(
        plugin_id, plugin_version)
    for key, value in node_types_to_remove.items():
        logger.info('Deleting {}'.format(key))
        new_cicd.marketplace.delete_node_type(value['id'])
    # Remove the flawed release from S3.
    delete_plugin_from_s3(plugin_name, plugin_version)
    # This will tell GH client decorator what repo to work on.
    ghkw = {
        'repository_name': plugin_name,
        'organization_name': org,
    }
    logger.info('Deleting version {} {}'.format(plugin_version, ghkw))
    new_cicd.github.delete_release(
        plugin_version, **ghkw)
    # Revert "latest" release to the previous value.
    logger.info('Reverting version {} {} {}'.format(
        plugin_name, old_version, ghkw))
    new_cicd.github.plugin_release(
        plugin_name, old_version, "latest", **ghkw)


def delete_plugin_from_s3(plugin_name, plugin_version):
    bucket_path = os.path.join(
        new_cicd.s3.BUCKET_FOLDER, plugin_name, plugin_version)
    return new_cicd.s3.delete_object_from_s3(bucket_path)
