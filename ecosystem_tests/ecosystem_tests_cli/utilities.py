import os
from contextlib import contextmanager

from .exceptions import EcosystemTestCliException
from .constants import (LICENSE_ENVAR_NAME,
                        MANAGER_CONTAINER_ENVAR_NAME)


def parse_key_value_pair(mapped_input, error_msg):
    split_mapping = mapped_input.split('=', 1)
    try:
        key = split_mapping[0].strip()
        value = split_mapping[1].strip()
        return key, value
    except IndexError:
        raise EcosystemTestCliException(
            error_msg)


@contextmanager
def prepare_test_env(license,
                     secret,
                     file_secret,
                     encoded_secret,
                     container_name):
    """
        prepare environment for prepare test.
    """
    old_environ = dict(os.environ)
    os.environ.update({LICENSE_ENVAR_NAME: license})
    os.environ.update({MANAGER_CONTAINER_ENVAR_NAME: container_name})
    os.environ.update(secret)
    os.environ.update(file_secret)
    os.environ.update(encoded_secret)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)
