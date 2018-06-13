import os
import requests
from random import randint, choice
import string
import subprocess
import sys
import yaml
import zipfile

from fabric import api as fabric_api

from cloudify_rest_client.client import CloudifyClient
from cloudify_rest_client.exceptions import CloudifyClientError

NODECELLAR = 'https://github.com/cloudify-examples/' \
             'nodecellar-auto-scale-auto-heal-blueprint' \
             '/archive/master.zip'


def execute_command_remotely(command, host_string, user, key_filename):
    print "Executing command `{0}`".format(command)
    connection = {
        'host_string': host_string,
        'user': user,
        'key_filename': key_filename
    }
    with fabric_api.settings(**connection):
        result = fabric_api.run(command)
        if result.failed:
            raise Exception(result)


def execute_command(command, return_output=False):
    print "Executing command `{0}`".format(command)
    process = subprocess.Popen(
        command.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    try:
        counter = 0
        while True:
            counter += 1
            if counter >= 10:
                # CircleCI times out after 10 minutes.
                # Normally this shouldn't be a problem.
                # But I am troubleshooting something.
                print '.'
                counter = 0
            out = process.stdout.read(1)
            if out == '' and process.poll() is not None:
                break
            sys.stdout.write(out)
            sys.stdout.flush()
    except ValueError:
        pass
    output, error = process.communicate()
    print "`{0}` output: {1}".format(command, output)
    if error:
        print "`{0}` output: {1}".format(command, error)
    if return_output:
        return output
    return process.returncode


def get_client_response(_client_name,
                        _client_attribute,
                        _client_args):

    client = CloudifyClient(
        host=os.environ['manager_test_ip'],
        username=os.environ.get(
            'manager_test_username', 'admin'),
        password=os.environ.get(
            'manager_test_password', 'admin'),
        tenant=os.environ.get(
            'manager_test_tenant', 'default_tenant'))

    _generic_client = \
        getattr(client, _client_name)

    _special_client = \
        getattr(_generic_client, _client_attribute)

    try:
        response = _special_client(**_client_args)
    except CloudifyClientError:
        raise
    else:
        return response


def create_password():
    characters = string.ascii_letters + string.digits
    password = "".join(
        choice(characters) for x in range(randint(8, 16)))
    return password


def initialize_cfy_profile(profile='local'):
    profile_command = 'cfy profiles use {0}'.format(profile)
    return execute_command(profile_command)


def upload_blueprint(
        archive, blueprint_id, blueprint_file):
    bluprint_command = 'cfy blueprints upload {0} -b {1} -n {2}'.format(
        archive, blueprint_id, blueprint_file)
    return execute_command(bluprint_command)


def create_deployment(blueprint_id, inputs=None):
    deploy_command = 'cfy deployments create -b {0}'.format(blueprint_id)
    if isinstance(inputs, dict) and len(inputs) > 0:
        deploy_command = '{0} -i {1}'.format(
            deploy_command,
            ' -i '.join('{0}={1}'.format(k, v) for (k, v) in inputs.items()))
    return execute_command(deploy_command)


def execute_install(deployment_id):
    install_command = \
        'cfy executions start install -vv --timeout 1800 -d {0}'.format(
            deployment_id)
    return execute_command(install_command)


def execute_scale(deployment_id, scalable_entity_name='nodejs_group'):
    scale_command = \
        'cfy executions start scale -vv --timeout 1800 -d {0} ' \
        '-p scalable_entity_name={1}'.format(
            deployment_id, scalable_entity_name)
    return execute_command(scale_command)


def execute_uninstall(deployment_id):
    uninstall_command = 'cfy executions start uninstall -vv -d {0}'.format(
        deployment_id)
    return execute_command(uninstall_command)


def install_nodecellar(blueprint_file_name, inputs=None):
    upload_blueprint(NODECELLAR, 'nc', blueprint_file_name)
    if not inputs:
        create_deployment('nc')
    else:
        create_deployment('nc', inputs=inputs)
    return execute_install('nc')


def get_node_instances(node_id):
    return get_client_response(
        'node_instances', 'list', {'node_id': node_id})


def get_nodes(deployment_id):
    return get_client_response(
        'nodes', 'list', {'deployment_id': deployment_id})


def get_deployment_resources_by_node_type_substring(
        deployment_id, node_type_substring,
        node_type_substring_exclusions):
    nodes_by_type = []
    for node in get_nodes(deployment_id):
        node_type = node.get('type')
        if node_type in node_type_substring_exclusions or \
                node_type_substring not in node_type:
            continue
        node_id = node.get('id')
        current_node = {
            'id': node_id,
            'type': node_type,
            'properties': node.get('properties'),
            'instances': []
        }
        for node_instance in get_node_instances(node_id):
            current_node_instance = {
                'id': node_instance.get('id'),
                'runtime_properties': node_instance.get(
                    'runtime_properties')
            }
            current_node['instances'].append(current_node_instance)
        nodes_by_type.append(current_node)
    return nodes_by_type


def get_deployment_resource_names(
        deployment_id, node_type_substring, name_property,
        node_type_substring_exclusions=None,
        external_resource_key='use_external_resource',
        resource_id_key='resource_id'):
    node_type_substring_exclusions = node_type_substring_exclusions or []
    names = []
    for node in get_deployment_resources_by_node_type_substring(
            deployment_id, node_type_substring,
            node_type_substring_exclusions):
        for instance in node['instances']:
            name = \
                instance['runtime_properties'].get(name_property)
            if not name and node['properties'][external_resource_key]:
                name = node['properties'][external_resource_key]
            names.append(instance['runtime_properties'][name_property])
    return names


def get_manager_ip(instances, manager_vm_node_id='cloudify_host'):
    for instance in instances:
        if manager_vm_node_id in instance.node_id:
            return instance.runtime_properties['public_ip']
    raise Exception('No manager IP found.')


def get_resource_ids_by_type(
        instances, node_type, get_function, id_property='name'):
    resources = []
    for instance in instances:
        node = get_function(instance.node_id)
        print 'Getting resource: {0}'.format(instance.node_id)
        if node_type not in node.type:
            break
        resource_id = instance.runtime_properties.get(id_property)
        if resource_id:
            resources.append(resource_id)
    return resources


def create_blueprint(
        blueprint_url, blueprint_zip, blueprint_dir, blueprint_path):
    r = requests.get(blueprint_url)
    with open(blueprint_zip, 'wb') as outfile:
        outfile.write(r.content)
    zip_ref = zipfile.ZipFile(blueprint_zip, 'r')
    zip_ref.extractall(blueprint_dir)
    zip_ref.close()
    return blueprint_path


def workflow_test_resources_to_copy(blueprint_dir):
    blueprint_resource_list = [
        (os.path.join(
           blueprint_dir,
           'cloudify-environment-setup-latest/imports/'
           'manager-configuration.yaml'),
         'imports/'),
        (os.path.join(
            blueprint_dir,
            'cloudify-environment-setup-latest/scripts/manager/tasks.py'),
         'scripts/manager/')
    ]
    return blueprint_resource_list


def update_plugin_yaml(
        commit_id, plugin_mapping, plugin_yaml_path='plugin.yaml'):
    with open(plugin_yaml_path, 'r') as infile:
        plugin_yaml = yaml.load(infile)
    try:
        old_filename = \
            plugin_yaml['plugins'][plugin_mapping]['source'].split(
                '/')[-1]
    except (KeyError, AttributeError, IndexError):
        raise
    plugin_yaml['plugins'][plugin_mapping]['source'] = \
        plugin_yaml['plugins'][plugin_mapping]['source'].replace(
            old_filename, '{0}.zip'.format(commit_id))
    with open(plugin_yaml_path, 'w') as outfile:
        yaml.dump(plugin_yaml, outfile, default_flow_style=False)


# I don't know what I was thinking.
# This wont work unless we build it on the manager's OS.
def create_wagon(ip, user, keypath, constraints=None):
    if constraints:
        with open('constraints.txt', 'w') as outfile:
            outfile.write(constraints)
        wagon_command = \
            "wagon create . --validate -v -f -a " \
            "'--no-cache-dir -c constraints.txt'"
    else:
        wagon_command = "wagon create -s . --validate -v -f"
    execute_command_remotely(wagon_command, ip, user, keypath)
    try:
        return [file for file in os.listdir('.') if file.endswith('.wgn')][0]
    except IndexError:
        raise


def upload_plugin(
        wagon_path, plugin_path='plugin.yaml',
        ip=None, user=None, keypath=None):
    upload_command = 'cfy plugins upload {0} -y {1}'.format(
        wagon_path, plugin_path)
    execute_command(upload_command)
    if ip and user and keypath:
        execute_command_remotely(upload_command)
