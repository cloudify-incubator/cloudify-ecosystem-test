
import os
import json
import base64
import shutil
import logging
import zipfile
from collections import OrderedDict
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

import boto3

BUCKET_NAME = 'cloudify-release-eu'
EXAMPLES_JSON = 'resources/examples.json'
PLUGINS_JSON = 'resources/plugins.json'


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
        s3_object.download_file(local_path)
        return local_path


def read_json_file(file_path):
    with open(file_path, 'r') as outfile:
        return json.load(outfile, object_pairs_hook=OrderedDict)


def write_json_and_upload_to_s3(content, remote_path, bucket_name):
    archive_temp = NamedTemporaryFile(delete=False)
    with open(archive_temp.name, 'w') as outfile:
        json.dump(content, outfile, ensure_ascii=False, indent=4)
    upload_to_s3(remote_path, bucket_name)


def get_plugins_json(remote_path):
    local_path = download_from_s3(remote_path, PLUGINS_JSON)
    return read_json_file(local_path)


def update_assets_in_plugin_dict(plugin_dict, assets):
    for asset in assets:
        if asset.endswith('.yaml'):
            plugin_dict['link'] = asset
            continue
        for wagon in plugin_dict['wagons']:
            if wagon['name'] == 'Redhat Maipo' and 'redhat' in asset:
                if 'md5' in asset:
                        wagon['md5url'] = asset
                else:
                    wagon['url'] = asset
            elif wagon['name'] == 'centos Core' and 'centos' in asset:
                if 'md5' in asset:
                        wagon['md5url'] = asset
                else:
                    wagon['url'] = asset
    return plugin_dict


def get_plugin_new_json(remote_path, plugin_name, plugin_version, assets):
    for pd in get_plugins_json(remote_path):
        if plugin_name == pd['name']:
            if plugin_version.split('.')[0] == pd['version'].split('.')[0]:
                return update_assets_in_plugin_dict(pd, assets)
    raise RuntimeError('The plugin {plugin_name} {plugin_version} '
                       'was not found in the plugins.json.'.format(
                           plugin_name=plugin_name,
                           plugin_version=plugin_version))


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
