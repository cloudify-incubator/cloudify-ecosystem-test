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
import tempfile

from ecosystem_cicd_tools import new_cicd
from ecosystem_cicd_tools.utils import download_file

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
    if not plugin_id:
        logger.error('Unable to find plugin {0}. '
                     'Perhaps you meant "cloudify-{0}-plugin"?'.format(
                         plugin_name))
        sys.exit(1)
    plugin_versions = new_cicd.marketplace.list_versions(plugin_id)
    if not plugin_versions:
        logger.error(
            'Unable to find versions for plugin {0}.'.format(plugin_name))
        sys.exit(1)
    if plugin_version not in plugin_versions:
        logger.info('The marketplace has not received {}'.format(
            plugin_version))
        delete_required = False
    else:
        plugin_versions.remove(plugin_version)
        delete_required = True
    if plugin_versions:
        old_version = plugin_versions.pop()
        logger.info('The previous version is {}'.format(old_version))
        # Get the list of node types that were added in plugin_version.
        if delete_required:
            node_types_to_remove = new_cicd.marketplace.get_node_types_diff(
                plugin_name, old_version, plugin_version)
            logger.info('We will need also to delete these types: {}'.format(
                node_types_to_remove))
    logger.info('Deleting {} {}'.format(plugin_name, plugin_version))
    if delete_required:
        result = new_cicd.marketplace.delete_plugin_version(
            plugin_id, plugin_version)
        logger.info('>>>Marketplace delete response: {}'.format(result))
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
    new_cicd.github.delete_release('latest', **ghkw)
    most_recent_release = new_cicd.github.get_release(old_version, **ghkw)
    new_cicd.github.create_release(
        "latest",
        "latest",
        "reverting latest",
        commit_id=most_recent_release.target_commitish,
        **ghkw)
    copy_assets_to_release(old_version, 'latest', ghkw)


def delete_plugin_from_s3(plugin_name, plugin_version):
    bucket_path = os.path.join(
        new_cicd.s3.BUCKET_FOLDER, plugin_name, plugin_version)
    return new_cicd.s3.delete_object_from_s3(bucket_path)


def copy_assets_to_release(source_release_name, target_release_name, ghkw):
    logger.info('Copying assets from {} to {}'.format(
        source_release_name,
        target_release_name
    ))
    source_release = new_cicd.github.get_release(
        source_release_name, **ghkw)
    target_release = new_cicd.github.get_release(
        target_release_name, **ghkw)
    for asset in source_release.get_assets():
        temp_asset = tempfile.NamedTemporaryFile(mode='wb', delete=False)
        download_file(asset.browser_download_url, temp_asset)
        temp_asset.close()
        new_cicd.github.upload_asset(
            target_release, temp_asset.name, asset.label)
        os.remove(temp_asset.name)
