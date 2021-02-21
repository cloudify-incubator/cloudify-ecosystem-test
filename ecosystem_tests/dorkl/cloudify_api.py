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
import yaml
import base64
from time import sleep
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
from ecosystem_tests.dorkl.constansts import (logger,
                                              LICENSE_ENVAR_NAME)
from ecosystem_tests.dorkl.exceptions import (EcosystemTimeout,
                                              EcosystemTestException)
from ecosystem_tests.dorkl.commands import (cloudify_exec,
                                            copy_file_to_docker,
                                            delete_file_from_docker,
                                            copy_directory_to_docker)


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
        license = base64.b64decode(os.environ[LICENSE_ENVAR_NAME])
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
        compare_distro = plugin.get('distribution', '').lower() or plugin.get(
            'yaml_url_path', '')

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
    :param plugin_test: Whether to install plugins from workspace.
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


def secrets_create(name, is_file=False):
    """
    Create a secret on the manager.
    :param name: The secret key.
    :param is_file: Whether to create the secret from a file.
    :return:
    """
    logger.info('Creating secret: {0}.'.format(name))
    try:
        value = (base64.b64decode(os.environ[name].encode('utf-8'))).decode(
            'ascii')
    except KeyError:
        raise EcosystemTestException(
            'Secret env var not set {0}.'.format(name))
    if is_file:
        with NamedTemporaryFile(mode='w+', delete=True) as outfile:
            outfile.write(value)
            outfile.flush()
            cmd = 'cfy secrets create -u {0} -f {1}'.format(
                name,
                copy_file_to_docker(outfile.name))
            return cloudify_exec(cmd,
                                 get_json=False,
                                 log=False)

    return cloudify_exec('cfy secrets create -u {0} -s {1}'.format(
        name, value), get_json=False, log=False)


def blueprints_upload(blueprint_file_name, blueprint_id):
    """
    Upload a blueprint to the manager.
    :param blueprint_file_name:
    :param blueprint_id:
    :return:
    """
    if not os.path.isfile(blueprint_file_name):
        raise EcosystemTestException(
            'Cant upload blueprint {path} because the file doesn`t '
            'exists.'.format(path=blueprint_file_name))
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
    if not inputs:
        return cloudify_exec('cfy deployments create -b {0}'.format(
            blueprint_id), get_json=False)
    with prepare_inputs(inputs) as handled_inputs:
        return cloudify_exec('cfy deployments create -i {0} -b {1}'.format(
            handled_inputs, blueprint_id), get_json=False)


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


def get_blueprint_id_of_deployment(deployment_id):
    deployments_list = cloudify_exec('cfy deployments list')
    for deployment in deployments_list:
        if deployment['id'] == deployment_id:
            return deployment["blueprint_id"]


def executions_start(workflow_id, deployment_id, timeout, params=None):
    """
    Start an execution on the manager.
    :param workflow_id:
    :param deployment_id:
    :param timeout:
    :param params: Valid Parameters for the workflow (Can be provided as
    wildcard based paths (*.yaml, /my_inputs/,etc..) to YAML files,
     a JSON string or as 'key1=value1;key2=value2')
    :return:
    """
    cmd = 'cfy executions start --timeout {0} -d {1} {2}'
    if params:
        cmd = cmd + ' -p {params}'.format(params=params)
    return cloudify_exec(
        cmd.format(timeout, deployment_id, workflow_id),
        get_json=False, timeout=timeout)


def executions_resume(execution_id, timeout):
    """
    Resume an execution on the manager.
    :param execution_id:
    :param timeout:
    :return:
    """
    return cloudify_exec(
        'cfy executions resume {0}'.format(execution_id),
        get_json=False, timeout=timeout)


def executions_cancel(execution_id, timeout, force=False):
    """
    Cancel an execution on the manager.
    :param execution_id:
    :param timeout:
    :param force:
    :return:
    """
    cmd = 'cfy executions cancel {0}'
    if force:
        cmd = cmd + ' -f'

    return cloudify_exec(
        cmd.format(execution_id),
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
                  if workflow_id == e['workflow_id']][-1]
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


def deployment_update(deployment_id,
                      blueprint_id,
                      inputs,
                      timeout=None):
    """
    Perform deployment update.
    :param deployment_id:
    :param blueprint_id:  Id of the blueprint to update the deployment with,
     blueprint id of a blueprint that already exists in the system.
    :param inputs:
    :param timeout:

    """
    if not inputs:
        return cloudify_exec(
            'cfy deployments update {deployment_id} -b {blueprint_id}'.format(
                deployment_id=deployment_id, blueprint_id=blueprint_id),
            get_json=False, timeout=timeout)
    else:
        with prepare_inputs(inputs) as handled_inputs:
            return cloudify_exec(
                'cfy deployments update {deployment_id} -b {blueprint_id} -i {'
                'inputs}'.format(
                    deployment_id=deployment_id, blueprint_id=blueprint_id,
                    inputs=handled_inputs),
                get_json=False, timeout=timeout)


@contextmanager
def prepare_inputs(inputs):
    logger.info("Preparing inputs...")
    if not inputs:
        yield
    elif type(inputs) is dict:
        with NamedTemporaryFile(mode='w+', delete=False) as outfile:
            yaml.dump(inputs, outfile, allow_unicode=True)
            logger.debug(
                "temporary inputs file path {p}".format(p=outfile.name))
            inputs_on_docker = copy_file_to_docker(outfile.name)
            try:
                yield inputs_on_docker
            finally:
                delete_file_from_docker(inputs_on_docker)
    elif os.path.isfile(inputs):
        inputs_on_docker = copy_file_to_docker(inputs)
        try:
            yield inputs_on_docker
        finally:
            delete_file_from_docker(inputs_on_docker)
    else:
        # It's input string or None so yield it as is.
        yield inputs


def upload_test_plugins_dev(plugins,
                            execute_bundle_upload=True,
                            bundle_path=None):
    """
    Upload all plugins that we need to execute the test.
    :param plugins: A list of additional plugins to upload.
       (Like ones that are not in the bundle (Openstack 3, Host Pool).
    :param execute_bundle_upload: Whether to install a bundle.
    :param bundle_path: Path to plugins bundle.
    :return:
    """

    plugins = plugins or []
    bundle_path = bundle_path or ''
    if execute_bundle_upload:
        if os.path.isfile(bundle_path):
            logger.info("Using plugins bundle found at: {path}".format(
                path=bundle_path))
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


def cancel_multiple_executions(executions_lst, timeout, force):
    for execution_id in executions_lst:
        try:
            executions_cancel(execution_id, timeout, force=force)
        except (EcosystemTestException, EcosystemTimeout):
            raise EcosystemTestException(
                'Failed to cancel execution {id} please clean resources '
                'manually'.format(
                    id=execution_id))
        sleep(5)
