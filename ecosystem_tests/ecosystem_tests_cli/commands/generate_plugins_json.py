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
import json

from ecosystem_cicd_tools.new_cicd import s3
from ecosystem_cicd_tools.new_cicd import actions
from ...ecosystem_tests_cli import (logger, ecosystem_tests)


@ecosystem_tests.command(name='generate-plugins-json',
                         short_help='Create a new plugins JSON file.')
@ecosystem_tests.options.plugins_yaml_version
@ecosystem_tests.options.upload_to_s3
@ecosystem_tests.options.directory
def generate_plugins_json(plugins_yaml_version, upload_to_s3, directory):
    json_formatted_string, filename = get_plugins_json(plugins_yaml_version)
    filename = output_file(directory, filename, json_formatted_string)
    if upload_to_s3:
        upload_file(filename)


def get_plugins_json(plugins_yaml_version):
    if plugins_yaml_version == 'v1':
        filename = 'plugins.json'
        new_json = actions.populate_plugins_json()
    elif plugins_yaml_version == 'v2':
        filename = 'v2_plugins.json'
        new_json = actions.populate_plugins_json('v2_plugin.yaml')
    else:
        raise RuntimeError('Unsupported plugins YAML version {}.'.format(
            plugins_yaml_version))
    json_formatted_string = json.dumps(new_json, indent=4)
    return json_formatted_string, filename


def output_file(directory, filename, json_formatted_string):
    if directory:
        filename = os.path.join(directory, filename)
    with open(filename, 'w') as outfile:
        outfile.write(json_formatted_string)
    logger.logger.info('New plugins JSON at {}'.format(filename))
    return filename


def upload_file(filename):
    remote_name = '{}/{}/{}'.format(
            s3.BUCKET_NAME,
            s3.BUCKET_FOLDER,
            os.path.basename(filename),
        )
    logger.logger.info('Uploading {} to s3.'.format(remote_name))
    s3.upload_to_s3(
        filename,
        remote_name
    )
