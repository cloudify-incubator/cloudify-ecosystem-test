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
import base64
import posixpath
import subprocess
from tqdm import tqdm
from time import sleep
from shlex import split
from pathlib import PureWindowsPath
from tempfile import NamedTemporaryFile
from datetime import datetime, timedelta

from ecosystem_tests.ecosystem_tests_cli.utilities import (
    get_universal_path)
from ecosystem_tests.dorkl.constansts import (logger,
                                              TIMEOUT,
                                              MANAGER_CONTAINER_ENVAR_NAME,
                                              RED,
                                              GREEN,
                                              YELLOW,
                                              BLUE,
                                              PINK,
                                              CYAN,
                                              RESET,
                                              BOLD,
                                              UNDERLINE)
from ecosystem_tests.dorkl.exceptions import (EcosystemTimeout,
                                              EcosystemTestException)
from ecosystem_cicd_tools.validations import validate_plugin_version

DEFAULT_COLOR = os.environ.get('DEFAULT_WORKFLOW_COLOR', BOLD)


def handle_process(command,
                   timeout=TIMEOUT,
                   log=True,
                   detach=False,
                   stdout_color=DEFAULT_COLOR):
    file_obj_stdout = NamedTemporaryFile(delete=False)
    file_obj_stderr = NamedTemporaryFile(delete=False)
    stdout_file = open(file_obj_stdout.name, 'w')
    stdout_file_read = open(file_obj_stdout.name, 'r')
    stderr_file = open(file_obj_stderr.name, 'w')
    stderr_file_read = open(file_obj_stderr.name, 'r')

    popen_args = {
        'args': split(command),
        'stdout': stdout_file,
        'stderr': stderr_file,
    }

    def dump_command_output():
        if log:
            stdout_file.flush()
            for stdout_line in stdout_file_read.readlines():
                logger.info(stdout_color +
                            'Execution output: {0}'.format(stdout_line) +
                            RESET)
            stderr_file.flush()
            for stderr_line in stderr_file_read.readlines():
                logger.error(RED +
                             'Execution error: {0}'.format(stderr_line) +
                             RESET)

    def return_parsable_output():
        stdout_file.flush()
        with open(file_obj_stdout.name, 'r') as fout:
            return '\n'.join(fout.readlines())

    if log:
        logger.info('Executing command {0}...'.format(command))
    time_started = datetime.now()
    p = subprocess.Popen(**popen_args)

    if detach:
        return p

    n = 2000.0
    i = 1
    with tqdm(desc='command', total=n) as pbar:
        while p.poll() is None:
            if log:
                pbar.update((datetime.now() - time_started).total_seconds())
                # gger.info('Command {0} still executing...'.format(command))
                dump_command_output()
            if datetime.now() - time_started > timedelta(seconds=timeout):
                raise EcosystemTimeout('The timeout was reached.')
            sleep(2)

        pbar.refresh()
        pbar.update(n-pbar.n)
        sleep(0.1)
        pbar.close()
        dump_command_output()

    if log:
        logger.info('Command finished {0}...'.format(command))

    if p.returncode:
        dump_command_output()
        raise EcosystemTestException('Command failed.'.format(p.returncode))

    if log:
        logger.info('Command succeeded {0}...'.format(command))

    return return_parsable_output()


def docker_exec(cmd,
                timeout=TIMEOUT,
                log=True,
                detach=False,
                stdout_color=DEFAULT_COLOR):
    """
    Execute command on the docker container.
    :param cmd: The command.
    :param timeout: How long to permit the process to run.
    :param log: Whether to log stdout or not.
    :param detach: Allow the process to block other functions.
    :param stdout_color: Defines the default stdout output color.
    :return: The command output.
    """

    container_name = get_manager_container_name()
    return handle_process(
        'docker exec {container_name} {cmd}'.format(
            container_name=container_name, cmd=cmd),
        timeout,
        log,
        detach,
        stdout_color)


def replace_file_on_manager(local_file_path, manager_file_path):
    """ Remove a file and upload a new one.

    :param local_file_path:
    :param manager_file_path:
    :return:
    """
    docker_path = copy_file_to_docker(local_file_path)
    if os.path.isdir(local_file_path):
        docker_exec('rm -rf {destination}'.format(
            destination=manager_file_path))
    docker_exec('mv {file} {destination}'.format(
        file=docker_path,
        destination=manager_file_path))


