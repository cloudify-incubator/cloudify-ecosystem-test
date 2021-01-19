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
import json
import yaml
import base64
import logging
import subprocess
from time import sleep
from shlex import split
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from datetime import datetime, timedelta
try:
    from urllib.request import urlopen  # Python 3
except ImportError:
    from urllib2 import urlopen  # Python 2

from wagon import show

from ecosystem_cicd_tools.packaging import (
    get_workspace_files,
    find_wagon_local_path,
    get_bundle_from_workspace)
from ecosystem_cicd_tools.validations import validate_plugin_version

logging.basicConfig()
logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)

MANAGER_CONTAINER_NAME = os.environ.get('MANAGER_CONTAINER', 'cfy_manager')
TIMEOUT = 1800
VPN_CONFIG_PATH = '/tmp/vpn.conf'


class EcosystemTestException(Exception):
    pass


class EcosystemTimeout(Exception):
    pass


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


def use_cfy(timeout=60):
    """
    Initialize the Cloudify CLI profile inside the container.
    :param timeout:
    :return: Command output.
    """

    logger.info('Checking manager status.')
    start = datetime.now()
    # Give 10 sec of mercy for the container to boot
    sleep(10)
    while True:
        if datetime.now() - start > timedelta(seconds=timeout):
            raise EcosystemTestException('Fn use_cfy timed out.')
        try:
            output = cloudify_exec('cfy status', get_json=False)
            logger.info(output)
        except EcosystemTestException:
            sleep(10)
        logger.info('Manager is ready.')
        break


def license_upload():
    """
    Upload the license to the manager.
    :return: Command output.
    """

    logger.info('Uploading manager license.')
    try:
        license = base64.b64decode(os.environ['TEST_LICENSE'])
    except KeyError:
        raise EcosystemTestException('License env var not set {0}.')
    file_temp = NamedTemporaryFile(delete=False)
    with open(file_temp.name, 'wb') as outfile:
        outfile.write(license)
    return cloudify_exec('cfy license upload {0}'.format(
        copy_file_to_docker(file_temp.name)), get_json=False)


def plugin_already_uploaded(wagon_path):
    """
    Check if a plugin is already loaded on the manager.
    :param wagon_path: Path to a wagon.
    :return: Bool.
    """

    # It`s url
    if '://' in wagon_path:
        wagon_metadata = show(wagon_path)
    else:
        wagon_metadata = show(find_wagon_local_path(wagon_path))
    plugin_name = wagon_metadata["package_name"]
    plugin_version = wagon_metadata["package_version"]
    plugin_distribution = \
        wagon_metadata["build_server_os_properties"]["distribution"]
    for plugin in cloudify_exec('cfy plugins list'):
        logger.info('CHECKING if {0} {1} {2} in {3}'.format(
            plugin_name,
            plugin_version,
            plugin_distribution,
            plugin))
        compare_name = plugin['package_name']
        compare_version = plugin['package_version']
        compare_distro = plugin.get('distribution', '').lower() or \
            plugin.get('yaml_url_path', '')

        if plugin_name.replace('_', '-') in compare_name and \
                plugin_version == compare_version and \
                plugin_distribution.lower() in compare_distro:
            return True


def plugins_upload(wagon_path, yaml_path):
    """
    Upload a wagon and plugin YAML to the manager.
    :param wagon_path: Path to the wagon on the manager.
    :param yaml_path: Path to the YAML on the manager container.
    :return: Command output.
    """
    logger.info('Uploading plugin: {0} {1}'.format(wagon_path, yaml_path))
    if not plugin_already_uploaded(wagon_path):
        return cloudify_exec('cfy plugins upload {0} -y {1}'.format(
            wagon_path, yaml_path), get_json=False)


def get_test_plugins(workspace_path=None):
    """
    Find all wagons from the workspace (generated during previous build job)
    and return a tuple with the wagon path on the manager and the plugin
    YAML path on the manger.
    :return: list of tuples
    """

    plugin_yaml = copy_file_to_docker('plugin.yaml')
    return [(copy_file_to_docker(f), plugin_yaml) for f in
            get_workspace_files(workspace_path=workspace_path)
            if f.endswith('.wgn')]


