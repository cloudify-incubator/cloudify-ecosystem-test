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
import re
import time
import shutil
import zipfile
import urllib3
import requests
import tempfile
import contextlib
from urllib.parse import urlparse

from ecosystem_tests.nerdl.utils import (
    zip_files,
    download_file,
    get_local_path,
    generate_progress_handler,
)
from ecosystem_tests.ecosystem_tests_cli.logger import logger
from cloudify_rest_client import (
    utils, exceptions, executions, CloudifyClient)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEP_CREATE = 'create_deployment_environment'
JIBBERISH = [
    'Creating node instance',
    'Node instance created',
    'Starting node instance',
    'Node instance started',
    'Subgraph started',
    'Subgraph succeeded',
    'Stopping node instance',
    'Stopped node instance',
    'Deleting node instance',
    'Deleted node instance',
]
PLUGIN_ID_EXC_REG = r'Plugin\sid=\`[A-Za-z0-9\-]{1,50}\`'


def with_client(func):
    """
    :param func: This is fn to be called.
    :return: a wrapper object encapsulating the invoked function
    """

    def wrapper_inner(*args, **kwargs):
        kwargs['client'] = CloudifyClient(**get_client_kwargs_from_env())
        return func(*args, **kwargs)
    return wrapper_inner


def get_client_kwargs_from_env():
    client_kwargs = {'protocol': 'https'}
    if 'CLOUDIFY_HOST' in os.environ:
        client_kwargs['host'] = os.environ['CLOUDIFY_HOST']
    if 'CLOUDIFY_TENANT' in os.environ:
        client_kwargs['tenant'] = os.environ['CLOUDIFY_TENANT']
    elif 'CIRCLE_PROJECT_REPONAME' in os.environ:
        client_kwargs['tenant'] = os.environ['CIRCLE_PROJECT_REPONAME']
    if 'CLOUDIFY_TOKEN' in os.environ:
        client_kwargs['token'] = os.environ['CLOUDIFY_TOKEN']
    if 'CLOUDIFY_CERTIFICATE' in os.environ and os.path.exists(
            os.environ['CLOUDIFY_CERTIFICATE']):
        client_kwargs['cert'] = os.environ['CLOUDIFY_CERTIFICATE']
    else:
        client_kwargs['trust_all'] = True
    return client_kwargs


@with_client
def list_blueprints(client):
    include = ['id', 'main_file_name', 'labels']
    for item in client.blueprints.list(_include=include):
        logger.info('Blueprint: {}'.format(item['id']))


@with_client
def list_deployments(client):
    for item in client.deployments.list(
            _include=['id', 'display_name', 'labels']):
        logger.info('Blueprint: {}:{}'.format(
            item['id'], item['display_name']))


@with_client
def list_nodes(deployment_id, client):
    return client.nodes.list(
        deployment_id=deployment_id,
        _node_id=['node_id'])


@with_client
def list_node_instances(deployment_id, client):
    return client.node_instances.list(
        deployment_id=deployment_id,
        _node_id=['node_id', 'id', 'state', 'runtime_properties'])


@with_client
def get_node_instance(node_instance_id, client):
    return client.node_instances.get(
        node_instance_id, _include=['id', 'state', 'runtime_properties'])


@with_client
def upload_blueprint(main_file_path, blueprint_id, client):
    logger.info('Uploading blueprint {}'.format(blueprint_id))
    client.blueprints.upload(
        main_file_path,
        blueprint_id,
        progress_callback=generate_progress_handler(main_file_path, ''),
    )
    timeout = 120
    start = time.time()
    while int(time.time() - start) < timeout:
        if blueprint_exists(blueprint_id):
            logger.info('Blueprint {} uploaded.'.format(blueprint_id))
            return
        time.sleep(5)
    logger.error('Failed to upload blueprint.')
    sys.exit(1)


@with_client
def delete_blueprint(blueprint_id, client):
    client.blueprints.delete(blueprint_id)
    timeout = 120
    start = time.time()
    while int(time.time() - start) < timeout:
        if not blueprint_exists(blueprint_id):
            logger.info('Blueprint {} deleted.'.format(blueprint_id))
            return
        time.sleep(5)
    logger.error('Failed to delete blueprint.')
    sys.exit(1)


