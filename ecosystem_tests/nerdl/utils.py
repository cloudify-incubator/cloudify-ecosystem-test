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
import shutil
import zipfile
import requests
import tempfile
import contextlib
from urllib.parse import urlparse

from ecosystem_tests.ecosystem_tests_cli.logger import logger


def download_file(url, destination=None, keep_name=False):
    CHUNK_SIZE = 1024

    if not destination:
        if keep_name:
            path = urlparse(url).path
            name = os.path.basename(path)
            destination = os.path.join(tempfile.mkdtemp(), name)
        else:
            fd, destination = tempfile.mkstemp()
            os.close(fd)

    try:
        response = requests.get(url, stream=True)
    except requests.exceptions.RequestException as ex:
        logger.error('Failed to call GET on {0}'.format(url))
        sys.exit(1)

    final_url = response.url
    if final_url != url:
        logger.debug('Redirected to {0}'.format(final_url))
        pass

    try:
        with open(destination, 'wb') as destination_file:
            for chunk in response.iter_content(CHUNK_SIZE):
                destination_file.write(chunk)
    except IOError as ex:
        logger.error('Failed to write to {0}'.format(destination))
        sys.exit(1)

    return destination


def get_local_path(source, destination=None, create_temp=False):
    allowed_schemes = ['http', 'https']
    if urlparse(source).scheme in allowed_schemes:
        downloaded_file = download_file(source, destination, keep_name=True)
        return downloaded_file
    else:
        source = os.path.abspath(source)
        if os.path.isfile(source):
            if not destination and create_temp:
                source_name = os.path.basename(source)
                destination = os.path.join(tempfile.mkdtemp(), source_name)
            if destination:
                shutil.copy(source, destination)
                return destination
            else:
                return source
        else:
            logger.error(
                'You must provide either a path to a local file, '
                'or a remote URL '
                'using one of the allowed schemes: {0}'.format(
                    allowed_schemes))


def zip_files(files):
    source_folder = tempfile.mkdtemp()
    destination_zip = source_folder + '.zip'
    for path in files:
        shutil.copy(path, source_folder)
    create_zip(source_folder, destination_zip, include_folder=False)
    shutil.rmtree(source_folder)
    return destination_zip


def create_zip(source, destination, include_folder=True):
    logger.debug('Creating zip archive: {0}...'.format(destination))
    with contextlib.closing(zipfile.ZipFile(destination, 'w')) as zip_file:
        for root, _, files in os.walk(source):
            for filename in files:
                file_path = os.path.join(root, filename)
                source_dir = os.path.dirname(source) if include_folder\
                    else source
                zip_file.write(
                    file_path, os.path.relpath(file_path, source_dir))
    return destination


def generate_progress_handler(file_path, action='', max_bar_length=80):
    terminal_width = os.get_terminal_size().columns
    terminal_width = terminal_width or max_bar_length
    bar_length = min(max_bar_length, terminal_width) - len(action) - 12
    file_name = os.path.basename(file_path)
    if len(file_name) > (bar_length // 4) + 3:
        file_name = file_name[:bar_length // 4] + '...'
    bar_length -= len(file_name)

    def print_progress(read_bytes, total_bytes):
        filled_length = min(bar_length, int(round(bar_length * read_bytes /
                                                  float(total_bytes))))
        percents = min(100.00, round(
            100.00 * (read_bytes / float(total_bytes)), 2))
        bar = '#' * filled_length + '-' * (bar_length - filled_length)
        msg = '\r{0} {1} |{2}| {3}%'.format(action, file_name, bar, percents)
        logger.info(msg)

    return print_progress
