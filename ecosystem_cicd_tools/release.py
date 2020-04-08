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
import shutil
import logging
import requests
from os import environ, path, pardir
from tempfile import NamedTemporaryFile

from github import Github, Commit
from github.GithubException import UnknownObjectException, GithubException

from packaging import package_blueprint

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
    commit_id = commit_id or environ['CIRCLE_SHA1']
    logging.info('Attempting to get commit {name}.'.format(name=commit_id))
    repo = repo or get_repository()
    if isinstance(commit_id, Commit.Commit):
        commit_id = commit_id.commit
    if not commit_id:
        return
    try:
        return repo.get_commit(commit_id)
    except GithubException:
        return


def create_release(name, version, message, commit, repo=None):
    logging.info('Attempting to create new release {name}.'.format(name=name))
    repo = repo or get_repository()
    commit = get_commit(commit)
    return repo.create_git_release(
        tag=version, name=name, message=message, target_commitish=commit)


def get_release(name, repo=None):
    repo = repo or get_repository()
    logging.info('Attempting to get release {name} from repo {repo}.'.format(
        name=name, repo=repo.name))
    try:
        return repo.get_release(name)
    except UnknownObjectException:
        logging.info(
            'Failed to get release {name} from repo {repo}.'.format(
                name=name, repo=repo.name))
        return


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
    try:
        release.upload_asset(asset_path, asset_label)
    except GithubException:
        logging.info('Failed to upload new asset: '
                     '{path}:{label} to release {name}.'.format(
                         path=asset_path,
                         label=asset_label,
                         name=release_name))
        raise


def get_most_recent_release(version_family=None, repo=None):
    repo = repo or get_repository()
    logging.info('Attempting to get most recent '
                 'release for version family {version} '
                 'from repo {repo}.'.format(
                     version=version_family,
                     repo=repo.name))
    releases = repo.get_releases()
    for release in releases:
        if "latest" in release.title:
            continue
        if version_family and not release.title.startswith(version_family):
            continue
        return release


def update_release(name, message, commit, prerelease=False, repo=None):
    repo = repo or get_repository()
    logging.info(
        'Attempting to update release {name} '
        'for repo {repo} {message}.'.format(
            name=name, repo=repo.name, message=message))
    release = repo.get_release(name)
    commit = get_commit(commit)
    return release.update_release(
        name, message, draft=False, prerelease=prerelease,
        target_commitish=commit)


def update_latest_release_resources(most_recent_release, name='latest'):
    logging.info('Attempting to update release {name} assets.'.format(
        name=most_recent_release.title))
    for asset in get_assets(name):
        asset.delete_asset()
    for asset in get_assets(most_recent_release.title):
        tmp = NamedTemporaryFile(delete=False)
        with open(tmp.name, 'wb') as asset_file:
            r = requests.get(asset.browser_download_url, stream=True)
            asset_file.write(r.content)
        shutil.move(tmp.name, asset.name)
        upload_asset(name, asset.name, asset.label or asset.name)


def find_version(setup_py):
    with open(setup_py, 'r') as infile:
        version_string = re.findall(VERSION_STRING_RE, infile.read())
    if version_string:
        version = version_string[0].split('=')[1]
        logging.info('Found version {0}.'.format(version))
        if version.endswith(','):
            version = version.split(',')[0]
        if version.startswith("'") and version.endswith("'"):
            version = version[1:-1]
        return version
    raise RuntimeError("Unable to find version string.")


def get_plugin_version():
    setup_py = path.join(
        path.abspath(path.join(path.dirname(__file__), pardir)),
        'setup.py')
    return find_version(setup_py)


def plugin_release(plugin_name,
                   version=None,
                   plugin_release_name=None,
                   plugins=None):

    # plugins = plugins or {}
    version = version or get_plugin_version()
    plugin_release_name = plugin_release_name or "{0}-v{1}".format(
        plugin_name, version)
    version_release = get_release(version)
    commit = get_commit()
    if not version_release:
        version_release = create_release(
            version, version, plugin_release_name,
            commit)
    # TODO: ADD Plugin Packaging and Upload.
    return version_release


def blueprint_release(blueprint_name,
                      version,
                      blueprint_release_name=None,
                      blueprints=None):

    blueprints = blueprints or {}
    blueprint_release_name = blueprint_release_name or "{0}-v{1}".format(
        blueprint_name, version)
    version_release = get_release(version)
    commit = get_commit()
    if not version_release:
        version_release = create_release(
            version, version, blueprint_release_name,
            commit)
    for blueprint_id, blueprint_path in blueprints.items():
        blueprint_archive = package_blueprint(blueprint_id, blueprint_path)
        file_wo_ext, ext = path.splitext(blueprint_archive)
        new_archive_name = path.basename(
            '{file_wo_ext}-{version}{ext}'.format(
                file_wo_ext=file_wo_ext, version=version, ext=ext))
        version_release.upload_asset(
            blueprint_archive,
            new_archive_name,
            'application/zip')
    return version_release


def plugin_release_with_latest(plugin_name,
                               version=None,
                               plugin_release_name=None,
                               plugins=None):

    plugin_release_name = plugin_release_name or "{0}-v{1}".format(
        plugin_name, version)
    version_release = plugin_release(
        plugin_name, version, plugin_release_name, plugins)
    if not get_release("latest"):
        create_release(
            "latest", "latest", plugin_release_name,
            version_release.target_commitish)
    else:

        update_release(
            "latest",
            plugin_release_name,
            commit=version_release.target_commitish,
        )
    latest_release = get_most_recent_release()
    update_latest_release_resources(latest_release)


def blueprint_release_with_latest(plugin_name,
                                  version=None,
                                  blueprint_release_name=None,
                                  blueprints=None):

    version_release = blueprint_release(
        plugin_name, version, blueprint_release_name, blueprints)
    if not get_release("latest"):
        create_release(
            "latest", "latest", blueprint_release_name,
            version_release.target_commitish)
    else:
        update_release(
            "latest",
            blueprint_release_name,
            commit=version_release.target_commitish,
        )
    latest_release = get_most_recent_release()
    update_latest_release_resources(latest_release)
