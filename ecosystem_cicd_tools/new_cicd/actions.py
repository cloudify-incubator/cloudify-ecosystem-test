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
from time import sleep
from copy import deepcopy
from urllib.parse import urlparse

from . import s3
from . import github
from . import logging
from . import plugins_json
from . import marketplace


@github.with_github_client
def upload_assets_to_release(assets, release_name, repository, **_):
    """ Upload a bunch of assets to release.
    Example assets:
    {
        'plugin.yaml': 'cloudify-aws-plugin/plugin.yaml',
        'v2_plugin.yaml': 'cloudify-aws-plugin/v2_plugin.yaml',
        'cloudify_aws_plugin-3.0.4-centos-Core-py36-none-linux_aarch64.wgn': 'cloudify-aws-plugin/cloudify_aws_plugin-3.0.4-centos-Core-py36-none-linux_aarch64.wgn',
    }
    Example release name: latest, or '3.0.5'

    :param assets:
    :param release_name:
    :param repository:
    :param _:
    :return:
    """  # noqa

    release_name = release_name or github.get_most_recent_release(repository)

    release = github.get_release(release_name, repository)

    if not release:
        raise RuntimeError(
            'The release {release} does not exist.'.format(release=release))

    for label, path, in assets.items():
        github.upload_asset(release, path, label)
        s3.upload_plugin_asset_to_s3(path, repository.name, release_name)

    if release_name == 'latest':
        return

    if repository.name.endswith('-plugin'):
        marketplace.call_plugins_webhook(
            repository.name,
            release_name,
            os.environ.get('CIRCLE_USERNAME', 'earthmant')
        )

    # Time to wait for the plugin to load
    # And checking that everything was updated correctly
    max_time = 360  # it should not take longer than 360 seconds.
    min_time = 20  # It should definitely take longer than 20 seconds.
    interval = 10  # We check every 10 seconds.
    current = 0
    while True:
        if current < min_time:
            current += interval
            continue
        elif current > max_time:
            raise RuntimeError(
                'Timed out waiting for marketplace plugin update.')
        elif checking_the_upload_of_the_plugin(repository,
                                               release_name,
                                               assets):
            logging.logger.info(
                'Verified plugin release in {} seconds'.format(current))
            break
        sleep(interval)
        current += interval


def checking_the_upload_of_the_plugin(repository,
                                      release_name,
                                      asset_workspace):

    # marketplace
    if not marketplace.get_node_types_for_plugin_version(
            repository.name, release_name):
        return False

    # github
    latest_release = github.get_release(release_name, repository)
    assets_list_github = []
    for asset in latest_release.get_assets():
        logging.logger.info('Asset in release: {}'.format(asset.name))
        assets_list_github.append(asset.name)

    return check_asset_problems(
        marketplace.get_assets(repository, release_name),
        assets_list_github,
        s3.get_assets(repository.name, release_name),
        list(asset_workspace.keys()),
        repository.name,
        release_name
    )


def check_asset_problems(marketplace_assets,
                         github_assets,
                         s3_assets,
                         assets,
                         plugin_name,
                         version):
    problems = []
    for asset in assets:
        if asset.endswith('wgn.md5'):
            continue
        marketplace_key = 'https://github.com/cloudify-cosmo/{}/' \
                          'releases/download/{}/{}'.format(plugin_name,
                                                           version,
                                                           asset)
        if marketplace_key not in marketplace_assets:
            problems.append('{} not found in {}'.format(
                marketplace_key, marketplace_assets))
        if asset not in github_assets:
            problems.append('{} not found in {}'.format(
                asset, github_assets))
        if asset not in s3_assets:
            problems.append('{} not found in {}'.format(
                asset, s3_assets))
    if problems:
        logging.logger.error(
            'Failed to verify all assets: {}'.format(problems))
        return False
    return True


@github.with_github_client
def get_latest_version(repository, **kwargs):
    logging.logger.info(
        'Getting latest version for {}/{}'.format(
            kwargs.get('organization_name'),
            kwargs.get('repository_name')
        )
    )
    latest_release = github.get_most_recent_release(repository)
    logging.logger.info('Got this version: {}'.format(latest_release))
    return latest_release


def populate_plugins_json(plugin_yaml_name='plugin.yaml'):
    json_content = []
    for i in range(0, len(plugins_json.JSON_TEMPLATE)):
        plugin_content = deepcopy(plugins_json.JSON_TEMPLATE[i])
        parsed_url = urlparse(plugin_content['releases'])
        repository_name = parsed_url.path.split('/')[-2]
        assert repository_name == plugin_content['name']
        organization_name = parsed_url.path.split('/')[-3]
        version = get_latest_version(
            repository_name=repository_name,
            organization_name=organization_name)
        logging.logger.info('Got this version: {}'.format(version))
        plugin_yaml_url = s3.get_plugin_yaml_url(
            plugin_name=repository_name,
            filename=plugin_yaml_name,
            plugin_version=version,
        )
        wagons_list = plugins_json.get_wagons_list(
            plugin_name=repository_name,
            plugin_version=version
        )
        plugin_content = deepcopy(plugins_json.JSON_TEMPLATE[i])
        plugin_content['version'] = version
        plugin_content['link'] = plugin_yaml_url
        plugin_content['yaml'] = plugin_yaml_url
        plugin_content['wagons'] = wagons_list
        json_content.append(plugin_content)
    return json_content


def check_plugins_json(plugin_name,
                       version,
                       plugins_json_content,
                       plugin_yaml_name):

    if plugin_yaml_name == 'v1':
        plugin_yaml_file_name = 'plugin.yaml'
    else:
        plugin_yaml_file_name = 'v2_plugin.yaml'
    wagons_list = plugins_json.get_wagons_list(
        plugin_name=plugin_name,
        plugin_version=version
    )
    plugin_yaml_url = s3.get_plugin_yaml_url(
        plugin_name=plugin_name,
        filename=plugin_yaml_file_name,
        plugin_version=version,
    )
    for plugin_content in plugins_json_content:
        if plugin_name != plugin_content['name']:
            continue
        else:
            try:
                assert version == plugin_content['version']
                assert plugin_yaml_url == plugin_content['link']
                assert plugin_yaml_url == plugin_content['yaml']
                assert wagons_list == plugin_content['wagons']
                return True
            except AssertionError:
                raise RuntimeError('Plugins JSON does not contain: '
                                   '{} {}'.format(plugin_name, version))
    return False