@with_client
def create_deployment(blueprint_id, deployment_id, inputs, client):
    client.deployments.create(
        blueprint_id=blueprint_id,
        deployment_id=deployment_id,
        inputs=inputs,
        display_name=deployment_id
    )
    timeout = 120
    start = time.time()
    while int(time.time() - start) < timeout:
        if deployment_exists(deployment_id):
            logger.info('Deployment {} created.'.format(deployment_id))
            return
        time.sleep(5)
    logger.error('Failed to create deployment.')
    sys.exit(1)


@with_client
def update_deployment(deployment_id, update_id, inputs, client):
    client.deployment_updates.update_with_existing_blueprint(
        deployment_id, update_id, inputs)


def update_deployment_wrapper(main_file_name,
                              update_id,
                              inputs,
                              deployment_id):
    upload_blueprint(main_file_name, update_id)
    update_deployment(deployment_id, update_id, inputs)
    exec_id = get_execution(deployment_id, 'update')
    wait_for_execution(exec_id)


@with_client
def delete_deployment(deployment_id, client):
    client.deployments.delete(deployment_id)
    timeout = 120
    start = time.time()
    while int(time.time() - start) < timeout:
        if not deployment_exists(deployment_id):
            logger.info('Deployment {} deleted.'.format(deployment_id))
            return
        time.sleep(5)
    logger.error('Failed to delete deployment.')
    sys.exit(1)


@with_client
def start_execution(deployment_id, client, workflow, params=None):
    for execution in list_executions(deployment_id):
        if execution.get('status') not in executions.Execution.END_STATES:
            logger.error('Waiting for execution {} to finish.'.format(
                execution.get('id')))
            start = time.time()
            while int(time.time() - start) < 120:
                e = client.executions.get(
                    execution.get('id'),
                    _include=['status'])
                if e.get('status') in executions.Execution.END_STATES:
                    break
                time.sleep(5)
    logger.info('Starting {} {}.'.format(deployment_id, workflow))
    if params:
        return client.executions.start(
            deployment_id, workflow, parameters=params)
    else:
        return client.executions.start(deployment_id, workflow)


@with_client
def wait_for_execution(execution_id, client, timeout=1800):
    exec = client.executions.get(execution_id, _include=['status'])
    logger.info('Checking execution {} status: {}'.format(
        execution_id,
        exec.get('status')))
    total = 0
    start = time.time()
    while int(time.time() - start) < timeout:
        exec = client.executions.get(execution_id, _include=['status'])
        logger.info('Exec is {}'.format(exec))
        events, total = client.events.get(execution_id, total)
        for event in events:
            em = event.get('message', '')
            if any([em.startswith(s) for s in JIBBERISH]):
                continue
            message = '{}:{}:{}:{}'.format(
                event.get('deployment_id'),
                event.get('workflow_id'),
                event.get('node_name'),
                event.get('message')
            )
            error_causes = event.get('error_causes', [])
            if error_causes:
                message = '{}:{}'.format(
                    message, error_causes)
                logger.error(message)
                for cause in error_causes:
                    if cause.get('type') == 'NonRecoverableError' and \
                            exec.get('status') in executions.Execution.FAILED:
                        raise Exception('Execution {} failed....'.format(
                            execution_id))
            else:
                if 'nothing to do' not in message:
                    logger.info(message)

        if exec.get('status') in executions.Execution.END_STATES:
            if exec.get('status').lower() == executions.Execution.FAILED:
                raise Exception('Execution {} failed....'.format(
                    execution_id))
            logger.info('Workflow ID {} in state {}'.format(
                event.get('workflow_id'), exec.get('status')))
            return exec.get('status')
        time.sleep(5)
        # TODO: Add Logger Here.
    raise Exception(
        'Failed to verify execution {} '
        'completion in {} seconds.'.format(
            execution_id, timeout))


@with_client
def get_execution(deployment_id, workflow, client):
    executions = client.executions.list(
        deployment_id=deployment_id,
        workflow_id=workflow,
        sort='created_at',
        is_descending=True
    )
    if executions and len(executions) > 0:
        return executions[0].get('id')


