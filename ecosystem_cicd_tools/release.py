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

import re
import shutil
import logging
import requests
from os import path
from tempfile import NamedTemporaryFile

from .github_stuff import (
    get_assets,
    get_release,
    get_commit,
    upload_asset,
    create_release,
    delete_latest_tag_if_exists,
)
from .packaging import (
    package_blueprint,
)
from .validations import get_plugin_version

logging.basicConfig(level=logging.INFO)
VERSION_STRING_RE = r"version\s{0,1}=\s{0,1}\'[0-9]{1,}\.[0-9]{1,}\.[0-9]{1,}[\-]{0,1}[A-Za-z09]{0,5}\'" # noqa


def find_version(__version__py):
    version_string = None
    with open(__version__py, 'r') as infile:
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


def update_latest_release_resources(most_recent_release, name):
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


def plugin_release(plugin_name,
                   version=None,
                   plugin_release_name=None,
                   *_,
                   **__):

    version = version or get_plugin_version()
    plugin_release_name = plugin_release_name or "{0}-v{1}".format(
        plugin_name, version)
    version_release = get_release(version)
    commit = get_commit()
    if not version_release:
        version_release = create_release(
            version, version, plugin_release_name, commit)
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
                               plugins=None,
                               v2_plugin=False):
    # if we have release for this version we do not want update nothing
    if get_release(version):
        logging.warn('Found existing release for {0}. '
                     'No new build.'.format(version))
    else:
        logging.info('Starting create plugin release for {} {} {} {}'.format(
            plugin_name, version, plugin_release_name, plugins))
        # Create release for the new version if not exists
        version_release = plugin_release(
            plugin_name,
            version,
            plugin_release_name=plugin_release_name,
            workspace_files=plugins,
            v2_plugin=v2_plugin)
        latest_release = get_release("latest")
        if latest_release:
            # We have latest tag and release so we need to delete
            # them and recreate.
            logging.info('Deleting latest release '
                         'before creating again.')
            latest_release.delete_release()
            delete_latest_tag_if_exists()

        # create latest release
        logging.info(
            'Create release with name latest and tag latest')
        plugin_release(plugin_name, "latest",
                       plugin_release_name=version_release.body,
                       workspace_files=plugins,
                       v2_plugin=v2_plugin)


def blueprint_release_with_latest(blueprint_name,
                                  version=None,
                                  blueprint_release_name=None,
                                  blueprints=None):
    if get_release(version):
        logging.warn('Found existing release for {0}. '
                     'No new build.'.format(version))
    else:
        version_release = blueprint_release(
            blueprint_name, version, blueprint_release_name, blueprints)
        latest_release = get_release("latest")
        if latest_release:
            # We have latest tag and release so we need to delete
            # them and recreate.
            logging.info('Deleting latest release '
                         'before creating again.')
            latest_release.delete_release()
            delete_latest_tag_if_exists()

        logging.info(
            'Create release with name latest and tag latest')
        blueprint_release(
            blueprint_name, "latest", version_release.title, blueprints)
