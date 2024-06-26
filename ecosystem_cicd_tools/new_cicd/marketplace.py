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

import json

import requests
import urllib.request
from packaging.version import parse as version_parse

from .logging import logger
from ..utils import get_json

URL_MARKETPLACE = "https://marketplace.cloudify.co"

URL = 'https://9t51ojrwrb.execute-api.eu-west-1.amazonaws.com/prod/' \
      'scrape-plugins-git-webhook'


def call_plugins_webhook(plugin_name, plugin_version, github_user):
    payload = {
        'plugin_name': plugin_name,
        'version': plugin_version,
        'creator': github_user,
    }
    logger.info('Calling marketplace webhook {}.'.format(payload))
    result = requests.post(
        URL,
        json=payload
    )
    if not result.ok:
        raise RuntimeError(
            'Failed to update marketplace with plugin release. '
            '{}'.format(result.text))


def get_plugin_id(plugin_name):
    logger.info('Getting plugin ID for name: {}'.format(plugin_name))
    url_plugin_id = 'https://marketplace.cloudify.co/plugins?name={}'.format(
        plugin_name)
    json_resp = get_json(url_plugin_id)
    logger.info('Got plugin ID response: {}'.format(json_resp))
    if 'items' in json_resp:
        if len(json_resp['items']) == 1:
            return json_resp['items'][0]['id']

def get_plugin_versions(plugin_id):
    logger.info('Getting plugin versions for ID: {}'.format(plugin_id))
    url_plugin_version = 'https://marketplace.cloudify.co/' \
                         'plugins/{}/versions?'.format(plugin_id)
    json_resp = get_json(url_plugin_version)
    logger.info('Got plugin version response: {}'.format(json_resp))
    if 'items' in json_resp:
        versions = [item['version'] for item in json_resp['items']]
        return sorted(versions, key=lambda x: version_parse(x))
    return []


def get_node_types_for_plugin_version(plugin_name, plugin_version):
    logger.info('Getting node types for {}:{}'.format(
        plugin_name, plugin_version))
    url = 'https://marketplace.cloudify.co/node-types?' \
          '&plugin_name={}' \
          '&plugin_version={}'.format(plugin_name, plugin_version)
    result = get_json(url)
    node_types = {}
    for item in result['items']:
        node_types[item['type']] = item
    return node_types


def list_versions(plugin_id):
    logger.info('Getting plugin versions for {}'.format(
        plugin_id))
    url = f'{URL_MARKETPLACE}/plugins/{plugin_id}/versions'
    json_resp = get_json_from_marketplace(url, True)
    if 'items' in json_resp:
        versions = [item['version'] for item in json_resp['items']]
        return sorted(versions, key=lambda x: version_parse(x))
    return []


def get_json_from_marketplace(url, log_response=False):
    logger.info('get_json_from_marketplace request {}.'.format(url))
    try:
        resp = urllib.request.urlopen(url)
    except urllib.error.HTTPError:
        return {}
    body = resp.read()
    if log_response:
        logger.info('get_json_from_marketplace response {}.'.format(body))
    result = json.loads(body)
    return result


def get_plugin_release_spec_from_marketplace(plugin_id, plugin_version):
    release_url = 'https://marketplace.cloudify.co/plugins/{}/{}'.format(
        plugin_id, plugin_version)
    return get_json_from_marketplace(release_url)


def get_assets(repository, version):
    logger.info('Getting Assets: {} {}'.format(repository, version))
    assets_list_marketplace = []
    plugin_id = get_plugin_id(repository.name)
    if not plugin_id:
        return assets_list_marketplace
    items = get_plugin_release_spec_from_marketplace(plugin_id, version)
    logger.info('Got assets: {}'.format(items))
    if not items:
        return items

    yaml_urls = items['yaml_urls']
    for yaml in yaml_urls:
        assets_list_marketplace.append(yaml['url'])

    wagon_urls = items['wagon_urls']
    for wagon in wagon_urls:
        assets_list_marketplace.append(wagon['url'])
    return assets_list_marketplace


def get_node_types_diff(plugin_id, old, new):
    """Get the node types diff between two versions of
    a plugin. The new_node_types dict will return node
    types that are not present in the old version.
    """
    node_types_diff = {}
    old_node_types = get_node_types_for_plugin_version(
        plugin_id, old)
    new_node_types = get_node_types_for_plugin_version(
        plugin_id, new)
    for key, value in new_node_types.items():
        if key not in old_node_types:
            node_types_diff[key] = value
    return node_types_diff


def delete_plugin_version(plugin_id, plugin_version):
    url = 'https://marketplace.cloudify.co/plugins/{}/{}'.format(
        plugin_id, plugin_version)
    return get_json(url=url, method='DELETE')


def delete_node_type(node_type_id):
    url = 'https://marketplace.cloudify.co/node-types/{}'.format(
        node_type_id)
    return get_json(url=url, method='DELETE')

