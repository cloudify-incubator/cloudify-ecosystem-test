########
# Copyright (c) 2014-2021 Cloudify Platform Ltd. All rights reserved
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
import random
import string
import base64
import binascii
import functools

from nose.tools import nottest

from cloudify._compat import text_type

from .exceptions import EcosystemTestCliException
from ..dorkl.commands import get_manager_container_name
from .constants import (LICENSE_ENVAR_NAME,
                        MANAGER_CONTAINER_ENVAR_NAME)


def parse_key_value_pair(mapped_input, error_msg):
    split_mapping = mapped_input.split('=', 1)
    try:
        key = text_type(split_mapping[0].strip())
        value = text_type(split_mapping[1].strip())
        return key, value
    except IndexError:
        raise EcosystemTestCliException(
            error_msg)


@nottest
def prepare_test_env(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        old_environ = dict(os.environ)
        os.environ.update({LICENSE_ENVAR_NAME: kwargs.get('license', '')})
        os.environ.update({MANAGER_CONTAINER_ENVAR_NAME: kwargs.get(
            'container_name', get_manager_container_name())})
        os.environ.update(kwargs.get('secret', {}))
        os.environ.update(kwargs.get('file_secret', {}))
        os.environ.update(kwargs.get('encoded_secret', {}))
        try:
            ret = func(*args, **kwargs)
        finally:
            os.environ.clear()
            os.environ.update(old_environ)
        return ret

    return wrapper


@nottest
def validate_and_generate_test_ids(blueprint_path, test_id):
    """
    Validate that if user pass mupltiple bluprints paths so test_id is not
    provided.
    If the user pass multiple blueprints to test , generate list of tuples:
    [(bp1,id1),(bp2,id2)].
    """
    if test_id:
        if len(blueprint_path) > 1:
            raise EcosystemTestCliException(
                'Please do not provide test-id with multiple blueprints to '
                'test.')
        test_ids = [test_id]

    else:
        # Generate test ids for all blueprints.
        test_ids = [id_generator() for _ in range(len(blueprint_path))]

    return list(zip(blueprint_path, test_ids))


def id_generator(size=6, chars=string.ascii_lowercase + string.digits):
    return 'test_' + ''.join(random.choice(chars) for _ in range(size))


def validate_string_is_base64_encoded(encoded_string):
    """
    This function try's to decode the received string.
    If it fails so the string is not base64 encoded.
    """
    try:
        base64.b64decode(encoded_string.encode('utf-8')).decode('ascii')
    except (TypeError, binascii.Error):
        raise EcosystemTestCliException(
            'string: {val} is not base64 encoded.'.format(
                val=encoded_string))