def upload_test_plugins(plugins,
                        plugin_test,
                        execute_bundle_upload=True,
                        workspace_path=None):
    """
    Upload all plugins that we need to execute the test.
    :param plugins: A list of additional plugins to upload.
       (Like ones that are not in the bundle (Openstack 3, Host Pool).
    :param plugin_test: Whether to isntall plugins from workspace.
    :param execute_bundle_upload: Whether to install a bundle.
    :return:
    """

    plugins = plugins or []
    if plugin_test:
        for plugin_pair in get_test_plugins():
            plugins.append(plugin_pair)
    if execute_bundle_upload:
        bundle_path = get_bundle_from_workspace(workspace_path=workspace_path)
        if bundle_path:
            cloudify_exec(
                'cfy plugins bundle-upload --path {bundle_path}'.format(
                    bundle_path=copy_file_to_docker(bundle_path)),
                get_json=False)
        else:
            cloudify_exec(
                'cfy plugins bundle-upload', get_json=False)

    for plugin in plugins:
        sleep(3)
        output = plugins_upload(plugin[0], plugin[1])
        logger.info('Uploaded plugin: {0}'.format(output))
    logger.info('Plugins list: {0}'.format(
        cloudify_exec('cfy plugins list')))


def create_test_secrets(secrets=None):
    """
    Create secrets on the manager.
    :param secrets:
    :return:
    """

    secrets = secrets or {}
    for secret, f in secrets.items():
        secrets_create(secret, f)
    logger.info('Secrets list: {0}'.format(
        cloudify_exec('cfy secrets list')))


def prepare_test(plugins=None,
                 secrets=None,
                 plugin_test=False,
                 pip_packages=None,
                 yum_packages=None,
                 execute_bundle_upload=True,
                 use_vpn=False,
                 workspace_path=None):
    """
    Prepare the environment for executing a plugin test.



    :param plugins: A list of plugins to install. `plugin_test` must be True.
    :param secrets: A list of secrets to create.
    :param plugin_test: Do want to use wagons in the workspace for this test?
    :param pip_packages: A list of packages to install (on manger) with pip.
    :param yum_packages: A list of packages to install (on manger) with yum.
    :param execute_bundle_upload: Whether to upload the plugins bundle.
    :param use_vpn:
    :param workspace_path: THe path to the build directory if not circleci
    :return:
    """

    pip_packages = pip_packages or []
    yum_packages = yum_packages or []
    use_cfy()
    license_upload()
    upload_test_plugins(plugins,
                        plugin_test,
                        execute_bundle_upload,
                        workspace_path=workspace_path)
    create_test_secrets(secrets)
    yum_command = 'yum install -y python-netaddr git '
    if use_vpn:
        yum_packages.append('openvpn')
    if yum_packages:
        yum_command = yum_command + ' '.join(yum_packages)
    docker_exec(yum_command)
    pip_command = '/opt/mgmtworker/env/bin/pip install netaddr ipaddr '
    if pip_packages:
        pip_command = pip_command + ' '.join(pip_packages)
    docker_exec(pip_command)
    if use_vpn:
        value = base64.b64decode(os.environ['vpn_config'])
        file_temp = NamedTemporaryFile(delete=False)
        with open(file_temp.name, 'w') as outfile:
            outfile.write(value)
        docker_path = copy_file_to_docker(file_temp.name)
        docker_exec('mv {0} {1}'.format(docker_path, VPN_CONFIG_PATH))


def secrets_create(name, is_file=False):
    """
    Create a secret on the manager.
    :param name: The secret key.
    :param is_file: Whether to create the secret from a file.
    :return:
    """
    logger.info('Creating secret: {0}.'.format(name))
    try:
        value = base64.b64decode(os.environ[name])
    except KeyError:
        raise EcosystemTestException(
            'Secret env var not set {0}.'.format(name))
    if is_file:
        file_temp = NamedTemporaryFile(delete=False)
        with open(file_temp.name, 'wb') as outfile:
            outfile.write(value)
        return cloudify_exec('cfy secrets create -u {0} -f {1}'.format(
            name,
            copy_file_to_docker(file_temp.name)),
            get_json=False,
            log=False)
    return cloudify_exec('cfy secrets create -u {0} -s {1}'.format(
        name, value), get_json=False, log=False)


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


