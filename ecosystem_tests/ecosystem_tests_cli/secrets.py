import os
import base64

from .logger import logger
from .utilities import parse_key_value_pair
from .exceptions import EcosystemTestCliException

ERR_MSG = 'Invalid input format for secret: {0}, the expected format is: ' \
          'key=value'

ERR_MSG_FILE_SECRET = 'Invalid input format for secret: {0}, the expected ' \
                      'format is: ' \
                      'key=/path/to/file/contains/secret.'

ERR_MSG_ENCODED_SECRET = 'Invalid input format for secret: {0}, the ' \
                         'expected format is: key=base64encodedvalue'


def secrets_to_dict(secrets):
    """Returns a dictionary of base64 encoded secrets
    `secrets` can be:
    - key=value pairs tuple.
    """
    secrets_dict = {}
    for secret in secrets:
        key, val = parse_key_value_pair(secret, ERR_MSG.format(secret))
        secrets_dict.update(
            {key: base64.b64encode(val.encode('utf-8')).decode('ascii')})
    return secrets_dict


def file_secrets_to_dict(secrets):
    """Returns a dictionary of base64 encoded secrets
    `secrets` can be:
    - key=/path/to/file/contains/secret pairs tuple.
    """
    secrets_dict = {}
    for secret in secrets:
        key, path = parse_key_value_pair(secret,
                                         ERR_MSG_FILE_SECRET.format(secret))
        if not os.path.isfile(path):
            raise EcosystemTestCliException(
                'Secret file {path} dosen`t exists!'.format(path=path))
        encoded_content = _encode_file_content(path)
        secrets_dict.update({key: encoded_content})
    return secrets_dict


def _encode_file_content(path):
    """
    :param path: File path.The file contains secret.
    :return Base 64 encoded string represents the file content
    """
    with open(path, 'r') as f:
        content = f.read()
    return base64.b64encode(content.encode('utf-8')).decode('ascii')


def encoded_secrets_to_dict(secrets):
    """Returns a dictionary of base64 encoded secrets
    `secrets` can be:
    - key=base64encodedvalue pairs tuple.
    """
    secrets_dict = {}
    for secret in secrets:
        key, val = parse_key_value_pair(secret, ERR_MSG_ENCODED_SECRET.format(secret))
        secrets_dict.update({key: val})
    return secrets_dict


def prepare_secrets_dict_for_prepare_test(regular_secrets,
                                          file_secrets,
                                          encoded_secrets):
    secrets_dict = {}
    secrets_dict.update(
        create_single_secrets_dict_for_prepare_test(regular_secrets, False))
    secrets_dict.update(
        create_single_secrets_dict_for_prepare_test(file_secrets, True))
    # From our prspective all the encoded secres are file secrets.
    secrets_dict.update(
        create_single_secrets_dict_for_prepare_test(encoded_secrets, True))
    return secrets_dict


def create_single_secrets_dict_for_prepare_test(secret_dict, file_secret):
    prepare_test_secrets_dict = {}
    for key in secret_dict:
        prepare_test_secrets_dict.update({key: file_secret})
    return prepare_test_secrets_dict
