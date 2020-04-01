########
# Copyright (c) 2014-2020 Cloudify Platform Ltd. All rights reserved
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

import re
import logging
import requests
from os import environ
from tempfile import NamedTemporaryFile

from github import Github

logging.basicConfig(level=logging.INFO)
VERSION_STRING_RE = \
    r"version=\'[0-9]{1,}\.[0-9]{1,}\.[0-9]{1,}[\-]{0,1}[A-Za-z09]{0,5}\'"


def get_client(github_token=None):
    github_token = github_token or environ['RELEASE_BUILD_TOKEN']
    return Github(github_token)


def get_repository(client=None, org=None, repo_name=None):
    client = client or get_client()
    org = org or environ.get('CIRCLE_PROJECT_USERNAME')
    repo_name = repo_name or environ.get('CIRCLE_PROJECT_REPONAME')
    logging.info('Attempting to get repo {name} from org {org}.'.format(
        name=repo_name, org=org))
    return client.get_repo('{org}/{repo}'.format(org=org, repo=repo_name))


def get_commit(commit_id=None, repo=None):
    logging.info('Attempting to get commit {name}.'.format(name=commit_id))
    commit_id = commit_id or environ['CIRCLE_SHA1']
    repo = repo or get_repository()
    return repo.get_commit(commit_id)


def create_release(name, version, message, commit, repo=None):
    logging.info('Attempting to create new release {name}.'.format(name=name))
    repo = repo or get_repository()
    return repo.create_git_release(
        tag=version, name=name, message=message, target_commitish=commit)


def get_release(name, repo=None):
    logging.info('Attempting to get release {name} from repo {repo}.'.format(
        name=name, repo=repo.name))
    repo = repo or get_repository()
    release = repo.get_release(name)
    return release


def get_assets(release_name):
    logging.info('Attempting to get assets from release {name}'.format(
        name=release_name))
    release = get_release(release_name)
    return release.get_assets()


def upload_asset(release_name, asset_path, asset_label):
    logging.info('Attempting upload new asset '
                 '{path}:{label} to release {name}.'.format(
                     path=asset_path,
                     label=asset_label,
                     name=release_name))
    release = get_release(release_name)
    release.upload_asset(asset_path, asset_label)


def get_most_recent_release(version_family=None, repo=None):
    logging.info('Attempting to get most recent '
                 'release for version family {version} '
                 'from repo {repo}.'.format(
                     version=version_family,
                     repo=repo.name))
    repo = repo or get_repository()
    releases = repo.get_releases()
    for release in releases:
        if version_family and not release.title.startswith(version_family):
            continue
        return release


def update_release(name, message, prerelease=False, repo=None):
    logging.info('Attempting to update release {name} for repo {repo}.'.format(
        name=name, repo=repo.name))
    repo = repo or get_repository()
    release = repo.get_release(name)
    return release.update_release(
        name, message, draft=False, prerelease=prerelease)


def update_latest_release_resources(most_recent_release, name='latest'):
    logging.info('Attempting to update release {name} assets.'.format(
        name=most_recent_release.title))
    for asset in get_assets(name):
        asset.delete_asset()
    for asset in get_assets(most_recent_release):
        with open(NamedTemporaryFile().name, 'wb') as asset_file:
            r = requests.get(asset.browser_download_url, stream=True)
            asset_file.write(r.content)
            upload_asset(asset.name, asset_file)


def find_version(setup_py):
    with open(setup_py, 'r') as infile:
        versions = re.findall(VERSION_STRING_RE, infile.read())
    logging.info('versions {0} '.format(versions))
    if versions:
        v = versions[0].split('=')[1]
        if v.endswith(','):
            return v.split(',')[0]
        return v
    raise RuntimeError("Unable to find version string.")