def blueprints_upload(blueprint_file_name, blueprint_id):
    """
    Upload a blueprint to the manager.
    :param blueprint_file_name:
    :param blueprint_id:
    :return:
    """
    remote_dir = copy_directory_to_docker(blueprint_file_name)
    blueprint_file = os.path.basename(blueprint_file_name)
    return cloudify_exec(
        'cfy blueprints upload {0} -b {1}'.format(
            os.path.join(remote_dir, blueprint_file),
            blueprint_id), get_json=False)


def blueprints_delete(blueprint_id):
    return cloudify_exec(
        'cfy blueprints delete {0}'.format(
            blueprint_id), get_json=False)


def deployments_create(blueprint_id, inputs):
    """
    Create a deployment on the manager.
    :param blueprint_id:
    :param inputs:
    :return:
    """
    try:
        os.path.isfile(inputs)
    except TypeError:
        archive_temp = NamedTemporaryFile(delete=False)
        with open(archive_temp.name, 'w') as outfile:
            yaml.dump(inputs, outfile, allow_unicode=True)
        inputs = archive_temp.name
    if inputs == '':
        return cloudify_exec('cfy deployments create -b {0}'.format(
            blueprint_id), get_json=False)
    return cloudify_exec('cfy deployments create -i {0} -b {1}'.format(
        inputs, blueprint_id), get_json=False)


def deployment_delete(blueprint_id):
    return cloudify_exec('cfy deployments delete {0}'.format(
        blueprint_id), get_json=False)


def get_deployment_outputs(deployment_id):
    logger.info('Getting deployment outputs {0}'.format(deployment_id))
    return cloudify_exec(
        'cfy deployments outputs --json {0}'.format(deployment_id))


def get_deployment_output_by_name(deployment_id, output_id):
    logger.info('Getting deployment output: {output_id}'.format(
        output_id=output_id))
    outputs = get_deployment_outputs(deployment_id)
    return outputs.get(output_id, {}).get('value')


def executions_start(workflow_id, deployment_id, timeout):
    """
    Start an execution on the manager.
    :param workflow_id:
    :param deployment_id:
    :param timeout:
    :return:
    """
    return cloudify_exec(
        'cfy executions start --timeout {0} -d {1} {2}'.format(
            timeout, deployment_id, workflow_id),
        get_json=False, timeout=timeout)


def executions_list(deployment_id):
    """
    List executions on the manager.
    :param deployment_id:
    :return:
    """
    return cloudify_exec('cfy executions list -d {0} '
                         '--include-system-workflows'.format(deployment_id))


def events_list(execution_id):
    """
    List events from an execution.
    :param execution_id:
    :return:
    """
    events = cloudify_exec('cfy events list {0}'.format(execution_id))
    if not events:
        return []
    return [json.loads(line) for line in events.split('\n') if line]


def log_events(execution_id):
    """
    Log events from execution.
    :param execution_id:
    :return:
    """
    for event in events_list(execution_id):
        if event['context']['task_error_causes']:
            logger.info(event['context']['task_error_causes'])


def wait_for_execution(deployment_id, workflow_id, timeout):
    """
    Wait for execution to end.
    :param deployment_id:
    :param workflow_id:
    :param timeout:
    :return:
    """
    logger.info('Waiting for execution deployment ID '
                '{0} workflow ID {1}'.format(deployment_id, workflow_id))
    start = datetime.now()
    while True:
        if datetime.now() - start > timedelta(seconds=timeout):
            raise EcosystemTimeout('Test timed out.')
        executions = executions_list(deployment_id)
        try:
            ex = [e for e in executions
                  if workflow_id == e['workflow_id']][0]
        except (IndexError, KeyError):
            raise EcosystemTestException(
                'Workflow {0} for deployment {1} was not found.'.format(
                    workflow_id, deployment_id))

        if ex['status'].lower() == 'completed':
            logger.info('{0}:{1} finished!'.format(deployment_id, workflow_id))
            break
        elif ex['status'].lower() == 'pending' or ex['status'] == 'started':
            logger.info('{0}:{1} is pending/started.'.format(
                deployment_id, workflow_id))
        elif ex['status'].lower() == 'failed':
            raise EcosystemTestException('Execution failed {0}:{1}'.format(
                deployment_id, workflow_id))
        else:
            logger.info(
                'Execution still running. Status: {0}'.format(ex['status']))
        sleep(5)


