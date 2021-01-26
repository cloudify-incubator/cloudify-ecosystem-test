import os
import json
import base64
import subprocess
from time import sleep
from shlex import split
from tempfile import NamedTemporaryFile
from datetime import datetime, timedelta

from constansts import TIMEOUT, MANAGER_CONTAINER_NAME
from . import (logger,
               EcosystemTimeout,
               EcosystemTestException)
from ecosystem_cicd_tools.validations import validate_plugin_version


def handle_process(command, timeout=TIMEOUT, log=True, detach=False):
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
                logger.info('Execution output: {0}'.format(stdout_line))
            stderr_file.flush()
            for stderr_line in stderr_file_read.readlines():
                logger.error('Execution error: {0}'.format(stderr_line))

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

    while p.poll() is None:
        if log:
            logger.info('Command {0} still executing...'.format(command))
            dump_command_output()
        if datetime.now() - time_started > timedelta(seconds=timeout):
            raise EcosystemTimeout('The timeout was reached.')
        sleep(2)
    dump_command_output()

    if log:
        logger.info('Command finished {0}...'.format(command))

    if p.returncode:
        dump_command_output()
        raise EcosystemTestException('Command failed.'.format(p.returncode))

    if log:
        logger.info('Command succeeded {0}...'.format(command))

    return return_parsable_output()


def docker_exec(cmd, timeout=TIMEOUT, log=True, detach=False):
    """
    Execute command on the docker container.
    :param cmd: The command.
    :param timeout: How long to permit the process to run.
    :param log: Whether to log stdout or not.
    :param detach: Allow the process to block other functions.
    :return: The command output.
    """

    container_name = os.environ.get(
        'DOCKER_CONTAINER_ID', MANAGER_CONTAINER_NAME)
    return handle_process(
        'docker exec {container_name} {cmd}'.format(
            container_name=container_name, cmd=cmd), timeout, log, detach)


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


def replace_plugin_package_on_manager(plugin_name,
                                      plugin_version,
                                      package_name,
                                      python_version='python3.6'):
    """Replace plugin code in the manager's path.

    Example usage: https://github.com/cloudify-cosmo/
    cloudify-vcloud-plugin/blob/75a9ab891edc249a7a7f82b0f855bd79fcd22d9e/
    cicd/update_test_manager.py#L8

    Then call the code like this: python .cicd/update_test_manager.py

    :param plugin_name: Name of a plug in.
    :param plugin_version: The plug in's version.
    :param package_name:  The plug in's name.
    :param python_version: The python version name.
    :return:
    """

    manager_package_path = \
        '/opt/mgmtworker/env/plugins/default_tenant/' \
        '{plugin}/{version}/lib/{python}/' \
        'site-packages/{package}'.format(
            plugin=plugin_name,
            version=plugin_version,
            python=python_version,
            package=package_name.split('/')[-1]
        )
    logger.info('Replacing {s} on manager {d}'.format(
        s=package_name, d=manager_package_path))
    replace_file_on_manager(package_name, manager_package_path)
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

    docker_path = os.path.join('/tmp/', os.path.basename(local_file_path))
    handle_process(
        'docker cp {0} {1}:{2}'.format(local_file_path,
                                       MANAGER_CONTAINER_NAME,
                                       docker_path))
    return docker_path


def delete_file_from_docker(docker_path):
    docker_exec('rm -rf {destination}'.format(destination=docker_path))


def copy_directory_to_docker(local_file_path):
    """
    Copy a directory from the container host to the container.
    :param local_file_path:  The local directory path.
    :return: The remote path inside the container.
    """

    local_dir = os.path.dirname(local_file_path)
    dir_name = os.path.basename(local_dir)
    remote_dir = os.path.join('/tmp', dir_name)
    try:
        handle_process(
            'docker cp {0} {1}:/tmp'.format(local_dir,
                                            MANAGER_CONTAINER_NAME))
    except EcosystemTestException:
        pass
    return remote_dir


def cloudify_exec(cmd, get_json=True, timeout=TIMEOUT, log=True, detach=False):
    """
    Execute a Cloudify CLI command inside the container.
    :param cmd: The command.
    :param get_json: Whether to return a JSON response or not.
    :param timeout: How long to allow the command to block other functions.
    :param log: Whether to log stdout or not.
    :param detach: To detach after executing
    :return:
    """

    if get_json:
        json_output = docker_exec(
            '{0} --json'.format(cmd), timeout, log, detach)
        try:
            return json.loads(json_output)
        except (TypeError, ValueError):
            if log:
                logger.error('JSON failed here: {0}'.format(json_output))
            return
    return docker_exec(cmd, timeout, log, detach)


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
