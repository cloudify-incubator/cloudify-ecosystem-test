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
import sys

from ecosystem_cicd_tools.new_cicd.s3 import (
    BUCKET_NAME,
    get_objects_in_key,
)
from ecosystem_tests.ecosystem_tests_cli.logger import logger

S3_PROJECT = 'cloudify'


def get_url(version=None, release=None, architecture=None):
    version = version or '6.4.2'
    release = release or 'ga-release'
    if not release.endswith('-release'):
        logger.error(
            'The release name "{}" appears invalid. '
            'Release should usually end with "-release", '
            'for example, ".dev1-release".'.format(release))
    if release != 'ga-release' and not release.startswith('.'):
        logger.error(
            'The release name "{}" is not "ga-release", '
            'and does not start with ".". It appears invalid. '
            'For example, ".dev1-release" is a valid release name.'.format(
                release)
        )
    architecture = architecture or 'aarch64'
    # E.g. s3://cloudify-release-eu/cloudify/6.4.1/ga-release/cloudify-manager-aio-docker-6.4.1-ga-aarch64.tar  # noqa
    prefix = '{project}/'.format(project=S3_PROJECT)
    if version:
        prefix += '{version}/'.format(version=version)
    if version and release:
        prefix += '{release}/cloudify-manager-aio-docker-{version}'.format(
            release=release, version=version)
    filter_kwargs = dict(Prefix=prefix)
    # TODO: Effectively sort this response.
    objects = get_objects_in_key(filter_kwargs=filter_kwargs)
    if not objects:
        logger.error(
            'No release images were found matching {}.'.format(filter_kwargs)
        )
        sys.exit(1)
    for object in objects:
        if object.endswith('{}.tar'.format(architecture)):
            return object