@with_client
def list_executions(deployment_id, client):
    return client.executions.list(
        deployment_id=deployment_id,
        sort='created_at',
        is_descending=True,
        _include=['id', 'status']
    )


@with_client
def cancel_multiple_executions(executions, client):
    for execution in executions:
        try:
            client.executions.cancel(execution['id'])
        except exceptions.CloudifyClientError:
            pass


@with_client
def blueprint_exists(blueprint_id, client):
    try:
        result = client.blueprints.get(
            blueprint_id, _include=['id', 'state'])
        if 'id' not in result or result['id'] != blueprint_id:
            return False
        elif 'state' not in result or result['state'] != 'uploaded':
            return False
    except Exception as e:
        if '404' in str(e):
            return False
        raise e
    return True


@with_client
def deployment_exists(deployment_id, client):
    try:
        return client.deployments.get(deployment_id)
    except Exception as e:
        if '404' in str(e):
            return False
        else:
            raise e
    return True


def wait_for_deployment_create(deployment_id):
    execution_id = get_execution(deployment_id, DEP_CREATE)
    ready = wait_for_execution(execution_id)
    return execution_id, ready


def wait_for_install(deployment_id, timeout):
    return wait_for_workflow(deployment_id, 'install', timeout)


def wait_for_uninstall(deployment_id, timeout):
    return wait_for_workflow(deployment_id, 'uninstall', timeout)


def wait_for_workflow(deployment_id, workflow_id, timeout, params=None):
    execution = start_execution(
        deployment_id, workflow=workflow_id, params=params)
    ready = wait_for_execution(execution['id'], timeout=timeout)
    return execution['id'], ready


@with_client
def list_plugins(client):
    return client.plugins.list(
        _include=['id', 'package_name', 'package_version', 'distribution'])


@with_client
def delete_plugin(plugin_id, client):
    return client.plugins.delete(plugin_id)


def delete_plugins():
    for plugin in list_plugins():
        try:
            delete_plugin(plugin['id'])
        except Exception:
            pass


@with_client
def upload_plugin(plugin_path, yaml_paths, client):
    logger.info('Getting: {} {}'.format(plugin_path, yaml_paths))
    wagon_path = get_local_path(plugin_path, create_temp=True)
    yaml_path = get_local_path(yaml_paths, create_temp=True)
    zips = [wagon_path] + [yaml_path]
    zip_path = zip_files(zips)
    progress_handler = generate_progress_handler(zip_path, '')
    try:
        plugin = client.plugins.upload(
            zip_path,
            visibility='tenant',
            progress_callback=progress_handler)
        logger.info("Plugin uploaded. Plugin's id is %s", plugin.id)
    except exceptions.CloudifyClientError as e:
        if '409' in str(e):
            matches = re.search(PLUGIN_ID_EXC_REG, str(e))
            plugin = {
                'id': matches.group().split('`')[-2]
            }
            logger.error('Skipping plugin upload: {}'.format(e))
        else:
            raise e
    finally:
        for f in zips:
            os.remove(f)
            f_dir = os.path.dirname(f)
            if os.path.exists(f_dir) and os.path.isdir(f_dir):
                os.rmdir(f_dir)
        os.remove(zip_path)
    return plugin


@with_client
def create_secret(name, value=None, filepath=None, client=None):
    if filepath:
        with open(filepath, 'r') as f:
            value = f.read()
    return client.secrets.create(name, value, update_if_exists=True)


def cleanup_on_failure(deployment_id, timeout=1800):
    try:
        list_executions(deployment_id)
    except EcosystemTestException:
        pass
    else:
        wait_for_workflow(deployment_id, 'uninstall', timeout)
        delete_deployment(deployment_id)
        delete_blueprint(deployment_id)
        delete_plugins()


@with_client
def resume_execution(execution_id, timeout, client):
    client.executions.resume(execution_id)
    wait_for_execution(execution_id, timeout)


def resume_install_workflow(test_name, timeout):
    exec_id = get_execution(test_name, 'install')
    logger.debug('execution to resume: {id}'.format(id=exec_id))
    try:
        logger.info('resuming...')
        resume_execution(exec_id, timeout)
    except EcosystemTimeout:
        # Give 5 seconds grace.
        list_executions(test_name)
