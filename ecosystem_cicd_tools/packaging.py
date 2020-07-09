
import os
import json
import yaml
import base64
import shutil
import logging
import tarfile
import zipfile
import requests
from contextlib import contextmanager
from tempfile import NamedTemporaryFile, mkdtemp

import boto3

logging.basicConfig(level=logging.INFO)
BUCKET_NAME = 'cloudify-release-eu'
BUCKET_FOLDER = 'cloudify/wagons'
PLUGINS_JSON_PATH = os.path.join(BUCKET_FOLDER, 'plugins.json')
EXAMPLES_JSON = 'resources/examples.json'
PLUGINS_JSON = 'resources/plugins.json'
PLUGINS_TO_BUNDLE = ['vSphere',
                     'Terraform',
                     'Docker',
                     'OpenStack',
                     'Fabric',
                     'GCP',
                     'AWS',
                     'Azure',
                     'Ansible',
                     'Kubernetes',
                     'Utilities']
REDHAT = 'Redhat Maipo'
CENTOS = 'Centos Core'
DISTROS_TO_BUNDLE = [CENTOS, REDHAT]
PLUGINS_BUNDLE_NAME = 'cloudify-plugins-bundle'
ASSET_URL_DOMAIN = 'http://repository.cloudifysource.org'
ASSET_URL_TEMPLATE = ASSET_URL_DOMAIN + '/{0}/{1}/{2}/{3}'


@contextmanager
def aws(aws_secrets=None, **_):
    aws_secrets = aws_secrets or ['aws_access_key_id', 'aws_secret_access_key']
    try:
        for envvar in aws_secrets:
            secret = base64.b64decode(os.environ[envvar])
            os.environ[envvar.upper()] = secret.rstrip('\n')
        yield
    finally:
        for envvar in ['aws_access_key_id', 'aws_secret_access_key']:
            del os.environ[envvar.upper()]


def upload_to_s3(local_path,
                 remote_path,
                 bucket_name=None):
    with aws():
        bucket_name = bucket_name or BUCKET_NAME
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        logging.info('Uploading {local_path} to s3://{remote_path}.'.format(
            local_path=local_path, remote_path=remote_path))
        bucket.upload_file(local_path, remote_path)


def download_from_s3(remote_path,
                     local_path=None,
                     bucket_name=None,
                     s3_object=None):
    with aws():
        if not local_path:
            archive_temp = NamedTemporaryFile(delete=False)
            local_path = archive_temp.name
        if not s3_object:
            bucket_name = bucket_name or BUCKET_NAME
            s3 = boto3.resource('s3')
            s3_object = s3.Object(bucket_name, remote_path)
        logging.info('Downloading s3://{local_path}.'.format(
            local_path=local_path))
        s3_object.download_file(local_path)
        return local_path


def read_json_file(file_path):
    with open(file_path, 'r') as outfile:
        return json.load(outfile)


def write_json_and_upload_to_s3(content, remote_path, bucket_name):
    logging.info('Writing new content to s3://{remote_path}.'.format(
        remote_path=remote_path))
    logging.debug('The new data is {content}'.format(content=content))
    archive_temp = NamedTemporaryFile(delete=False)
    with open(archive_temp.name, 'w') as outfile:
        json.dump(content, outfile, ensure_ascii=False, indent=4)
    upload_to_s3(archive_temp.name, remote_path, bucket_name)


def get_plugins_json(remote_path):
    local_path = download_from_s3(remote_path, PLUGINS_JSON)
    return read_json_file(local_path)


def update_assets_in_plugin_dict(plugin_dict, assets):
    logging.debug('Updating plugin JSON with assets {assets}'.format(
        assets=assets))
    for asset in assets:
        if asset.endswith('.yaml'):
            plugin_dict['link'] = asset
            continue
        for wagon in plugin_dict['wagons']:
            if wagon['name'] == REDHAT and 'redhat-Maipo' in asset:
                if 'md5' in asset:
                        wagon['md5url'] = asset
                else:
                    wagon['url'] = asset
            elif wagon['name'] == CENTOS and 'centos-Core' in asset:
                if 'md5' in asset:
                        wagon['md5url'] = asset
                else:
                    wagon['url'] = asset


