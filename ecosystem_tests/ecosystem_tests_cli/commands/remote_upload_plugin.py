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
import sys
import shutil
import urllib.request
from tempfile import mkdtemp

from ecosystem_cicd_tools.new_cicd.marketplace import (
    get_plugin_id,
    get_plugin_versions,
    get_plugin_release_spec_from_marketplace)

from ecosystem_tests.nerdl.api import upload_plugin
from ecosystem_tests.ecosystem_tests_cli import (
    logger,
    decorators,
    ecosystem_tests
)
from ecosystem_tests.ecosystem_tests_cli.commands.upload_plugin import (
    get_spec_item,
    get_latest_version,
    validate_wagon_type,
    VALID_WAGON_DISTRO_NAMES,
)


@ecosystem_tests.command(name='remote-upload-plugin',
                         short_help='Upload plugins.')
@decorators.prepare_test_env
@ecosystem_tests.options.plugin_name
@ecosystem_tests.options.plugin_version
@ecosystem_tests.options.wagon_type
@ecosystem_tests.options.cloudify_token
@ecosystem_tests.options.cloudify_tenant
@ecosystem_tests.options.cloudify_hostname
def remote_upload_plugin(plugin_name,
                         plugin_version,
                         wagon_type,
                         cloudify_token,
                         cloudify_tenant,
                         cloudify_hostname):
    """
    Upload wagon and yamls to Cfy Manager.
    """

    wagon_type, repo = validate_wagon_type(wagon_type, plugin_name)

    plugin_id = get_plugin_id(repo)
    plugin_version = plugin_version or get_latest_version(
        plugin_id, repo)
    spec = get_plugin_release_spec_from_marketplace(
        plugin_id, plugin_version)
    logger.logger.info('We got this spec: {}'.format(spec))
    yaml_url_dict = get_spec_item(
        spec['yaml_urls'], 'dsl_version', 'cloudify_dsl_1_5')
    wagon_url_dict = get_spec_item(
        spec['wagon_urls'], 'release', wagon_type)
    if not yaml_url_dict['url'] or not wagon_url_dict['url']:
        logger.logger.error(
            'Unable to find wagon or yaml for {} {} in {} {}'.format(
                repo, plugin_version, yaml_url_dict, wagon_url_dict))
        sys.exit(1)
    download_write_upload(wagon_url_dict['url'], yaml_url_dict['url'])


def download_write_upload(wagon_url, yaml_url):
    tempdir = mkdtemp()
    wagon_path = os.path.join(tempdir, os.path.basename(wagon_url))
    yaml_path = os.path.join(tempdir, os.path.basename(yaml_url))
    download_file(wagon_url, wagon_path)
    download_file(yaml_url, yaml_path)
    upload_plugin(wagon_path, yaml_path)


def download_file(source, target):
    try:
        logger.logger.info('Downloading {} to {}'.format(source, target))
        urllib.request.urlretrieve(source, target)
    except Exception:
        shutil.rmtree(os.path.dirname(target))
        logger.logger.error('Failed to download {}'.format(source))
        sys.exit(1)
