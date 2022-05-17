import os
import base64
from functools import wraps

from boto3 import resource

from .logging import logger

BUCKET_NAME = 'cloudify-release-eu'
BUCKET_FOLDER = 'cloudify/wagons'

ACCESS_KEY = 'aws_access_key_id'
ACCESS_SECRET = 'aws_secret_access_key'


def with_s3_client(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):

        kwargs['s3'] = get_client()
        func(*args, **kwargs)
    return wrapper_func


def get_client():
    if ACCESS_KEY in os.environ:
        access_key = os.environ[ACCESS_KEY].strip('\n')
        os.environ[ACCESS_KEY.upper()] = str(base64.b64decode(
            access_key), 'utf-8').strip('\n')
    elif ACCESS_KEY.upper() in os.environ:
        pass
    else:
        raise RuntimeError(
            'Please provide {} environment variable.'.format(
                ACCESS_KEY.upper()))

    if ACCESS_SECRET in os.environ:
        access_secret = os.environ[ACCESS_SECRET].strip('\n')
        os.environ[ACCESS_SECRET.upper()] = str(base64.b64decode(
            access_secret), 'utf-8').strip('\n')
    elif ACCESS_SECRET.upper() in os.environ:
        pass
    else:
        raise RuntimeError(
            'Please provide {} environment variable.'.format(
                ACCESS_SECRET.upper()))
    if 'AWS_DEFAULT_REGION' not in os.environ:
        os.environ['AWS_DEFAULT_REGION'] = 'eu-west-1'

    return resource('s3')


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
    logger.info('Uploading {plugin_name} {plugin_version} to S3.'.format(
        plugin_name=plugin_name, plugin_version=plugin_version))
    upload_to_s3(local_path, bucket_path)


@with_s3_client
def upload_to_s3(local_path,
                 remote_path,
                 bucket_name=None,
                 content_type=None,
                 s3=None):
    """
    Upload a local file to s3.
    :param local_path: The local path to the file that we want to upload.
    :param remote_path: The s3 key.
    :param bucket_name: The s3 bucket.
    :param content_type: By default s3 upload_file adds
        content-type octet-stream. This is not universal, for example JSON
        files need to be application/json.
    :param s3: s3 client boto3
    :return:
    """
    bucket_name = bucket_name or BUCKET_NAME
    bucket = s3.Bucket(bucket_name)
    logger.info('Uploading {local_path} to s3://{remote_path}.'.format(
        local_path=local_path, remote_path=remote_path))
    extra_args = {'ACL': 'public-read'}
    if content_type:
        extra_args.update({'ContentType': content_type})
    bucket.upload_file(local_path,
                       remote_path,
                       ExtraArgs=extra_args)
    object_acl = s3.ObjectAcl(bucket_name, remote_path)
    object_acl.put(ACL='public-read')
