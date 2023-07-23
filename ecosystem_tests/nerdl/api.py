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

from ecosystem_tests.nerdl.utils import (
    zip_files,
    download_file,
    get_local_path,
    generate_progress_handler,
)
from ecosystem_tests.ecosystem_tests_cli.logger import logger

from cloudify_rest_client import CloudifyClient

DEP_CREATE = 'create_deployment_environment'


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
    if 'CLOUDIFY_TOKEN' in os.environ:
        client_kwargs['token'] = os.environ['CLOUDIFY_TOKEN']
    if 'CLOUDIFY_CERTIFICATE' in os.environ and os.path.exists(
            os.environ['CLOUDIFY_CERTIFICATE']):
        client_kwargs['cert'] = os.environ['CLOUDIFY_CERTIFICATE']
    else:
        client_kwargs['trust_all'] = True
    return client_kwargs


@with_client
def upload_blueprint(main_file_path, blueprint_id, client):
    client.blueprints.upload(main_file_path, blueprint_id)


@with_client
def create_deployment(blueprint_id, deployment_id, inputs, client):
    client.deployments.create(
        blueprint_id=blueprint_id,
        deployment_id=deployment_id,
        inputs=inputs,
        display_name=deployment_id
    )


@with_client
def start_execution(deployment_id, client, workflow):
    return client.executions.start(deployment_id, workflow)


@with_client
def wait_for_execution(execution_id, client, timeout=1800):
    start = time.time()
    while int(time.time() - start) < timeout:
        exec = client.executions.get(execution_id, _include=['status'])
        if exec.get('status') in Execution.END_STATES:
            return True
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
def blueprint_exists(blueprint_id, client):
    try:
        result = client.blueprints.get(
            blueprint_id, _include=['id'])
        if 'id' not in result or result['id'] != blueprint_id:
            return False
    except Exception as e:
        if '404' in str(e):
            return False
        raise e
    return True


@with_client
def deployment_exists(deployment_id, client):
    try:
        client.deployments.get(deployment_id)
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


@with_client
def list_plugins(client):
    return client.plugins.list(
        _include=['id', 'package_name', 'package_version', 'distribution'])


@with_client
def delete_plugin(plugin_id, client):
    return client.plugins.delete(plugin_id)


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
            progress_callback=progress_handler)
        logger.info("Plugin uploaded. Plugin's id is %s", plugin.id)
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
        with open(filepath, 'w') as f:
            value = f.read()
    return client.secrets.create(name, value, update_if_exists=True)
