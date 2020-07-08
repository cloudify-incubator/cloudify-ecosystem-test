
from __future__ import with_statement

import os
import base64
import shutil
import logging
import zipfile
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

import boto3

BUCKET_NAME = 'cloudify-release-eu'


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


def upload_to_s3(local_path, bucket_path, bucket_name=None, **_):
    with aws():
        bucket_name = bucket_name or BUCKET_NAME
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        bucket.upload_file(local_path, bucket_path)


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