def replace_plugin_package_on_manager(package_name,
                                      plugin_version,
                                      directory,
                                      python_version='python3.6'):
    """Replace plugin code in the manager's path.

    Example usage: https://github.com/cloudify-cosmo/
    cloudify-vcloud-plugin/blob/75a9ab891edc249a7a7f82b0f855bd79fcd22d9e/
    cicd/update_test_manager.py#L8

    Then call the code like this: python .cicd/update_test_manager.py

    :param package_name: Name of a package.
    :param plugin_version: The plugin's version.
    :param directory:  The plugin's directory.
    :param python_version: The python version name.
    :return:
    """

    manager_package_path = \
        '/opt/mgmtworker/env/plugins/default_tenant/' \
        '{plugin}/{version}/lib/{python}/' \
        'site-packages/{package}'.format(
            package=package_name,
            version=plugin_version,
            python=python_version,
            plugin=os.path.basename(directory)
        )
    directory = posixpath.join(directory, package_name)
    if not os.path.exists(directory):
        raise Exception('No such file or directory {}'.format(directory))
    elif not os.path.isdir(directory):
        raise Exception('The directory provided {} is not a directory.'.format(
            directory))
    logger.info('Replacing {s} on manager {d}'.format(
        s=directory, d=manager_package_path))

    replace_file_on_manager(directory, manager_package_path)
    docker_exec('chown -R cfyuser:cfyuser {path}'.format(
        path=manager_package_path))


def update_plugin_on_manager(version_path, plugin_name, plugin_packages):
    version = validate_plugin_version(version_path)
    for package in plugin_packages:
        replace_plugin_package_on_manager(
            plugin_name, version, package, )


def copy_file_to_docker(local_file_path):
    """
    Copy a file from the container host to the container.
    :param local_file_path:  The local file path.
    :return: The remote path inside the container.
    """
    local_file_path = get_universal_path(local_file_path)
    docker_path = posixpath.join('/tmp/', os.path.basename(local_file_path))
    handle_process(
        'docker cp {0} {1}:{2}'.format(local_file_path,
                                       get_manager_container_name(),
                                       docker_path))
    return docker_path


def copy_file_from_docker(docker_file_path):
    local_file = NamedTemporaryFile()
    pure_windows = PureWindowsPath(local_file.name)
    if pure_windows.drive:
        local_file_path = pure_windows.as_posix().replace('C:', '')
    else:
        local_file_path = pure_windows.as_posix()
    handle_process(
        'docker cp {0}:{1} {2}'.format(get_manager_container_name(),
                                       docker_file_path,
                                       local_file_path))
    return local_file_path


def delete_file_from_docker(docker_path):
    docker_exec('rm -rf {destination}'.format(destination=docker_path))


def copy_directory_to_docker(local_file_path):
    """
    Copy a directory from the container host to the container.
    :param local_file_path:  The local directory path.
    :return: The remote path inside the container.
    """
    local_file_path = get_universal_path(local_file_path)
    local_dir = os.path.dirname(local_file_path)
    dir_name = os.path.basename(local_dir)
    remote_dir = PureWindowsPath(
        posixpath.join('/tmp', dir_name)).as_posix()
    try:
        handle_process(
            'docker cp {0} {1}:/tmp'.format(local_dir,
                                            get_manager_container_name()))
    except EcosystemTestException:
        pass
    return remote_dir


def cloudify_exec(cmd,
                  get_json=True,
                  timeout=TIMEOUT,
                  log=True,
                  detach=False,
                  stdout_color=DEFAULT_COLOR):
    """
    Execute a Cloudify CLI command inside the container.
    :param cmd: The command.
    :param get_json: Whether to return a JSON response or not.
    :param timeout: How long to allow the command to block other functions.
    :param log: Whether to log stdout or not.
    :param detach: To detach after executing
    :param stdout_color: Defines the default stdout output color.
    :return:
    """

    if get_json:
        json_output = docker_exec(
            '{0} --json'.format(cmd), timeout, log, detach, stdout_color)
        try:
            return json.loads(json_output)
        except (TypeError, ValueError):
            if log:
                logger.error(RED +
                             'JSON failed here: {0}'.format(json_output) +
                             RESET)
            return
    return docker_exec(cmd, timeout, log, detach, stdout_color)


def export_secret_to_environment(name):
    """
    Add secret to envvar.
    :param name: The secret key.
    :return:
    """
    logger.info('Adding envvar: {0}.'.format(name))
    try:
        value = base64.b64decode(os.environ[name])
    except KeyError:
        raise EcosystemTestException(
            'Secret env var not set {0}.'.format(name))
    if isinstance(value, bytes):
        value = value.decode(encoding='UTF-8')
    os.environ[name.upper()] = value


def get_manager_container_name():
    return os.environ.get(MANAGER_CONTAINER_ENVAR_NAME, 'cfy_manager')
