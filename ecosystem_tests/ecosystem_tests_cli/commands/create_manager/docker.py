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
import json
import shutil

import requests
from tqdm import tqdm
from urllib.parse import urlparse
from tempfile import NamedTemporaryFile

from ecosystem_tests.dorkl.commands import handle_process
from ecosystem_tests.ecosystem_tests_cli.logger import logger
from ecosystem_cicd_tools.new_cicd.s3 import download_from_s3
from ecosystem_tests.ecosystem_tests_cli.utilities import (
    get_universal_path)
from .utils import get_url

DOCKER_RUN_COMMAND = """-d --name {container_name} \
    -p 8000:8000 -p 80:80 -p 443:443 -p 5671:5671 {image_name}
"""


def container_exists(name):
    for container in docker_ps():
        if name in container.get('Names', []):
            if container.get('state') in ['exited']:
                logger.warning(
                    'Container name {name} exists, '
                    'but is not running. Deleting...'.format(name=name))
                docker_rm(name)
            else:
                logger.error(
                    'Unable to create docker container {name}. '
                    'Container {name} already exists and '
                    'cannot be deleted.'.format(name=name))
                return True
    logger.info('The container name {name} is unused.'.format(name=name))
    return False


def image_exists(image_name):
    repo, tag = get_repo_and_tag(image_name)
    for image in docker_images():
        if image.get('Repository') == repo and image.get('Tag') == tag:
            logger.warning(
                'The image {image_name} already exists '
                'and can be used.'.format(image_name=image_name))
            return True
    logger.info('The image {image_name} does not exist.'.format(
        image_name=image_name))
    return False


def docker_ps():
    return handle_list_response(docker('ps -a'))


def docker_rm(name):
    return docker('rm {name}'.format(name=name))


def docker_images():
    return handle_list_response(docker('images'))


def docker_load(filename):
    with tqdm(desc='docker load -i {filename}'.format(filename=filename),
              total=100) as pbar:
        result = docker('load -i {filename}'.format(
            filename=filename), json_format=False)
        pbar.update(80)
        if 'Loaded image' in result:
            pbar.update(20)
            return result.split()[-1]
        pbar.update(20)


def docker_rmi(image_name):
    return docker('rmi {image_name}'.format(image_name=image_name),
                  json_format=False)


def docker(subcommand, json_format=True):
    command = ['docker']
    command.extend(subcommand.split())
    if json_format:
        command.extend(["--format", "'{{json .}}'"])
    result = handle_process(' '.join(command), log=False)
    logger.info('Docker command result: {}'.format(result))
    return result


def handle_list_response(response):
    items = []
    for item in response.split('\n'):
        if len(item):
            items.append(json.loads(item))
    return items


def get_repo_and_tag(image_name):
    try:
        repo, tag = image_name.split(':')
    except ValueError:
        repo, tag = image_name, 'latest'
    return repo, tag


def download_file(url, local_filename):
    with tqdm(desc='requests GET {}'.format(url), total=100) as pbar:
        with requests.get(url, stream=True) as r:
            pbar.update(20)
            with open(local_filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
                pbar.update(80)


def download_and_load_docker_image(url, image_name=None):
    up = urlparse(url)
    if not up.path:
        logger.error('Unable to resolve download url: {}'.format(url))
    with NamedTemporaryFile(dir=os.path.expanduser('~')) as f:
        logger.info('Downloading this object: {}'.format(url))
        if up.scheme in ['http', 'https']:
            download_file(url, f.name)
        else:
            download_from_s3(f.name, url)
        filename = get_universal_path(f.name)
        image_name = docker_load(filename) or image_name
    return image_name


def load_new_image(image_name, url, version, release, architecture):
    url = url or get_url(version, release, architecture)
    return download_and_load_docker_image(url, image_name)


def docker_run(command):
    docker('run {command}'.format(command=command), json_format=False)


def docker_exec(command, interactive=True):
    if interactive:
        command = '-it ' + command
    return docker('exec {command}'.format(command=command), json_format=False)


def start_container(container_name, image_name):
    docker_run(DOCKER_RUN_COMMAND.format(
        image_name=image_name,
        container_name=container_name)
    )
    docker_exec('cfy_manager cfy_manager wait-for-starter')
