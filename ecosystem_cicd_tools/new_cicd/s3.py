import os
from functools import wraps

from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig

from .logging import logger
from .boto3 import get_boto_service

BUCKET_NAME = 'cloudify-release-eu'
BUCKET_FOLDER = 'cloudify/wagons'

ACCESS_KEY = 'aws_access_key_id'
ACCESS_SECRET = 'aws_secret_access_key'

URL_TEMPLATE = 'http://repository.cloudifysource.org/cloudify/wagons/{}/{}/{}'


def with_s3_client(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):

        kwargs['s3'] = get_client()
        return func(*args, **kwargs)
    return wrapper_func


def get_client():
    return get_boto_service('s3')


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


@with_s3_client
def get_assets(plugin_name,
               plugin_version,
               bucket_name=BUCKET_NAME,
               s3=None):
    url = 'cloudify/wagons/{plugin_name}/{plugin_version}/'.format(
        plugin_name=plugin_name,
        plugin_version=plugin_version)
    assets_list_s3 = []
    my_bucket = s3.Bucket(bucket_name)
    for object_summary in my_bucket.objects.filter(Prefix=url):
        assets_list_s3.append(object_summary.key.split(url)[-1])
    return assets_list_s3


@with_s3_client
def download_from_s3(local_path,
                     remote_path,
                     s3=None):

    logger.info('download_from_s3 {remote_path} to {local_path}.'
                .format(remote_path=remote_path,
                        local_path=local_path))

    s3_object = s3.Object(BUCKET_NAME, remote_path)

    if object_exists(s3_object):
        s3_object.download_file(
            local_path,
            Config=TransferConfig(use_threads=False))

    if os.path.exists(local_path):
        logger.info('The file exists: {}.'.format(local_path))


def object_exists(o):
    try:
        o.content_length
    except ClientError:
        return False
    else:
        return True


@with_s3_client
def get_plugin_yaml_url(plugin_name, filename, plugin_version, s3=None):
    logger.debug('Getting plugin YAML file: {} {} {} {}.'.format(
        BUCKET_FOLDER,
        plugin_name,
        plugin_version,
        filename))
    bucket_path = os.path.join(BUCKET_FOLDER,
                               plugin_name,
                               plugin_version,
                               filename)
    s3_object = s3.Object(BUCKET_NAME, bucket_path)
    if object_exists(s3_object):
        return URL_TEMPLATE.format(plugin_name, plugin_version, filename)


@with_s3_client
def get_objects_in_key(plugin_name, plugin_version, s3=None):
    bucket = s3.Bucket(BUCKET_NAME)
    objects = bucket.objects.filter(
        Prefix='{}/{}/{}'.format(BUCKET_FOLDER, plugin_name, plugin_version))
    sorted_objects = sorted(
        objects,
        key=lambda v: v.key)
    objects = [o.key for o in sorted_objects]
    logger.debug('Objects in key: {} {} {}'.format(
        plugin_name, plugin_version, objects))
    return objects


@with_s3_client
def get_objects_in_key(plugin_name=None,
                       plugin_version=None,
                       bucket_folder=None,
                       filter_kwargs=None,
                       s3=None):

    bucket = s3.Bucket(BUCKET_NAME)
    if plugin_name and plugin_version and not filter_kwargs:
        filter_kwargs = dict(
            Prefix='{}/{}/{}'.format(
                bucket_folder or BUCKET_FOLDER,
                plugin_name,
                plugin_version
            )
        )
    logger.debug('Object filter params: {}'.format(filter_kwargs))
    objects = bucket.objects.filter(**filter_kwargs)
    logger.debug('Object filter result: {}'.format(objects))

    sorted_objects = sorted(
        objects,
        key=lambda v: v.key)
    objects = [o.key for o in sorted_objects]
    return objects