def verify_endpoint(endpoint, endpoint_value):
    logger.info('Checking Endpoint.')
    conn = urlopen(endpoint)
    if conn.getcode() == endpoint_value:
        logger.info('Endpoint up!')
        return
    raise EcosystemTestException(
        'Endpoint {e} not up {result}.'.format(
            e=endpoint, result=endpoint_value))


def cleanup_on_failure(deployment_id):
    """
    Execute uninstall if a deployment failed.
    :param deployment_id:
    :return:
    """
    try:
        executions_list(deployment_id)
    except EcosystemTestException:
        pass
    else:
        cloudify_exec(
            'cfy uninstall -p ignore_failure=true {0}'.format(
                deployment_id))


def _basic_blueprint_test(blueprint_file_name,
                          test_name,
                          inputs=None,
                          timeout=None,
                          endpoint_name=None,
                          endpoint_value=None):
    """
    Simple blueprint install/uninstall test.
    :param blueprint_file_name:
    :param test_name:
    :param inputs:
    :param timeout:
    :return:
    """

    timeout = timeout or TIMEOUT
    if inputs != '':
        inputs = inputs or os.path.join(
            os.path.dirname(blueprint_file_name), 'inputs/test-inputs.yaml')
    logger.info('Blueprints list: {0}'.format(
        cloudify_exec('cfy blueprints list')))
    blueprints_upload(blueprint_file_name, test_name)
    logger.info('Deployments list: {0}'.format(
        cloudify_exec('cfy deployments list')))
    deployments_create(test_name, inputs)
    sleep(5)
    logger.info('Installing...')
    try:
        executions_list(test_name)
        executions_start('install', test_name, timeout)
    except EcosystemTimeout:
        # Give 5 seconds grace.
        executions_list(test_name)
        wait_for_execution(test_name, 'install', 10)
    else:
        wait_for_execution(test_name, 'install', timeout)
    if endpoint_name and endpoint_value:
        verify_endpoint(
            get_deployment_output_by_name(
                test_name,
                endpoint_name
            ), endpoint_value)
    logger.info('Uninstalling...')
    executions_start('uninstall', test_name, timeout)
    wait_for_execution(test_name, 'uninstall', timeout)
    try:
        deployment_delete(test_name)
        blueprints_delete(test_name)
    except Exception as e:
        logger.info('Failed to delete blueprint, '
                    '{0}'.format(str(e)))


@contextmanager
def vpn():
    """Run tests while VPN is executing.
    Does not actually work in circle ci :("""
    logger.info('Starting VPN...')
    proc = docker_exec('openvpn {config_path}'.format(
        config_path=VPN_CONFIG_PATH), detach=True)
    # TODO: Find a way to poll the VPN without killing it. :(
    sleep(10)
    logger.info('VPN is supposed to be running...')
    try:
        yield proc
    except Exception as e:
        # TODO: Learn about potential Exceptions here.
        logger.info('VPN error {0}'.format(str(e)))
        pass
        # Apparently CircleCI does not support VPNs. !!!!
    finally:
        logger.info('Stopping VPN...')
        proc.terminate()


def basic_blueprint_test(blueprint_file_name,
                         test_name,
                         inputs=None,
                         timeout=None,
                         use_vpn=False,
                         endpoint_name=None,
                         endpoint_value=None):
    if use_vpn:
        with vpn():
            try:
                _basic_blueprint_test(blueprint_file_name,
                                      test_name,
                                      inputs,
                                      timeout,
                                      endpoint_name=endpoint_name,
                                      endpoint_value=endpoint_value)
            except:
                cleanup_on_failure(test_name)
    else:
        try:
            _basic_blueprint_test(blueprint_file_name,
                                  test_name,
                                  inputs,
                                  timeout,
                                  endpoint_name=endpoint_name,
                                  endpoint_value=endpoint_value)
        except Exception as e:
            logger.error('Error: {e}'.format(e=str(e)))
            cleanup_on_failure(test_name)
