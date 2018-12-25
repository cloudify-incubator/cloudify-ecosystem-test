import os
import requests
from random import randint, choice
import string
import subprocess
import sys
import time
import yaml
import zipfile

from cloudify_rest_client.client import CloudifyClient
from cloudify_rest_client.exceptions import CloudifyClientError

NODECELLAR = 'https://github.com/cloudify-examples/' \
             'nodecellar-auto-scale-auto-heal-blueprint' \
             '/archive/master.zip'


def execute_command(command, return_output=False, use_sudo=False):
    """execute some shell command

    :param command: the shell command to execute
    :param return_output: whether to return stdout instead of return code
    :param use_sudo: whether to add shell=True to Popen
    :type command: string
    :type return_output: string
    :type use_sudo: string
    :returns: returns the bash command return code or stdout
    :rtype: int or a string
    """

    print "Executing command `{0}`".format(command)
    process = subprocess.Popen(
        command.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=use_sudo)
    try:
        while True:
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
        print "`{0}` error: {1}".format(command, error)
    if return_output:
        return output
    return process.returncode


def get_client_response(_client_name,
                        _client_attribute,
                        _client_args):
    """request some Cloudify Client method

    :param _client_name: the name of the client such as `deployments`
    :param _client_attribute: the name of the method such as `list`
    :param _client_args: whatever keyword args to send to the client.
    :type _client_name: string
    :type _client_attribute: string
    :type _client_args: dict
    :returns: returns the request response
    :rtype: dict
    """

    client = CloudifyClient(
        host=os.environ['ECOSYSTEM_SESSION_MANAGER_IP'],
        username=os.environ.get(
            'ECOSYSTEM_SESSION_MANAGER_USER', 'admin'),
        password=os.environ.get(
            'ECOSYSTEM_SESSION_PASSWORD', 'admin'),
        tenant=os.environ.get(
            'ECOSYSTEM_SESSION_MANAGER_TENANT', 'default_tenant'))

    _generic_client = \
        getattr(client, _client_name)

    try:
        _client_attribute_left, _client_attribute_right = \
            _client_attribute.split('.')
    except ValueError:
        _special_client = \
            getattr(_generic_client, _client_attribute)
    else:
        _special_client = \
            getattr(_generic_client, _client_attribute_left)
        _special_client = \
            getattr(_special_client, _client_attribute_right)

    try:
        response = _special_client(**_client_args)
    except CloudifyClientError:
        raise
    else:
        return response


def create_password():
    """create a random string

    :returns: returns random numbers and letters
    :rtype: string
    """

    characters = string.ascii_letters + string.digits
    password = "".join(
        choice(characters) for x in range(randint(8, 16)))
    return password


def initialize_cfy_profile(profile='local'):
    """execute cfy profiles use

    :param profile: additional args to the `cfy profiles use` command
    :type profile: string
    :returns: returns the bash command return code
    :rtype: int
    """

    profile_command = 'cfy profiles use {0}'.format(profile)
    count = 0
    while True:
        failed = execute_command(profile_command)
        if not failed or count >= 10:
            return failed
        count += 1
        time.sleep(5)


def upload_blueprint(archive, blueprint_id, blueprint_file):
    """execute cfy blueprints upload create

    :param archive: the URL or path to a blueprint
    :param blueprint_id: the blueprint ID
    :param blueprint_file: the filename of the blueprint YAML
    :type archive: string
    :type blueprint_id: string
    :type blueprint_file: string
    :returns: returns the bash command return code
    :rtype: int
    """

    bluprint_command = 'cfy blueprints upload {0} -b {1} -n {2}'.format(
        archive, blueprint_id, blueprint_file)
    return execute_command(bluprint_command)


def create_deployment(blueprint_id, inputs=None):
    """execute cfy deployments create

    :param deployment_id: the deployment ID to create
    :param inputs: the deployment inputs
    :type deployment_id: string
    :type inputs: dict
    :returns: returns the bash command return code
    :rtype: int
    """

    deploy_command = 'cfy deployments create -b {0}'.format(blueprint_id)
    if isinstance(inputs, dict) and len(inputs) > 0:
        deploy_command = '{0} -i {1}'.format(
            deploy_command,
            ' -i '.join('{0}={1}'.format(k, v) for (k, v) in inputs.items()))
    return execute_command(deploy_command)


