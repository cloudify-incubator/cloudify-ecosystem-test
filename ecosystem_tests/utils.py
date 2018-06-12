import os
import requests
from random import randint, choice
import string
import subprocess
import sys
import yaml
import zipfile

NODECELLAR = 'https://github.com/cloudify-examples/' \
             'nodecellar-auto-scale-auto-heal-blueprint' \
             '/archive/master.zip'


def execute_command(command):
    process = subprocess.Popen(
        command.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    try:
        while True:
            out = process.stdout.read(1)
            if out == '' and process.poll() is not None:
                break
            if out != '':
                sys.stdout.write(out)
                sys.stdout.flush()
    except ValueError:
        pass
    output, error = process.communicate()
    print "`{0}` output: {1}".format(command, output)
    if error:
        print "`{0}` output: {1}".format(command, error)
    return process.returncode


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
    install_command = 'cfy executions start install -d {0}'.format(
        deployment_id)
    return execute_command(install_command)


def execute_scale(deployment_id, scalable_entity_name='nodejs_group'):
    scale_command = \
        'cfy executions start scale -d {0} ' \
        '-p scalable_entity_name={1}'.format(
            deployment_id, scalable_entity_name)
    return execute_command(scale_command)


def execute_uninstall(deployment_id):
    uninstall_command = 'cfy executions start uninstall -d {0}'.format(
        deployment_id)
    return execute_command(uninstall_command)


def run_nodecellar(blueprint_file_name):
    upload_blueprint(NODECELLAR, 'nc', blueprint_file_name)
    create_deployment('nc')
    execute_install('nc')
    execute_scale('nc')
    execute_uninstall('nc')


def get_manager_ip(instances, manager_vm_node_id='cloudify_host'):
    for instance in instances:
        if manager_vm_node_id in instance.node_id:
            return instance.runtime_properties['public_ip']
    raise


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


def create_wagon(constraints=None):
    if constraints:
        with open('constraints', 'w') as outfile:
            outfile.write(constraints)
        wagon_command = \
            "wagon create -s . --validate -v -f -a " \
            "'--no-cache-dir -c ./constraints"
    else:
        wagon_command = "wagon create -s . --validate -v -f"
    execute_command(wagon_command)
    try:
        return [file for file in os.listdir('.') if file.endswith('.wgn')][0]
    except IndexError:
        raise


def upload_plugin(wagon_path, plugin_path='plugin.yaml'):
    upload_command = 'cfy plugins upload {0} -y {1}'.format(
        wagon_path, plugin_path)
    execute_command(upload_command)
