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
import requests
import tempfile

from urllib.parse import urlparse

from click import option
from github import (GithubException, UnknownObjectException)

from ecosystem_cicd_tools.new_cicd import github
from ecosystem_cicd_tools.utils import download_file
from ecosystem_tests.ecosystem_tests_cli.logger import logger
from ecosystem_tests.ecosystem_tests_cli import ecosystem_tests


@ecosystem_tests.command(
    name='copy-releases',
    short_help='Copies tags, releases, and assets from one fork to another.')
@option('-f', '--from-repo')
@option('-t', '--to-repo')
def copy_releases(from_repo, to_repo):
    # logger.info(f'We have from {from_repo} to {to_repo}.')
    _, from_org, from_repo_name = urlparse(from_repo).path.split('/')
    _, to_org, to_repo_name = urlparse(to_repo).path.split('/')
    for old_release in get_all_releases(
            organization_name=from_org,
            repository_name=from_repo_name):
        logger.info(f'We have release {old_release.title} '
                    f'with tag {old_release.tag_name}.')
        if not check_if_repo_has_release(
                old_release.title,
                organization_name=to_org,
                repository_name=to_repo_name):
            logger.error('The target repo does not have '
                         f'the release {old_release.title}.')
            try:
                new_release = github.create_release(
                    old_release.tag_name,
                    old_release.title,
                    f'Re-releasing {old_release.title}.',
                    commit=old_release.target_commitish,
                    organization_name=to_org,
                    repository_name=to_repo_name
                )
            except GithubException as e:
                logger.error(f'Skipping {old_release.tag_name}...{str(e)}.')
                continue
            copy_assets(old_release, new_release)


@github.with_github_client
def get_all_releases(repository=None, **kwargs):
    return repository.get_releases()


@github.with_github_client
def check_if_repo_has_release(release_title, repository=None, **_):
    try:
        repository.get_release(release_title)
    except UnknownObjectException as e:
        return False
    return True


def copy_assets(from_release, to_release):
    logger.info('Uploading assets...')
    assets = from_release.get_assets()
    logger.info(f'We have assets {assets}.')
    for asset in assets:
        logger.info(f'We have asset {asset}')
        copy_asset(asset.url, asset.browser_download_url, to_release)


def copy_asset(url, download_url, to_release):
    headers = {
        'Authorization': 'token ' + os.environ['RELEASE_BUILD_TOKEN'],
        'Accept': 'application/octet-stream'
    }
    with tempfile.TemporaryDirectory() as download_dir:
        asset_label = urlparse(download_url).path.split('/')[-1]
        asset_path = os.path.join(download_dir, asset_label)
        logger.info(f'We are going to download {url} '
                    f'and upload {asset_path} to {to_release}.')
        response = requests.get(
            url, stream=True, headers=headers, allow_redirects=True)
        with open(asset_path, 'wb') as f:
            for chunk in response.iter_content(1024*1024):
                f.write(chunk)
        result = to_release.upload_asset(asset_path, asset_label)
        if not result.state == 'uploaded':
            raise Exception(f'Failed...{result}')
