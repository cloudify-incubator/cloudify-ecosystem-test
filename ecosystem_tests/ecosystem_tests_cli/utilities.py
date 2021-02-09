########
# Copyright (c) 2014-2019 Cloudify Platform Ltd. All rights reserved
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
from contextlib import contextmanager

from nose.tools import nottest

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


@nottest
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
