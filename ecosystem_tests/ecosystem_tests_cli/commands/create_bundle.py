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
import json

from ..logger import logger
from ...ecosystem_tests_cli import ecosystem_tests
from ecosystem_cicd_tools.packaging import create_plugin_bundle_archive, \
                                               configure_bundle_archive


@ecosystem_tests.command(name='create-bundle',
                         short_help='create plugins bundle.')
@ecosystem_tests.options.directory
def create_bundle(directory):
    if directory:
        json_content = get_json_content(directory)
    else:
        json_content = None
    bundle_path = create_plugin_bundle_archive(
        *configure_bundle_archive(json_content))
    logger.info("bundle path is {}".format(bundle_path))


def get_json_content(json_path):
    f = open(json_path)
    data = json.load(f)
    f.close()
    return data