def execute_install(deployment_id):
    """execute cfy executions start install

    :param deployment_id: the deployment ID to install
    :type deployment_id: string
    :returns: returns the bash command return code
    :rtype: int
    """

    install_command = \
        'cfy executions start install -vv --timeout 1800 -d {0}'.format(
            deployment_id)
    return execute_command(install_command)


def execute_scale(deployment_id, scalable_entity_name='nodejs_group'):
    """execute cfy executions start scale

    :param deployment_id: the deployment ID to scale
    :param scalable_entity_name: the scale group node name to scale
    :type deployment_id: string
    :type scalable_entity_name: string
    :returns: returns the bash command return code
    :rtype: int
    """

    scale_command = \
        'cfy executions start scale -vv --timeout 1800 -d {0} ' \
        '-p scalable_entity_name={1}'.format(
            deployment_id, scalable_entity_name)
    return execute_command(scale_command)


def execute_uninstall(deployment_id):
    """execute cfy executions start uninstall

    :param deployment_id: the deployment ID to uninstall
    :type deployment_id: string
    :returns: returns the bash command return code
    :rtype: int
    """

    uninstall_command = 'cfy executions start uninstall -vv -d {0}'.format(
        deployment_id)
    return execute_command(uninstall_command)


def upload_plugin(wagon_path, plugin_yaml='plugin.yaml'):
    """execute cfy upload

    :param wagon_path: URL or file path to a wagon
    :param plugin_yaml: URL or file path to a plugin YAML
    :type wagon_path: string
    :type plugin_yaml: string
    :returns: returns the bash command return code
    :rtype: int
    """

    upload_command = 'cfy plugins upload {0} -y {1}'.format(
        wagon_path, plugin_yaml)
    return execute_command(upload_command)


def install_nodecellar(blueprint_file_name,
                       inputs=None,
                       blueprint_archive=NODECELLAR,
                       blueprint_id='nc'):
    """install the some blueprint example

    :param blueprint_file_name: the name of the archive filename
    :param inputs: deployment inputs
    :param blueprint_archive: URL of the blueprint
    :param blueprint_id: desired blueprint and deployment ID
    :type blueprint_file_name: string
    :type inputs: dict
    :type blueprint_archive: string
    :type blueprint_id: string
    :returns: returns the bash command return code
    :rtype: int
    """

    upload_blueprint(blueprint_archive, blueprint_id, blueprint_file_name)
    if not inputs:
        create_deployment(blueprint_id)
    else:
        create_deployment(blueprint_id, inputs=inputs)
    return execute_install(blueprint_id)


def get_node_instances(node_id, deployment_id):
    """get a list of node instances

    :param node_id: the node template name of your node instances
    :param deployment_id: the deployment ID of your node instances
    :type node_id: string
    :type deployment_id: string
    :returns: returns client response
    :rtype: cloudify_rest_client.responses.ListResponse
    """

    params = {'node_id': node_id}
    if deployment_id:
        params['deployment_id'] = deployment_id
    return get_client_response(
        'node_instances', 'list', params)


def get_nodes(deployment_id):
    """get a list of nodes

    :param deployment_id: the deployment ID of your node
    :type deployment_id: string
    :returns: returns client response
    :rtype: cloudify_rest_client.responses.ListResponse
    """

    return get_client_response(
        'nodes', 'list', {'deployment_id': deployment_id})


def get_deployment_outputs(deployment_id):
    """get a list of nodes

    :param deployment_id: the deployment ID of your node
    :type deployment_id: string
    :returns: returns client response
    :rtype: cloudify_rest_client.deployments.DeploymentOutputs
    """

    return get_client_response(
        'deployments', 'outputs.get', {'deployment_id': deployment_id})


def get_secrets(secret_name):
    """get a secret

    :param secret_name: the name of the secret
    :type secret_name: string
    :returns: returns client response
    :rtype: cloudify_rest_client.secrets.Secret
    """

    return get_client_response(
        'secrets', 'get', {'key': secret_name})


