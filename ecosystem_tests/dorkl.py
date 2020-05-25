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
from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile

from ecosystem_cicd_tools.packaging import get_workspace_files

logging.basicConfig(level=logging.INFO)
MANAGER_CONTAINER_NAME = 'cfy_manager'
TIMEOUT = 1800


class EcosystemTestException(Exception):
    pass


class EcosystemTimeout(Exception):
    pass


def dump_command_output(stdout_file, stderr_file):
    with open(stdout_file, 'r') as fout:
        for stdout_line in fout.readlines():
            logging.debug('STDOUT: {0}'.format(stdout_line))
    with open(stderr_file, 'r') as fout:
        for stderr_line in fout.readlines():
            logging.debug('STDERR: {0}'.format(stderr_line))


def return_parsable_output(stdout_file):
    with open(stdout_file, 'r') as fout:
        return '\n'.join(fout.readlines())


def handle_process(command, timeout=None):

    file_obj_stdout = NamedTemporaryFile(delete=False)
    file_obj_stderr = NamedTemporaryFile(delete=False)

    popen_args = {
        'args': command.split(),
        'stdout': open(file_obj_stdout.name, 'w'),
        'stderr': open(file_obj_stderr.name, 'w'),
    }

    logging.info('Executing command {0}...'.format(command))
    time_started = datetime.now()
    p = subprocess.Popen(**popen_args)

    while not p.poll():
        logging.info('Command {0} still executing...'.format(command))
        if datetime.now() - time_started > timedelta(seconds=timeout):
            p.terminate()
            p.stdout.close()
            p.stderr.close()
            dump_command_output(file_obj_stdout.name,
                                file_obj_stderr.name)
            raise EcosystemTimeout('The timeout was reached.')
        sleep(5)

    logging.info('Command finished {0}...'.format(command))

    if p.returncode:
        dump_command_output(file_obj_stdout.name,
                            file_obj_stderr.name)
        raise EcosystemTestException('Command failed.'.format(p.returncode))

    logging.info('Command succeeded {0}...'.format(command))

    return return_parsable_output(file_obj_stdout.name)


def docker_exec(cmd, timeout=TIMEOUT):
    container_name = os.environ.get(
        'DOCKER_CONTAINER_ID', MANAGER_CONTAINER_NAME)
    return handle_process(
        'docker exec {container_name} {cmd}'.format(
            container_name=container_name, cmd=cmd), timeout)


def copy_file_to_docker(local_file_path):
    docker_path = os.path.join('/tmp/', os.path.basename(local_file_path))
    handle_process(
        'docker cp {0} {1}:{2}'.format(local_file_path,
                                       MANAGER_CONTAINER_NAME,
                                       docker_path))
    return docker_path


def copy_directory_to_docker(local_file_path):
    local_dir = os.path.dirname(local_file_path)
    dir_name = os.path.basename(local_dir)
    remote_dir = os.path.join('/tmp', dir_name)
    try:
        handle_process(
            'docker cp {0} {1}:/tmp'.format(local_dir,
                                            MANAGER_CONTAINER_NAME))
    except subprocess.CalledProcessError:
        pass
    return remote_dir


def cloudify_exec(cmd, get_json=True, timeout=TIMEOUT):
    if get_json:
        json_output = docker_exec('{0} --json'.format(cmd), timeout)
        try:
            return json.loads(json_output)
        except (TypeError, ValueError):
            logging.error('JSON failed here: {0}'.format(json_output))
            return
    return docker_exec(cmd, timeout)


def use_cfy(timeout=60):
    logging.info('Checking manager status.')
    start = datetime.now()
    while True:
        if datetime.now() - start > timedelta(seconds=timeout):
            raise EcosystemTestException('Fn use_cfy timed out.')
        try:
            output = cloudify_exec('cfy status', get_json=False)
            logging.info(output)
        except subprocess.CalledProcessError:
            sleep(10)
        logging.info('Manager is ready.')
        break


def license_upload():
    logging.info('Uploading manager license.')
    try:
        license = base64.b64decode(os.environ['TEST_LICENSE'])
    except KeyError:
        raise EcosystemTestException('License env var not set {0}.')
    file_temp = NamedTemporaryFile(delete=False)
    with open(file_temp.name, 'w') as outfile:
        outfile.write(license)
    return cloudify_exec('cfy license upload {0}'.format(
        copy_file_to_docker(file_temp.name)), get_json=False)


def plugins_upload(wagon_path, yaml_path):
    logging.info('Uploading plugin: {0} {1}'.format(wagon_path, yaml_path))
    return cloudify_exec('cfy plugins upload {0} -y {1}'.format(
        wagon_path, yaml_path), get_json=False)


