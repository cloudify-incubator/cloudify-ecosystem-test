import os
import base64

from boto3 import resource, client

ACCESS_KEY = 'aws_access_key_id'
ACCESS_SECRET = 'aws_secret_access_key'


def get_boto_client(client_name):
    return get_boto_service(client_name=client_name)


def get_boto_service(service_name=None, client_name=None):
    if ACCESS_KEY in os.environ:
        access_key = os.environ[ACCESS_KEY].strip('\n')
        try:
            os.environ[ACCESS_KEY.upper()] = str(base64.b64decode(
                access_key), 'utf-8').strip('\n')
        except UnicodeDecodeError:
            pass
    elif ACCESS_KEY.upper() in os.environ:
        pass
    else:
        raise RuntimeError(
            'Please provide {} environment variable.'.format(
                ACCESS_KEY.upper()))
    if ACCESS_SECRET in os.environ:
        access_secret = os.environ[ACCESS_SECRET].strip('\n')
        try:
            os.environ[ACCESS_SECRET.upper()] = str(base64.b64decode(
                access_secret), 'utf-8').strip('\n')
        except UnicodeDecodeError:
            pass
    elif ACCESS_SECRET.upper() in os.environ:
        pass
    else:
        raise RuntimeError(
            'Please provide {} environment variable.'.format(
                ACCESS_SECRET.upper()))
    if 'AWS_DEFAULT_REGION' not in os.environ:
        os.environ['AWS_DEFAULT_REGION'] = 'eu-west-1'

    if client_name:
        return client(client_name)

    return resource(service_name)
