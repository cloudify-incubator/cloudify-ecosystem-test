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

from ecosystem_tests.ecosystem_tests_cli import ecosystem_tests

from .docker import (
    docker_rmi,
    image_exists,
    load_new_image,
    start_container,
    container_exists)

CONTAINER_NAME = 'cfy_manager'
IMAGE_NAME = 'cloudify-manager-aio:latest'


@ecosystem_tests.command(name='create-manager',
                         short_help='Create a local docker manager')
@ecosystem_tests.options.container_name
@ecosystem_tests.options.image_name
@ecosystem_tests.options.use_existing_image
@ecosystem_tests.options.url
@ecosystem_tests.options.version
@ecosystem_tests.options.release_name
@ecosystem_tests.options.architecture
def create_manager(container_name,
                   image_name,
                   use_existing_image,
                   url,
                   version,
                   release_name,
                   architecture):
    """
    Run a local docker manager.
    """
    container_name = container_name or CONTAINER_NAME
    image_name = image_name or IMAGE_NAME
    if container_exists(container_name):
        sys.exit(1)
    if image_exists(image_name) and not use_existing_image:
        docker_rmi(image_name)
    if not use_existing_image:
        image_name = load_new_image(
            image_name, url, version, release_name, architecture)
    start_container(container_name, image_name)