def get_plugin_new_json(remote_path, plugin_name, plugin_version, assets):
    plugins_list = get_plugins_json(remote_path)
    for pd in plugins_list:
        if plugin_name == pd['name']:
            if plugin_version.split('.')[0] == pd['version'].split('.')[0]:
                update_assets_in_plugin_dict(pd, assets)
    return plugins_list


def update_plugins_json(plugin_name, plugin_version, assets):
    logging.info(
        'Updating {plugin_name} {plugin_version} in plugin JSON'.format(
            plugin_name=plugin_name,
            plugin_version=plugin_version))
    assets = [ASSET_URL_TEMPLATE.format(BUCKET_FOLDER,
                                        plugin_name,
                                        plugin_version,
                                        asset) for asset in assets]
    plugin_dict = get_plugin_new_json(
        PLUGINS_JSON_PATH,
        plugin_name,
        plugin_version,
        assets)
    write_json_and_upload_to_s3(plugin_dict, PLUGINS_JSON_PATH, BUCKET_NAME)


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


def create_plugin_metadata(wgn_path, yaml_path, directory):
    """This is related to How the plugin bundle is unpacked."""
    plugin_root_dir = os.path.basename(wgn_path).split('.wgn')[0]
    os.mkdir(os.path.join(directory, plugin_root_dir))
    dest_wgn_path = os.path.join(plugin_root_dir,
                                 os.path.basename(wgn_path))
    dest_yaml_path = os.path.join(plugin_root_dir,
                                  os.path.basename(yaml_path))
    dest_wgn_path = download_from_s3(
        wgn_path.replace(ASSET_URL_TEMPLATE, BUCKET_FOLDER), dest_wgn_path)
    dest_yaml_path = download_from_s3(
        yaml_path.replace(ASSET_URL_TEMPLATE, BUCKET_FOLDER), dest_yaml_path)
    return dest_wgn_path, dest_yaml_path


def create_plugin_bundle_archive(mappings, tar_name=None, destination=None):
    tar_name = tar_name or PLUGINS_BUNDLE_NAME
    destination = destination or mkdtemp()
    work_dir = mkdtemp()

    metadata = {}
    for key, value in mappings.iteritems():
        wagon_path, yaml_path = create_plugin_metadata(key, value, work_dir)
        metadata[wagon_path] = yaml_path

    with open(os.path.join(work_dir, 'METADATA'), 'w+') as f:
        yaml.dump(metadata, f)
    tar_path = os.path.join(destination, '{0}.tgz'.format(tar_name))
    tarfile_ = tarfile.open(tar_path, 'w:gz')
    try:
        tarfile_.add(work_dir, arcname=tar_name)
    finally:
        tarfile_.close()
        shutil.rmtree(work_dir, ignore_errors=True)
    return tar_path


def build_plugins_bundle():
    plugins = get_plugins_json(PLUGINS_JSON_PATH)
    mapping = {}

    for plugin in plugins:
        if plugin['title'] in PLUGINS_TO_BUNDLE:
            plugin_yaml = plugin['link']
            for wagon in plugin['wagons']:
                if wagon['name'] in DISTROS_TO_BUNDLE:
                    mapping[wagon['url']] = plugin_yaml

    bundle_archive = create_plugin_bundle_archive(mapping)
    print bundle_archive
    # upload_to_s3(bundle_archive,
    #              os.path.join(BUCKET_FOLDER, os.path.basename(bundle_archive)))


def get_workspace_files(file_type=None):
    file_type = file_type or '.wgn'
    workspace_path = os.path.join(os.path.abspath('workspace'), 'build')
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
    logging.info('These are the workspace files: {0}'.format(
        files))
    return files


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
