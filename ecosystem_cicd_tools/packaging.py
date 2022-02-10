########
# Copyright (c) 2018--2022 Cloudify Platform Ltd. All rights reserved
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
import re
import json
import yaml
import base64
import shutil
import logging
import tarfile
import zipfile
import mimetypes
from copy import deepcopy
from pprint import pformat
from contextlib import contextmanager
from tempfile import NamedTemporaryFile, mkdtemp

import boto3
from wagon import show
from botocore.exceptions import ClientError

from . import (
    V2_YAML,
    LABELLED_PLUGINS,
    BLUEPRINT_LABEL_TEMPLATE,
    DEPLOYMENT_LABEL_TEMPLATE)

logging.basicConfig(level=logging.INFO)
BUCKET_NAME = 'cloudify-release-eu'
BUCKET_FOLDER = 'cloudify/wagons'
PLUGINS_JSON_PATH = os.path.join(BUCKET_FOLDER, 'plugins.json')
EXAMPLES_JSON = 'resources/examples.json'
PLUGINS_JSON = 'resources/plugins.json'
PLUGINS_TO_BUNDLE\
    = [
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

REDHAT = 'Redhat Maipo'
CENTOS = 'Centos Core'
ARM64 = 'Centos AltArch'
DISTROS_TO_BUNDLE = [CENTOS, REDHAT, ARM64]
PLUGINS_BUNDLE_NAME = 'cloudify-plugins-bundle'
ASSET_URL_DOMAIN = 'http://repository.cloudifysource.org'
ASSET_URL_TEMPLATE = ASSET_URL_DOMAIN + '/{0}/{1}/{2}/{3}'
ASSET_FILE_URL_TEMPLATE = ASSET_URL_TEMPLATE + '/{4}'

PLUGIN_NAMING_CONVENTION = pattern = 'cloudify\-(.*?)\-plugin'


@contextmanager
def aws(**_):
    access_key = os.environ['aws_access_key_id'].strip('\n')
    access_secret = os.environ['aws_secret_access_key'].strip('\n')
    os.environ['aws_access_key_id'.upper()] = str(base64.b64decode(
        access_key), 'utf-8').strip('\n')
    os.environ['aws_secret_access_key'.upper()] = str(base64.b64decode(
        access_secret), 'utf-8').strip('\n')
    os.environ['AWS_DEFAULT_REGION'] = 'eu-west-1'
    yield


def list_bucket_objects(bucket_name=None, path=None):
    with aws():
        bucket_name = bucket_name or BUCKET_NAME
        s3 = boto3.client('s3')
        return s3.list_objects(Bucket=bucket_name, Prefix=path)


def upload_to_s3(local_path,
                 remote_path,
                 bucket_name=None,
                 content_type=None):
    """
    Upload a local file to s3.
    :param local_path: The local path to the file that we want to upload.
    :param remote_path: The s3 key.
    :param bucket_name: The s3 bucket.
    :param content_type: By default s3 upload_file adds
        content-type octet-stream. This is not universal, for example JSON
        files need to be application/json.
    :return:
    """

    with aws():
        bucket_name = bucket_name or BUCKET_NAME
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        logging.info('Uploading {local_path} to s3://{remote_path}.'.format(
            local_path=local_path, remote_path=remote_path))
        extra_args = {'ACL': 'public-read'}
        if content_type:
            extra_args.update({'ContentType': content_type})
        bucket.upload_file(local_path,
                           remote_path,
                           ExtraArgs=extra_args)
        object_acl = s3.ObjectAcl(bucket_name, remote_path)
        logging.info('{object_acl} grants: {grants}.'.format(
            object_acl=object_acl, grants=object_acl.grants))
        object_acl.put(ACL='public-read')
        logging.info('{object_acl} grants: {grants}.'.format(
            object_acl=object_acl, grants=object_acl.grants))


def download_from_s3(remote_path,
                     local_path=None,
                     bucket_name=None,
                     s3_object=None):
    """
    Download a file from s3.
    :param remote_path: The s3 key.
    :param local_path: The destination path.
    :param bucket_name: The s3 bucket.
    :param s3_object: Optional if you have created the boto3 s3 object alredy.
    :return:
    """

    logging.info('download_from_s3 {s3_object} {remote_path} to {local_path}.'
                 .format(s3_object=s3_object,
                         remote_path=remote_path,
                         local_path=local_path))

    with aws():
        if not local_path:
            archive_temp = NamedTemporaryFile(delete=False)
            local_path = archive_temp.name
        if not s3_object:
            bucket_name = bucket_name or BUCKET_NAME
            s3 = boto3.resource('s3')
            s3_object = s3.Object(bucket_name, remote_path)
        logging.info('Downloading {s3_object} to {local_path}.'.format(
            s3_object=s3_object, local_path=local_path))
        if not os.path.exists(os.path.dirname(local_path)):
            os.makedirs(os.path.dirname(local_path))
        logging.info('Starting download')
        s3_object.download_file(
            local_path,
            Config=boto3.s3.transfer.TransferConfig(use_threads=False))
        logging.info('Finished download')
        return local_path


def read_json_file(file_path):
    """
    Read a JSON file.
    :param file_path: the local path to the JSON file.
    :return: a JSON object - usually a list or a dict.
    """

    with open(file_path, 'r') as outfile:
        return json.load(outfile)


def write_json_and_upload_to_s3(content, remote_path, bucket_name):
    """

    :param content: Usually a list or a dict.
    :param remote_path: the s3 key.
    :param bucket_name: The s3 bucket.
    :return:
    """

    logging.info('Writing new content to s3://{remote_path}.'.format(
        remote_path=remote_path))
    logging.info('The new data is {content}'.format(content=content))
    json_temp = NamedTemporaryFile(suffix='.json', delete=False)
    with open(json_temp.name, 'w') as outfile:
        json.dump(content, outfile, ensure_ascii=False, indent=4)
    mt, _ = mimetypes.guess_type(json_temp.name)
    upload_to_s3(json_temp.name, remote_path, bucket_name, content_type=mt)


def write_json(content):
    logging.info('The new data is {content}'.format(content=content))
    archive_temp = NamedTemporaryFile(delete=False)
    with open(archive_temp.name, 'w') as outfile:
        json.dump(content, outfile, ensure_ascii=False, indent=4)
    return archive_temp.name


def get_plugins_json(remote_path):
    """
    Get the plugins list.
    :param remote_path: The s3 key where plugins.json sits.
    :return: the list of plugins from plugins.json
    """

    local_path = download_from_s3(remote_path, PLUGINS_JSON)
    return read_json_file(local_path)


def plugin_dicts(plugin_dict, assets, wagons_list=None):

    logging.info('Plugin dict: {}'.format(plugin_dict))

    wagons_list = wagons_list or []

    new_wagon_list = []

    centos_core_li = {
        'name': CENTOS
    }
    centos_aarch_li = {
        'name': ARM64
    }
    redhat_maipo_li = {
        'name': REDHAT
    }

    for asset in assets:
        # Replace the old asset paths with new ones.
        if asset.endswith('.yaml'):
            plugin_dict['link'] = asset
        elif 'centos-altarch' in asset:
            if asset.endswith('md5'):
                centos_aarch_li['md5url'] = asset
            else:
                centos_aarch_li['url'] = asset
        elif 'centos-Core' in asset:
            if asset.endswith('md5'):
                centos_core_li['md5url'] = asset
            else:
                centos_core_li['url'] = asset
        elif 'redhat-Maipo' in asset:
            if asset.endswith('md5'):
                redhat_maipo_li['md5url'] = asset
            else:
                redhat_maipo_li['url'] = asset

    for li in [centos_core_li, centos_aarch_li, redhat_maipo_li]:
        if 'url' not in li or 'md5url' not in li:
            continue
        elif plugin_dict['version'] not in li['url'] or \
                plugin_dict['version'] not in li['md5url']:
            continue
        for wagon_item in wagons_list:
            if wagon_item['name'] == li['name']:
                wagons_list.remove(wagon_item)
        new_wagon_list.append(li)

    new_wagon_list.extend(wagons_list)
    plugin_dict['wagons'] = sorted(
        new_wagon_list, key=lambda d: d['name'])


def update_assets_in_plugin_dict(plugin_dict,
                                 assets,
                                 plugin_version=None,
                                 v2_plugin=False):
    """
    Update the YAML and Wagon URLs in the plugins dict with new assets.
    :param plugin_dict: The dict item for this plugin in plugins.json list.
    :param assets: A list of URLs of plugin YAMLs and wagons.
    :param plugin_version: New plugin version string
    :param v2_plugin: Add labels?
    :return: None, the object is edited in place.
    """

    logging.info('Updating plugin JSON with assets {assets}'.format(
        assets=assets))
    logging.info('Updating plugin JSON with this version {version}'.format(
        version=plugin_version))
    plugin_yaml = plugin_dict['link']
    plugin_yaml_v2 = plugin_yaml.replace(
        plugin_yaml.split('plugin.yaml')[1], V2_YAML)
    if plugin_version:
        plugin_yaml = plugin_yaml.replace(
            plugin_yaml.split('/')[-2], plugin_version)
        plugin_yaml_v2 = plugin_yaml.replace(
            plugin_yaml_v2.split('/')[-2], plugin_version)
        plugin_dict['version'] = plugin_version
    plugin_dict['link'] = plugin_yaml
    if v2_plugin:
        plugin_dict['yaml'] = plugin_yaml_v2
    wagons_list_copy = sorted(
        deepcopy(plugin_dict['wagons']),
        key=lambda d: d['name'])
    plugin_dicts(plugin_dict, assets, wagons_list_copy)


def get_plugin_new_json(remote_path,
                        plugin_name,
                        plugin_version,
                        assets,
                        plugins_list=None,
                        v2_plugin=False):
    """
    Download the plugins.json from s3. Update the plugin dict with new assets.
    :param remote_path: the key in s3 of the plugins.json
    :param plugin_name: the plugin name
    :param plugin_version: the plugin version
    :param assets: new resources, such as plugin YAML, wagon, md5, etc.
    :param plugins_list: Override the need for remote if you already have it.
    :param v2_plugin: Labels?
    :return: the new plugins list.
    """

    logging.info('Fn get_plugin_new_json {p} {n} {v} {a} {ll}'.format(
        p=remote_path,
        n=plugin_name,
        v=plugin_version,
        a=assets,
        ll=plugins_list))
    update_version = not plugins_list
    plugins_list = plugins_list or get_plugins_json(remote_path)
    # Plugins list is a list of dictionaries. Each plugin/version is one dict.
    for pd in plugins_list:
        logging.info('Checking {plugin_name} {plugin_version}'.format(
            plugin_name=plugin_name,
            plugin_version=plugin_version))
        logging.info('against plugin {pn} {pv}'.format(
            pn=pd['name'],
            pv=pd['version']))
        if plugin_name == pd['name']:
            # Double check that we are editing the same version.
            # For example, we don't want to update
            # Openstack 3.2.0 with Openstack 2.14.20.
            logging.info(
                'Checking if we have a major version '
                'update {vers} vs {pdv}.'.format(vers=plugin_version,
                                                 pdv=pd['version']))
            if plugin_version.split('.')[0] == pd['version'].split('.')[0]:
                if update_version:
                    update_assets_in_plugin_dict(
                        pd, assets, plugin_version, v2_plugin)
                else:
                    update_assets_in_plugin_dict(
                        pd, assets, v2_plugin=v2_plugin)
    logging.info('New plugin list: {pl}'.format(pl=plugins_list))
    return plugins_list


def update_plugins_json(plugin_name, plugin_version, assets, v2_plugin=False):
    """
    Update the plugins JSON in s3 with the new URLs for assets.
    :param plugin_name: The plugin name
    :param plugin_version: The plugin version.
    :param assets: A list of local paths that will be changed to new URLs.
    :param v2_plugin: labels?
    :return:
    """

    logging.info(
        'Updating {plugin_name} {plugin_version} in plugin JSON'.format(
            plugin_name=plugin_name,
            plugin_version=plugin_version))
    # Convert the local paths to remote URLs in s3.
    # For example /tmp/tmp000000/plugin.yaml
    # will become: cloudify/wagons/{plugin_name}/{plugin_version}/plugin.yaml
    assets = [ASSET_URL_TEMPLATE.format(
        BUCKET_FOLDER,
        plugin_name,
        plugin_version,
        os.path.basename(asset)) for asset in assets]
    plugin_dict = get_plugin_new_json(
        PLUGINS_JSON_PATH,
        plugin_name,
        plugin_version,
        assets,
        v2_plugin=v2_plugin)
    write_json_and_upload_to_s3(plugin_dict, PLUGINS_JSON_PATH, BUCKET_NAME)


def get_list_of_updated_assets(plugins_json=None):
    plugins_json = plugins_json or get_plugins_json(PLUGINS_JSON_PATH)
    for plugin in plugins_json:
        list_of_updated_assets = []
        base_path = '/'.join(plugin['link'].split('/')[3:7])
        for s3_path in list_bucket_objects(path=base_path)['Contents']:
            cloudify_path = ASSET_FILE_URL_TEMPLATE.format(
                *s3_path['Key'].split('/'))
            list_of_updated_assets.append(cloudify_path)
        plugin_dicts(plugin_dict=plugin, assets=list_of_updated_assets)


def upload_plugin_asset_to_s3(local_path, plugin_name, plugin_version):
    """

    :param local_path: The path to the asset, such as 'dir/my-wagon.wgn.md5'.
    :param plugin_name: The plugin name, such as 'cloudify-foo-plugin'.
    :param plugin_version: The plugin version, such as '1.0.0'.
    :return:
    """
    # We want to create a string in the format:
    # cloudify/wagons/cloudify-foo-plugin/1.0.0/my-wagon.wgn.md5
    bucket_path = os.path.join(BUCKET_FOLDER,
                               plugin_name,
                               plugin_version,
                               os.path.basename(local_path))
    logging.info('Uploading {plugin_name} {plugin_version} to S3.'.format(
        plugin_name=plugin_name, plugin_version=plugin_version))
    upload_to_s3(local_path, bucket_path)


def find_wagon_local_path(docker_path, workspace_path=None):
    """

    :param docker_path:
    :return:
    """
    logging.info('Finding wagon {} in {}'.format(docker_path, workspace_path))
    for f in get_workspace_files(workspace_path=workspace_path):
        logging.info(
            'Checking \n{} against \n{}'.format(os.path.basename(docker_path), f))
        if os.path.basename(docker_path) in f and f.endswith('.wgn'):
            return f
    return docker_path


def get_file_from_s3_or_locally(source, destination, v2_bundle=False):
    logging.info('Get source {0}'.format(source))
    try:
        source = source.split(ASSET_URL_DOMAIN + '/')[1]
    except IndexError:
        logging.info('Source is not URL, source {0}'.format(source))
    local_yaml = os.path.join(os.getcwd(), 'plugin.yaml')
    if source.endswith('plugin.yaml') and os.path.exists(local_yaml):
        shutil.copyfile(local_yaml, destination)
    else:
        try:
            download_from_s3(
                source,
                destination)
        except ClientError:
            if source.endswith('.wgn'):
                source = find_wagon_local_path(source)
            else:
                raise
            if source:
                shutil.copyfile(source, destination)
    if source.endswith('plugin.yaml'):
        update_yaml_for_v2_bundle(destination, v2_bundle)


def create_plugin_metadata(wgn_path, yaml_path, tempdir, v2_bundle=False):
    """
    Update the metadata with the path relative to zip root.
    :param wgn_path: A path to a local wagon file.
    :param yaml_path: A path to a local plugin YAML file.
    :param tempdir: The tempdir we're working with.
    :param v2_bundle: update plugin YAML.
    :return:
    """

    logging.info('Downloading {wgn_path} and {yaml_path}'.format(
        wgn_path=wgn_path, yaml_path=yaml_path))
    plugin_root_dir = os.path.basename(wgn_path).rsplit('.', 1)[0]
    try:
        os.mkdir(os.path.join(tempdir, plugin_root_dir))
    except OSError as e:
        logging.info(e)
    dest_wgn_path = os.path.join(plugin_root_dir,
                                 os.path.basename(wgn_path))
    dest_yaml_path = os.path.join(plugin_root_dir,
                                  os.path.basename(yaml_path))
    # Some plugins we need to download from s3 and some we want to package
    # using locally built files.
    get_file_from_s3_or_locally(wgn_path,
                                os.path.join(tempdir, dest_wgn_path))
    get_file_from_s3_or_locally(
        yaml_path,
        os.path.join(tempdir, dest_yaml_path),
        v2_bundle)
    return dest_wgn_path, dest_yaml_path


def create_plugin_bundle_archive(mappings,
                                 tar_name,
                                 destination,
                                 v2_bundle=False):
    """

    :param mappings: A special metadata data structure.
    :param tar_name: The name of the tar file.
    :param destination: The destination where we save it.
    :param v2_bundle: Whether to v2-ize the bundle.
    :return:
    """

    if v2_bundle:
        tar_name = tar_name + '-v2'

    logging.info('Creating tar name {tar_name} at '
                 '{destination} with mappings {mappings}'.format(
                     tar_name=tar_name,
                     destination=destination,
                     mappings=pformat(mappings)))

    tempdir = mkdtemp()
    metadata = {}

    for key, value in mappings.items():
        # If we have a plugin we want to use for a local path,
        # then we don't want to download it.
        wagon_path, yaml_path = create_plugin_metadata(
            key, value, tempdir, v2_bundle)
        logging.info('Inserting '
                     'metadata[{wagon_path}] = {yaml_path}'.format(
                         wagon_path=wagon_path, yaml_path=yaml_path))
        metadata[wagon_path] = yaml_path
    with open(os.path.join(tempdir, 'METADATA'), 'w+') as f:
        logging.info(
            'create_plugin_bundle_archive writing metadata {m}'.format(
                m=metadata))
        yaml.dump(metadata, f)
    tar_path = os.path.join(destination, tar_name + '.tgz')
    tarfile_ = tarfile.open(tar_path, 'w:gz')
    try:
        tarfile_.add(tempdir, arcname=tar_name)
    finally:
        tarfile_.close()
        shutil.rmtree(tempdir, ignore_errors=True)
    return tar_path


def update_yaml_for_v2_bundle(yaml_path, v2_plugin):
    if not os.path.exists(yaml_path):
        raise RuntimeError('Path does not exist: {}'.format(yaml_path))
    if not v2_plugin:
        return
    with open(yaml_path, "r") as stream:
        current_yaml = yaml.safe_load(stream)

        label_value = re.search(
            pattern,
            next(iter(current_yaml['plugins'].values()))['package_name']
        ).group(1)

    if label_value not in LABELLED_PLUGINS:
        return

    with open(yaml_path, 'a') as f:
        f.write(BLUEPRINT_LABEL_TEMPLATE.format(plugin_name=label_value))
        f.write(DEPLOYMENT_LABEL_TEMPLATE.format(plugin_name=label_value))


def configure_bundle_archive(plugins_json=None):
    """
    create the metadata data structure that is used to describe the contents
    of the bundle
    :param plugins_json: an alternative plugins_json
    :return:
    """
    plugins_json = plugins_json or get_plugins_json(PLUGINS_JSON_PATH)
    mapping = {}
    build_directory = mkdtemp()
    logging.info('Creating bundle with plugins {plugins}'.format(
        plugins=pformat(plugins_json)))

    for plugin in plugins_json:
        if plugin['title'].lower() in PLUGINS_TO_BUNDLE:
            plugin_yaml = plugin['link']
            centos_wagon = None
            for wagon in plugin['wagons']:
                if wagon['name'] in DISTROS_TO_BUNDLE:
                    mapping[wagon['url']] = plugin_yaml
                if wagon['name'] == CENTOS:
                    centos_wagon = wagon
            if centos_wagon:
                aarch_name = centos_wagon['url'].replace(
                    'centos-Core', 'centos-altarch')
                aarch_name = aarch_name.replace(
                    'x86_64', 'aarch64')
                aarch_name = aarch_name.replace(
                    'py27.py36', 'py36')
                mapping[aarch_name] = plugin_yaml

    logging.info('Configure bundle mapping: {mapping}'.format(mapping=mapping))
    return mapping, PLUGINS_BUNDLE_NAME, build_directory


def build_plugins_bundle(plugins_json=None, v2_bundle=False):
    # Deprecate this by looking in other repos.
    return create_plugin_bundle_archive(
        *configure_bundle_archive(plugins_json), v2_bundle=v2_bundle)


def update_plugins_bundle(bundle_archive=None, plugins_json=None):
    bundle_archive = bundle_archive or build_plugins_bundle(plugins_json)
    upload_to_s3(bundle_archive,
                 os.path.join(BUCKET_FOLDER, os.path.basename(bundle_archive)))
    logging.info('update_plugins_bundle report_tar_contents ...')
    report_tar_contents(bundle_archive)


def build_plugins_bundle_with_workspace(workspace_path=None, v2_bundle=False):
    """
    Get wagons and md5 files from the workspace and replace the old values in
    plugins.json with the new values. This is only used to build the
    bundle, it's not what's published.
    :return:
    """
    plugins_json = {}
    # Get all the workspace files
    files = [
        f for f in get_workspace_files(workspace_path=workspace_path)
        if f.endswith('wgn') or f.endswith('md5')
    ]
    files.sort()
    for i in range(0, len(files), 2):
        if files[i].endswith('.wgn'):
            plugin = (files[i], files[i+1])
            wagon_metadata = show(find_wagon_local_path(plugin[0]))
            logging.info('Build plugins bundle {md}.'.format(
                md=wagon_metadata))
            plugin_name = wagon_metadata["package_name"]
            plugin_version = wagon_metadata["package_version"]
            plugins_json = get_plugin_new_json(
                PLUGINS_JSON_PATH,
                plugin_name,
                plugin_version,
                plugin,
                plugins_json,
                v2_bundle
            )
            logging.info('Build plugins json {i} {out}'.format(
                i=i, out=plugins_json))
        else:
            try:
                os.remove(files[i])
            except OSError:
                raise Exception(
                    'Illegal files list {files}'.format(files=files[i]))
    copy_plugins_json_to_workspace(write_json(plugins_json))
    bundle_path = build_plugins_bundle(plugins_json, v2_bundle)
    workspace_path = os.path.join(
        os.path.abspath('workspace'),
        'build',
        os.path.basename(bundle_path))

    shutil.copyfile(bundle_path, workspace_path)
    logging.info('build_plugins_bundle_with_workspace fn report_tar_contents.')
    report_tar_contents(workspace_path)


def report_tar_contents(path):
    loc = mkdtemp()
    tar = tarfile.open(path)
    tar.extractall(path=loc)
    tar.close()
    files = os.listdir(loc)
    logging.info('These are the files in the bundle: {files}'.format(
        files=files))
    shutil.rmtree(loc)


def get_workspace_files(file_type=None, workspace_path=None):
    file_type = file_type or '.wgn'
    workspace_path = workspace_path or os.path.join(
        os.path.abspath('workspace'), 'build')
    files = []
    if not os.path.isdir(workspace_path):
        return []
    for f in os.listdir(workspace_path):
        f = os.path.join(workspace_path, f)
        files.append(f)
        if f.endswith(file_type):
            f_md5 = f + '.md5'
            os.system('md5sum {0} > {1}'.format(f, f_md5))
            files.append(f_md5)
    logging.info('These are the workspace files: {0}'.format(files))
    return files


def copy_plugins_json_to_workspace(plugins_json):
    new_plugins_json_file = write_json(plugins_json)
    workspace_path = os.path.join(
        os.path.abspath('workspace'),
        'build',
        'plugins.json')
    shutil.copyfile(new_plugins_json_file, workspace_path)


def get_bundle_from_workspace(workspace_path=None):
    for filename in get_workspace_files('tgz', workspace_path=workspace_path):
        if filename.endswith('.tgz'):
            logging.info('Found bundle: {0}'.format(filename))
            return filename
    logging.warn('No bundle found in {workspace_path}'.format(
        workspace_path=workspace_path))


def package_blueprint(name, source_directory):
    archive_temp = NamedTemporaryFile(delete=False)
    if '/' in name:
        name = name.replace('/', '-')
        name = name.strip('-')
    destination = os.path.join(
        os.path.dirname(archive_temp.name), '{0}.zip'.format(name))
    create_archive(source_directory, archive_temp.name)
    logging.info('Moving {0} to {1}.'.format(archive_temp.name, destination))
    shutil.move(archive_temp.name, destination)
    return destination


def create_archive(source_directory, destination):
    logging.info(
        'Packaging archive from source: {0} to destination: {1}.'.format(
            source_directory, destination))
    zip_file = zipfile.ZipFile(destination, 'w')
    for root, _, files in os.walk(source_directory):
        for filename in files:
            logging.info('Packing {0} in archive.'.format(filename))
            file_path = os.path.join(root, filename)
            source_dir = os.path.dirname(source_directory)
            zip_file.write(
                file_path, os.path.relpath(file_path, source_dir))
    zip_file.close()
    logging.info('Finished writing archive {0}'.format(destination))
