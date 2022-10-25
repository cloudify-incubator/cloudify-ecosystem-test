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

from ecosystem_cicd_tools.new_cicd import actions
from ...ecosystem_tests_cli import (logger, ecosystem_tests)


WORKSPACE_DIR = 'workspace/build'
INCLUDE_SUFFIX = ['.wgn', '.wgn.md5']
INCLUDE_NAMES = ['plugin.yaml', 'v2_plugin.yaml']


@ecosystem_tests.command(name='upload-assets',
                         short_help='Upload assets to release.')
@ecosystem_tests.options.github_token
@ecosystem_tests.options.release
@ecosystem_tests.options.assets
@ecosystem_tests.options.repo
@ecosystem_tests.options.org
def upload_assets(assets,
                  repo,
                  github_token=None,
                  org=None,
                  release=None):

    assets = get_assets_dict(assets)

    if not assets:
        logger.logger.error('No assets found!')
        return

    kwargs = {
        'assets': assets,
        'release_name': release,
        'repository_name': repo
    }

    if org:
        kwargs['organization_name'] = org

    if github_token:
        kwargs['github_token'] = github_token

    if github_token:
        kwargs['github_token'] = github_token

    logger.logger.info(
        'Uploading these assets to the {} {} release: {}.'.format(
            repo, release, ', '.join(kwargs['assets'].keys())))

    actions.upload_assets_to_release(**kwargs)


def get_assets_dict(assets_tuple=None):
    asset_dict = {}
    assets_tuple = assets_tuple or get_assets_from_workspace()

    if not assets_tuple:
        return

    for pair in assets_tuple:
        try:
            k, v = pair.split('=')
        except ValueError:
            logger.logger.error('Invalid asset pair provided: {}. '
                                'Must be in format "label=path".')
            sys.exit(1)
        else:
            asset_dict[k] = v
    return asset_dict


def get_assets_from_workspace():
    assets_list = []
    if os.path.exists(WORKSPACE_DIR):
        for f in os.listdir(WORKSPACE_DIR):
            if list(filter(f.endswith, INCLUDE_SUFFIX)) or f in INCLUDE_NAMES:
                assets_list.append('{}={}'.format(
                    f, os.path.join(WORKSPACE_DIR, f)))
    return assets_list