def get_deployment_resources_by_node_type_substring(
        deployment_id, node_type_substring,
        node_type_substring_exclusions=None):
    """get a list of nodes and their node instances

    We build a list of nodes with id, node_type, properties,
    and a list of node instances of that node. The node
    instances have the runtime properties of the node instance.

    **Example**

    Let's say that you have a blueprint with node1, node2,
    and node3. The nodes node1 and node2 have similar node types,
    like `cloudify.nodes.Custom` and `cloudify.nodes.Custom.Custom`.
    The node node3 has something different like
    `cloudify.nodes.Different`.

    You can filter out node3 by setting
    `node_type_substring='Custom' or by setting
    `node_type_substring_exclusions='node3'`.

    You'll end up with something like this:

    ```json
    [
        {
            'id': 'node1',
            'node_type': 'cloudify.nodes.Custom',
            'properties': {
                'prop1': 'prop1',
                'prop2': 'prop2'
            }
            'instances': [
                'id': 'node1-abcdefg',
                'runtime_properties': {
                    'attr1': 'attr1',
                    'attr2': 'attr2'
                },
                'id': 'node1-hijklmn',
                'runtime_properties': {
                    'attr1': 'attr1',
                    'attr2': 'attr2'
                }
            ]
        },
        {
            'id': 'node2',
            'node_type': 'cloudify.nodes.Custom.Custom',
            'properties': {
                'prop1': 'prop1',
                'prop2': 'prop2'
            }
            'instances': [
                'id': 'node2-abcdefg',
                'runtime_properties': {
                    'attr1': 'attr1',
                    'attr2': 'attr2'
                },
            ]
        },
    ]
    ```

    :param deployment_id: the deployment to get nodes from
    :param node_type_substring: substring of node type to get
    :param node_type_substring_exclusions: nodes to ignore
    :type deployment_id: string
    :type node_type_substring: string
    :type node_type_substring_exclusions: string
    :returns: returns list of nodes and their instances
    :rtype: list
    """

    nodes_by_type = []
    node_type_substring_exclusions = \
        node_type_substring_exclusions or []
    for node in get_nodes(deployment_id):
        node_type = node.get('type')
        if node_type in node_type_substring_exclusions or \
                node_type_substring not in node_type:
            continue
        node_id = node.get('id')
        print 'Creating a node dictionary for {0}'.format(node_id)
        current_node = {
            'id': node_id,
            'node_type': node_type,
            'properties': node.get('properties'),
            'relationships': node.get('relationships'),
            'instances': []
        }
        for node_instance in get_node_instances(
                node_id, deployment_id=deployment_id):
            node_instance_id = node_instance.get('id')
            print 'Creating a node-instance dictionary for {0}'.format(
                node_instance_id)
            current_node_instance = {
                'id': node_instance_id,
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
    """get a list of resource IDs in a particular deployment.

    Let's say that you installed a blueprint in Openstack and
    you want to get the IDs of all of the Openstack resources
    that you created. Your test can have something like this:

    utils.get_deployment_resource_names(
        my_openstack_deployment_id,
        'cloudify.openstack.nodes',
        ['cloudify.openstack.nodes.FakeType']
    )

    :param deployment_id: the deployment to resource IDs
    :param node_type_substring: substring of node type names for
    :param name_property: the runtime property key for resource ID
    :param node_type_substring_exclusions: nodes to ignore
    :param external_resource_key: the node property indicating
        an external resource
    :param resource_id_key: the node property indicating resource ID
    :type deployment_id: string
    :type node_type_substring: string
    :type name_property: string
    :type node_type_substring_exclusions: list
    :type external_resource_key: string
    :type resource_id_key: string
    :returns: returns list of nodes and their instances
    :rtype: list
    """

    node_type_substring_exclusions = node_type_substring_exclusions or []
    names = []
    for node in get_deployment_resources_by_node_type_substring(
            deployment_id, node_type_substring,
            node_type_substring_exclusions):
        print 'Getting {0} resource properties in {1}'.format(
            name_property, node)
        for instance in node['instances']:
            name = \
                instance['runtime_properties'].get(name_property)
            if not name and node['properties'][external_resource_key]:
                name = node['properties'][resource_id_key]
            names.append(name)
    return names


def get_resource_ids_by_type(
        instances, node_type, get_function, id_property='name'):
    """get resource IDs by node type

    This is really only used for local workflows.

    :param instances: a list of node instances
    :param node_type: the node type to filter by
    :param get_function: a function which gets nodes
    :param id_property: the runtime property for resource ID
    :type instances: list
    :type node_type: string
    :type get_function: method
    :type id_property: string

    :returns: returns list of resource IDs
    :rtype: list
    """

    resources = []
    for instance in instances:
        print 'Getting resource: {0}'.format(instance.node_id)
        node = get_function(instance.node_id)
        if node_type not in node.type:
            break
        resource_id = instance.runtime_properties.get(id_property)
        if resource_id:
            resources.append(resource_id)
    return resources


def download_file(url_path, file_path, filemode='wb'):
    """download some file to a path

    :param url_path: th URL to download
    :param file_path: path to save the file to
    :param filemode: which file mode to write `wb` or `w`.
    :type url_path: list
    :type file_path: string
    :type filemode: string

    :returns: returns nothing
    :rtype: NoneType
    """

    print "downloading with requests"
    response = requests.get(url_path)
    with open(file_path, filemode) as outfile:
        outfile.write(response.content)


def unzip_file(zip_path, out_dir):
    """unzip some file

    :param zip_path: the path to the zip
    :param out_dir: path to extract to
    :type zip_path: string
    :type out_dir: string

    :returns: returns nothing
    :rtype: NoneType
    """

    zip_ref = zipfile.ZipFile(zip_path, 'r')
    zip_ref.extractall(out_dir)
    zip_ref.close()


def create_blueprint(
        blueprint_url, blueprint_zip, blueprint_dir, blueprint_path):
    """download a blueprint archive

    :param blueprint_url: the URL of the blueprint zip
    :param blueprint_zip: file name to save the zip to
    :param blueprint_dir: the directory to unzip the zip into
    :param blueprint_path: the expected full path to blueprint YAML
    :type blueprint_url: string
    :type blueprint_zip: string
    :type blueprint_dir: string
    :type blueprint_path: string

    :returns: full path to the blueprint filename
    :rtype: string
    """

    download_file(blueprint_url, blueprint_zip)
    unzip_file(blueprint_zip, blueprint_dir)
    return blueprint_path


def read_blueprint_yaml(yaml_path):
    """read YAML file into YAML object

    :param yaml_path: path to a YAML file
    :type yaml_path: string

    :returns: the yaml
    :rtype: yaml
    """

    with open(yaml_path, 'r') as infile:
        return yaml.load(infile)


def write_blueprint_yaml(new_yaml, yaml_path):
    """write YAML object file into file

    :param new_yaml: YAML object
    :param yaml_path: path to write YAML into
    :type new_yaml: string
    :type yaml_path: string

    :returns: nothing
    :rtype: NoneType
    """

    with open(yaml_path, 'w') as outfile:
        yaml.dump(new_yaml, outfile, encoding=('utf-8'),
                  default_flow_style=False, allow_unicode=True)


def update_plugin_yaml(
        commit_id, plugin_mapping, plugin_yaml_path='plugin.yaml'):
    """update a plugin YAML source to point to current commit ID

    In our test, we want to make sure that we are testing the manager
    using a wagon of the current code. Since github caches archives
    we need to get the archive for the current commit.
    This method gets the plugin YAML and points its source to the
    current commit where we are running the test.

    :param commit_id: the commit ID of this tree
    :param plugin_mapping: the plugin name in the plugins dictionary
    :param plugin_yaml_path: where to read and save the new file to
    :type commit_id: string
    :type plugin_mapping: string
    :type plugin_yaml_path: string

    :returns: nothing
    :rtype: NoneType
    """

    plugin_yaml = read_blueprint_yaml(plugin_yaml_path)
    try:
        old_filename = \
            plugin_yaml['plugins'][plugin_mapping]['source'].split(
                '/')[-1]
    except (KeyError, AttributeError, IndexError):
        raise
    plugin_yaml['plugins'][plugin_mapping]['source'] = \
        plugin_yaml['plugins'][plugin_mapping]['source'].replace(
            old_filename, '{0}.zip'.format(commit_id))
    write_blueprint_yaml(plugin_yaml, plugin_yaml_path)


def get_wagon_path(workspace_path):
    """get the path to the current wagon

    We will build the wagon of the current code in a previous test job.
    We mount a folder containing the wagon in the test container.
    This is the path to the folder containing the wagon.
    There should be only one *.wgn file in that folder.

    :param workspace_path: the workspace path as attached in circle CI
    :type workspace_path: string

    :returns: nothing
    :rtype: NoneType
    """

    workspace_file_list = [file for file in os.listdir(workspace_path)
                           if file.endswith('.wgn')]
    try:
        filename = workspace_file_list[0]
    except IndexError:
        print 'Wagon does not exist in files: {0}'.format(
            workspace_file_list)
        raise
    return os.path.join(workspace_path, filename)


def check_deployment(blueprint_path,
                     blueprint_id,
                     node_type_substring,
                     nodes_to_check,
                     check_nodes_installed,
                     check_nodes_uninstalled):
    """executes several cfy commands then executes some functions.

    There is a basic pattern for testing a blueprint.
    First, upload, create, install. Then you want to get a list of
    nodes. Then you want to check that the nodes were really
    created. Then you want to uninstall. Then you want to check
    that the nodes were really removed. This method does all of that.

    :param blueprint_path: the path to the blueprint YAML
    :param blueprint_id: the human readable ID for the blueprint
        and deployment
    :param node_type_substring: the substring of node types to
        prepare for checking
    :param nodes_to_check: a list of nodes to check
    :param check_nodes_installed: a method that implements the
        how you want to check that the nodes were created
    :param check_nodes_uninstalled: a method that implements the
        how you want to check that the nodes were deleted
    :type blueprint_path: string
    :type blueprint_id: string
    :type node_type_substring: string
    :type nodes_to_check: list
    :type check_nodes_installed: function
    :type check_nodes_uninstalled: function
    :returns: returns nothing
    :rtype: None
    """

    install_command = 'cfy install {0} -b {1}'.format(
        blueprint_path, blueprint_id)
    failed = execute_command(install_command)
    if failed:
        raise Exception(
            'Install {0} failed.'.format(blueprint_id))
    deployment_nodes = \
        get_deployment_resources_by_node_type_substring(
            blueprint_id, node_type_substring)
    check_nodes_installed(deployment_nodes, nodes_to_check)
    failed = execute_uninstall(blueprint_id)
    if failed:
        raise Exception(
            'Uninstall {0} failed.'.format(blueprint_id))
    check_nodes_uninstalled(deployment_nodes, nodes_to_check)


def create_external_resource_blueprint(
        blueprint_path,
        nodes_to_use,
        deployment_nodes,
        external_resource_key='use_external_resource',
        resource_id_prop='resource_id',
        resource_id_attr='external_id',
        nodes_to_keep_without_transform=[]):
    """returns a file path to a modified blueprint

    We test that our IaaS plugins support existing resources.
    This function takes the path to an existing blueprint YAML
    and modifies the blueprint so that certain resources use
    existing resources.

    The intended use is two steps. First, install a regular blueprint.
    Then, modify that blueprint using this method.
    Then, install the modified blueprint.

    :param blueprint_path: the path to a blueprint yaml file
    :param nodes_to_use: a list of nodes from the blueprint to keep
    :param deployment_nodes: a list retrieve from
        get_deployment_resources_by_node_type_substring
    :param external_resource_key: the node property for the plugin
        that indicates an existing resource
    :param resource_id: the node property that indicates
        the resource's ID
    :param resource_id_attr: the instance runtime property that indicates
        the resource's ID
    :param nodes_to_keep_without_transform: nodes from nodes_to_use
        that should be kept from the blueprint, but not transformed
        into existing resources
    :returns: the path to the modified blueprint
    :rtype: string
    """

    blueprint_yaml = read_blueprint_yaml(blueprint_path)
    new_node_templates = {}
    for node in deployment_nodes:
        node_id = node['id'] if not isinstance(
            node['id'], unicode) else node['id'].encode('utf-8')
        node_definition = blueprint_yaml['node_templates'][node_id]
        if node_id not in nodes_to_use and node_id not in \
                nodes_to_keep_without_transform:
            continue
        external_id = \
            node['instances'][0]['runtime_properties'].get(
                resource_id_attr,
                node_definition['properties'].get(resource_id_prop))
        external_id = external_id if not isinstance(
            external_id, unicode) else external_id.encode('utf-8')
        if node_id not in nodes_to_keep_without_transform:
            node_definition = blueprint_yaml['node_templates'][node_id]
            node_definition['properties'][external_resource_key] = True
            node_definition['properties'][resource_id_prop] = external_id
        new_node_templates[node_id] = {
            'type': node_definition['type'],
            'properties': node_definition['properties']
        }
    blueprint_yaml['node_templates'] = new_node_templates
    for unneeded in ['outputs', 'groups', 'policies', 'description']:
        if unneeded in blueprint_yaml:
            del blueprint_yaml[unneeded]
    new_blueprint_path = '{0}-external.yaml'.format(
        blueprint_path.split('.yaml')[0])
    print "NEW YAML:\n{0}".format(blueprint_yaml)
    write_blueprint_yaml(blueprint_yaml, new_blueprint_path)
    return new_blueprint_path
