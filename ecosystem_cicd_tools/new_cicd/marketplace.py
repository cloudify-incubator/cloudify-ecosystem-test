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
from .logging import logger
from packaging.version import parse as version_parse

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
    url_plugin_id = 'https://marketplace.cloudify.co/plugins?name={}'.format(
        plugin_name)
    json_resp = get_json(url_plugin_id)
    if 'items' in json_resp:
        if len(json_resp['items']) == 1:
            return json_resp['items'][0]['id']


def get_plugin_versions(plugin_id):
    url_plugin_version = 'https://marketplace.cloudify.co/' \
                         'plugins/{}/versions?'.format(plugin_id)
    json_resp = get_json(url_plugin_version)
    if 'items' in json_resp:
        versions = [item['version'] for item in json_resp['items']]
        return sorted(versions, key=lambda x: version_parse(x))
    return []


def get_node_types_for_plugin_version(plugin_name, plugin_version):
    url = 'https://marketplace.cloudify.co/node-types?' \
          '&plugin_name={}' \
          '&plugin_version={}'.format(plugin_name, plugin_version)
    result = get_json(url)
    node_types = {}
    for item in result['items']:
        node_types[item['type']] = item
    return node_types


def get_json(url):
    try:
        resp = urllib.request.urlopen(url)
    except urllib.error.HTTPError:
        return {}
    body = resp.read()
    return json.loads(body)


def list_versions(plugin_id):
    return requests.get(
        f'{URL_MARKETPLACE}/plugins/{plugin_id}/versions')[0]
