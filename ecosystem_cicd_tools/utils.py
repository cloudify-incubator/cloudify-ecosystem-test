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
import json
import base64
import shutil
import logging
import tarfile
import zipfile
import mimetypes
from contextlib import contextmanager
from tempfile import NamedTemporaryFile, mkdtemp

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)

BUCKET_NAME = 'cloudify-release-eu'


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
                     s3_object=None,
                     workspace_path=None):
    """
    Download a file from s3.
    :param remote_path: The s3 key.
    :param local_path: The destination path.
    :param bucket_name: The s3 bucket.
    :param s3_object: Optional if you have created the boto3 s3 object alredy.
    :param workspace_path: dir where we work
    :return:
    """

    logging.info('download_from_s3 {s3_object} {remote_path} to {local_path}.'
                 .format(s3_object=s3_object,
                         remote_path=remote_path,
                         local_path=local_path))

    workspace_path = workspace_path or os.path.join(
        os.path.abspath('workspace'), 'build')

    if not local_path:
        if not os.path.exists(workspace_path):
            os.makedirs(os.path.dirname(workspace_path))
        archive_temp = NamedTemporaryFile(delete=False, dir=workspace_path)
        local_path = archive_temp.name

    if not os.path.exists(os.path.dirname(local_path)):
        os.makedirs(os.path.dirname(local_path))

    with aws():
        if not s3_object:
            bucket_name = bucket_name or BUCKET_NAME
            s3 = boto3.resource('s3')
            s3_object = s3.Object(bucket_name, remote_path)
        logging.info('Downloading {s3_object} to {local_path}.'.format(
            s3_object=s3_object, local_path=local_path))
        logging.info('....Starting download')
        try:
            s3_object.download_file(
                local_path,
                Config=boto3.s3.transfer.TransferConfig(use_threads=False))
        except ClientError:
            logging.info('....Download failed.')

    if not os.path.exists(local_path):
        if os.path.exists(
                os.path.join(workspace_path, os.path.basename(local_path))):
            local_path = os.path.join(
                workspace_path, os.path.basename(local_path))
        raise RuntimeError(
            'There is no path for the file {}'.format(local_path))

    logging.info('....Finished download')
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


def find_wagon_local_path(docker_path, workspace_path=None):
    """

    :param docker_path:
    :param workspace_path:
    :return:
    """
    logging.info('Finding wagon {} in {}'.format(docker_path, workspace_path))
    for f in get_workspace_files(workspace_path=workspace_path):
        logging.info('Checking \n{} against \n{}'.format(
            os.path.basename(docker_path), f))
        if os.path.basename(docker_path) in f and f.endswith('.wgn'):
            return f
    return docker_path


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