def get_test_plugins():
    plugin_yaml = copy_file_to_docker('plugin.yaml')
    return [(copy_file_to_docker(f), plugin_yaml) for f in
            get_workspace_files() if f.endswith('.wgn')]


def upload_test_plugins(plugins):
    plugins = plugins or []
    for plugin_pair in get_test_plugins():
        plugins.append(plugin_pair)
    cloudify_exec('cfy plugins bundle-upload', get_json=False)
    for plugin in plugins:
        sleep(2)
        output = plugins_upload(plugin[0], plugin[1])
        logging.info('Uploaded plugin: {0}'.format(output))


def create_test_secrets(secrets=None):
    secrets = secrets or {}
    for secret, f in secrets.items():
        secrets_create(secret, f)


def prepare_test(plugins=None, secrets=None):
    use_cfy()
    license_upload()
    upload_test_plugins(plugins)
    create_test_secrets(secrets)
    docker_exec('yum install -y python-netaddr git')
    docker_exec('/opt/mgmtworker/env/bin/pip install netaddr ipaddr')


def secrets_create(name, is_file=False):
    logging.info('creating secret: {0}.'.format(name))
    try:
        value = base64.b64decode(os.environ[name])
    except KeyError:
        raise EcosystemTestException(
            'Secret env var not set {0}.'.format(name))
    if is_file:
        file_temp = NamedTemporaryFile(delete=False)
        with open(file_temp.name, 'w') as outfile:
            outfile.write(value)
        return cloudify_exec('cfy secrets create -u {0} -f {1}'.format(
            name, copy_file_to_docker(file_temp.name)), get_json=False)
    return cloudify_exec('cfy secrets create -u {0} -s {1}'.format(
        name, value), get_json=False)


def blueprints_upload(blueprint_file_name, blueprint_id):
    remote_dir = copy_directory_to_docker(blueprint_file_name)
    blueprint_file = os.path.basename(blueprint_file_name)
    return cloudify_exec(
        'cfy blueprints upload {0} -b {1}'.format(
            os.path.join(remote_dir, blueprint_file),
            blueprint_id), get_json=False)


def deployments_create(blueprint_id, inputs):
    try:
        os.path.isfile(inputs)
    except TypeError:
        archive_temp = NamedTemporaryFile(delete=False)
        with open(archive_temp.name, 'w') as outfile:
            yaml.dump(inputs, outfile, allow_unicode=True)
        inputs = archive_temp.name
    return cloudify_exec('cfy deployments create -i {0} -b {1}'.format(
        inputs, blueprint_id), get_json=False)


def executions_start(workflow_id, deployment_id, timeout):
    return cloudify_exec(
        'cfy executions start --timeout {0} -d {1} {2}'.format(
            timeout, deployment_id, workflow_id),
        get_json=False, timeout=timeout)


def executions_list(deployment_id):
    return cloudify_exec('cfy executions list -d {0}'.format(deployment_id))


def events_list(events_id):
    events = cloudify_exec('cfy events list {0}'.format(events_id))
    if not events:
        return []
    return [json.loads(line) for line in events.split('\n') if line]


def log_events(events_id):
    for event in events_list(events_id):
        if event['context']['task_error_causes']:
            logging.info(event['context']['task_error_causes'])


def wait_for_execution(deployment_id, workflow_id, timeout):
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

        if ex['status'] == 'completed':
            logging.info('{0}:{1} finished!'.format(
                deployment_id, workflow_id))
            break
        elif ex['status'] == 'pending' or ex['status'] == 'started':
            logging.info('{0}:{1} is pending/started.'.format(
                deployment_id, workflow_id))
        elif ex['status'] == 'failed':
            raise EcosystemTestException('Execution failed {0}:{1}'.format(
                deployment_id, workflow_id))
        sleep(5)


def cleanup_on_failure(deployment_id):
    try:
        executions_list(deployment_id)
    except EcosystemTestException:
        pass
    else:
        cloudify_exec(
            'cfy uninstall -f -p ignore_failure=true {0}'.format(
                deployment_id))


def basic_blueprint_test(blueprint_file_name,
                         test_name,
                         inputs=None,
                         timeout=None):
    timeout = timeout or TIMEOUT
    inputs = inputs or os.path.join(
        os.path.dirname(blueprint_file_name), 'inputs/test-inputs.yaml')
    blueprints_upload(blueprint_file_name, test_name)
    deployments_create(test_name, inputs)
    sleep(5)
    logging.info('Installing...')
    try:
        executions_start('install', test_name, timeout)
    except EcosystemTimeout:
        # Give 5 seconds grace.
        wait_for_execution(test_name, 'install', 10)
    else:
        wait_for_execution(test_name, 'install', timeout)
    logging.info('Uninstalling...')
    executions_start('uninstall', test_name, timeout)
    wait_for_execution(test_name, 'uninstall', timeout)
