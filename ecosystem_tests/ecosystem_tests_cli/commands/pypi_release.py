########
# Copyright (c) 2014-2022 Cloudify Platform Ltd. All rights reserved
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
import sys
import pathlib
from time import sleep
from datetime import datetime, timedelta

from ..logger import logger

from ecosystem_cicd_tools.utils import get_resp
from .package_release import find_version_in_files
from ...ecosystem_tests_cli import ecosystem_tests

short_help = 'Call the Jenkins release Job ' \
             'and verify that it was successful!'

template = 'https://pypi.org/project/{}/{}/'


@ecosystem_tests.command(name='pypi-release',
                         short_help=short_help)
@ecosystem_tests.options.directory
@ecosystem_tests.options.name
@ecosystem_tests.options.timeout
def pypi_release(directory, name, timeout):
    name = name or pathlib.Path(directory).name
    version = find_version_in_files(directory)
    endpoint = template.format(name, version)
    start = datetime.now()
    logger.info('Checking if project {} has version {}'.format(name, version))
    while True:
        if datetime.now() - start > timedelta(seconds=timeout):
            logger.error('Failed to verify successful release {} {}.'.format(
                name, version))
            sys.exit(1)
        elif get_resp(url=endpoint):
            logger.info('Successfully verified that the '
                        'project {} release {} exists.'.format(name, version))
            break
        logger.info('Still checking if project {} has version {}'.format(
            name, version))
        sleep(10)
