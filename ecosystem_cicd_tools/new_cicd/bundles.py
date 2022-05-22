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
import yaml
import shutil
import tarfile
from tempfile import mkdtemp
from urllib.parse import urlparse

from . import s3
from .logging import logger

ARM64 = 'Centos AltArch'
CENTOS = 'Centos Core'
REDHAT = 'Redhat Maipo'
DISTROS = {
    CENTOS: 'centos-Core',
    REDHAT: 'redhat-Maipo',
    ARM64: 'centos-altarch'
}
DISTROS_TO_BUNDLE = [
    CENTOS,
    REDHAT,
    ARM64]
PLUGINS_TO_BUNDLE = [
    'vsphere',
    'terraform',
    'docker',
    'openstack',
    'openstackv3',
    'fabric',
    'gcp',
    'aws',
    'azure',
    'ansible',
    'kubernetes',
    'utilities',
    'starlingx',
    'helm'
]
PLUGINS_BUNDLE_NAME = 'cloudify-plugins-bundle'


def get_local_file_from_workspace(filename, workspace):
    if workspace and filename in os.listdir(workspace):
        return os.path.abspath(os.path.join(workspace, filename))


def find_plugin_yaml_in_workspace(filename,
                                  plugin_yaml,
                                  plugin_version,
                                  plugin_name,
                                  workspace):

    filename = get_local_file_from_workspace(filename, workspace)
    if filename:
        with open(filename, 'r') as outfile:
            data = yaml.safe_load(outfile)
            for n, p in data['plugins'].items():
                if plugin_version in p['package_version'] and \
                        plugin_name in p['package_name']:
                    logger.info('This is really happening!!!')
                    return filename
    return plugin_yaml


def find_wagon_in_workspace(
        plugin_name, plugin_version, distro, workspace=None):
    logger.info('Looking for wagon {} {} {} in {}.'.format(
        plugin_name, plugin_version, distro, workspace))
    plugin_name = plugin_name.replace('-', '_')
    if workspace:
        for filename in os.listdir(workspace):
            if plugin_name in filename and \
                    plugin_version in filename and \
                    distro in filename:
                return get_local_file_from_workspace(
                    filename,
                    workspace
                )


def get_metadata_mapping(data, workspace=None, plugin_yaml_name=None):
    mapping = {}
    logger.info('Get mapping from data: {}'.format(data))

    for plugin in data:
        logger.info('Creating mapping for {}'.format(plugin))
        if plugin['title'].lower() not in PLUGINS_TO_BUNDLE:
            continue
        plugin_yaml = find_plugin_yaml_in_workspace(
                plugin_yaml_name,
                plugin['link'],
                plugin['version'],
                plugin['name'],
                workspace)
        for wagon in plugin['wagons']:
            if wagon['name'] in DISTROS_TO_BUNDLE:
                wagon['url'] = find_wagon_in_workspace(
                    plugin['name'],
                    plugin['version'],
                    DISTROS.get(wagon['name']),
                    workspace
                ) or wagon['url']
                mapping[wagon['url']] = plugin_yaml
    logger.info('Returning mapping: {}'.format(mapping))
    return mapping, PLUGINS_BUNDLE_NAME


def package_archive(mappings,
                    archive_name=None,
                    directory=None,
                    workspace=None,
                    plugins_yaml_version=None):
    archive_name = archive_name or PLUGINS_BUNDLE_NAME
    if plugins_yaml_version and plugins_yaml_version != 'v1':
        archive_name += '-{}'.format(plugins_yaml_version)
    logger.info('Creating tar name {} at '
                '{} with mappings {}'.format(
                    archive_name,
                    directory,
                    mappings))

    tempdir = mkdtemp()
    create_metadata_file(mappings, tempdir, workspace)
    tar_path = os.path.join(directory, archive_name + '.tgz')
    tarfile_ = tarfile.open(tar_path, 'w:gz')
    try:
        tarfile_.add(tempdir, arcname=archive_name)
    finally:
        tarfile_.close()
        shutil.rmtree(tempdir, ignore_errors=True)
    return tar_path


def create_metadata_file(mappings, tempdir, workspace=None):

    metadata = {}

    for wagon_path, yaml_path in mappings.items():
        if not wagon_path or not yaml_path:
            logger.error('Unable to download {} {}'.format(wagon_path, yaml_path))
            continue
        wagon_path, yaml_path = download_or_find_wagon_and_yaml(
            wagon_path, yaml_path, tempdir, workspace)
        logger.info('Inserting '
                     'metadata[{wagon_path}] = {yaml_path}'.format(
                         wagon_path=wagon_path, yaml_path=yaml_path))
        metadata[wagon_path] = yaml_path

    with open(os.path.join(tempdir, 'METADATA'), 'w+') as f:
        logger.info(
            'create_plugin_bundle_archive writing metadata {m}'.format(
                m=metadata))
        yaml.dump(metadata, f)


def download_or_find_wagon_and_yaml(wagon_url,
                                    yaml_url,
                                    tempdir,
                                    workspace=None):

    logger.info('Downloading {} and {}'.format(wagon_url, yaml_url))
    plugin_root_dir = os.path.basename(wagon_url).rsplit('.', 1)[0]
    os.mkdir(os.path.join(tempdir, plugin_root_dir))
    downloaded_wagon_path = get_file_from_s3_or_workspace(
        wagon_url, plugin_root_dir, tempdir, workspace)
    downloaded_yaml_path = get_file_from_s3_or_workspace(
        yaml_url, plugin_root_dir, tempdir, workspace)
    return downloaded_wagon_path, downloaded_yaml_path


def get_file_from_s3_or_workspace(url, plugin_root_dir, tempdir, workspace):
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path[1:])
    destination_path = os.path.join(
        tempdir,
        plugin_root_dir,
        filename)
    if os.path.exists(url) and \
            os.path.basename(parsed.path[1:]) in os.listdir(workspace):
        shutil.copyfile(
            os.path.join(workspace, filename),
            destination_path)
    else:
        s3.download_from_s3(
            destination_path,
            parsed.path[1:])
    if not os.path.exists(destination_path):
        raise RuntimeError(
            'Unable to find file in s3 or in workspace: {} {} {}'.format(
                filename,
                os.path.basename(parsed.path[1:]),
                os.listdir(workspace)))
    return os.path.join(plugin_root_dir, os.path.basename(parsed.path[1:]))
