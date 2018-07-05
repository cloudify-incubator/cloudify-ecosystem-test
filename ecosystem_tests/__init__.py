
# Standard Imports
import os
import sys
import re
import tempfile

# Third Parties Imports
import testtools
from cloudify.workflows.local import init_env, load_env, FileStorage
from cloudify.test_utils.local_workflow_decorator \
    import IGNORED_LOCAL_WORKFLOW_MODULES

# Local Imports
from utils import (
    initialize_cfy_profile,
    create_password,
    create_blueprint,
    get_resource_ids_by_type,
    get_wagon_path,
    update_plugin_yaml,
    upload_plugin,
    execute_command)


IP_ADDRESS_REGEX = "(?:[0-9]{1,3}\.){3}[0-9]{1,3}"
DIAMOND_WAGON = 'https://github.com/cloudify-cosmo/' \
                'cloudify-diamond-plugin/releases/' \
                'download/1.3.8/cloudify_diamond_plugin-' \
                '1.3.8-py27-none-linux_x86_64-centos-Core.wgn'
DIAMOND_YAML = 'https://github.com/cloudify-cosmo/' \
               'cloudify-diamond-plugin/releases/' \
               'download/1.3.8/plugin.yaml'


class PasswordFilter(object):
    """ Lifted from here: https://stackoverflow.com/a/42021966/5580340.
    """

    def __init__(self, strings_to_filter, stream):
        if not isinstance(strings_to_filter, list):
            raise Exception('strings_to_filter must be a list.')
        self.stream = stream
        strings_to_filter.append(IP_ADDRESS_REGEX)
        self.strings_to_filter = strings_to_filter

    def __getattr__(self, attr_name):
        return getattr(self.stream, attr_name)

    def write(self, data):
        for my_string in self.strings_to_filter:
            data = re.sub(
                r'\b{0}\b'.format(my_string), '*' * len(my_string), data)
        self.stream.write(data)
        self.stream.flush()

    def flush(self):
        self.stream.flush()


class EcosystemTestBase(testtools.TestCase):

    if 'ECOSYSTEM_SESSION_PASSWORD' not in os.environ:
        os.environ['ECOSYSTEM_SESSION_PASSWORD'] = create_password()
    password = os.environ['ECOSYSTEM_SESSION_PASSWORD']

    def setUp(self):
        if self.password not in self.sensitive_data:
            self.sensitive_data.append(self.password)
        sys.stdout = PasswordFilter(self.sensitive_data, sys.stdout)
        sys.stderr = PasswordFilter(self.sensitive_data, sys.stderr)
        super(EcosystemTestBase, self).setUp()
        if 'ECOSYSTEM_SESSION_MANAGER_IP' in os.environ:
            self.manager_ip = \
                os.environ['ECOSYSTEM_SESSION_MANAGER_IP']
        else:
            self.setup_cfy_local()
            self.install_manager()
            self.initialize_manager_profile()
            self.upload_plugins()

    def tearDown(self):
        super(EcosystemTestBase, self).tearDown()
        self.uninstall_manager()

    @property
    def plugins_to_upload(self):
        """plugin yamls to upload to manager"""
        return [(DIAMOND_WAGON, DIAMOND_YAML)]

    @property
    def sensitive_data(self):
        """list of strings to ignore"""
        raise NotImplementedError(
            'Property sensitive_data implemented by subclass.')

    @property
    def inputs(self):
        """manager blueprint inputs"""
        raise NotImplementedError(
            'Property inputs implemented by subclass.')

    @property
    def server_ip_property(self):
        """the node property for resource ID"""
        raise NotImplementedError(
            'Property server_ip_property implemented by subclass.')

    @property
    def external_id_key(self):
        """the runtime property for resource ID"""
        raise NotImplementedError(
            'Property external_id_key implemented by subclass.')

    @property
    def blueprint_archive(self):
        """name of the manager blueprint extracted file"""
        return 'cloudify-environment-setup-latest'

    @property
    def blueprinturl(self):
        """URL to manager blueprint"""
        url = 'https://github.com/cloudify-examples/' \
              'cloudify-environment-setup/archive/latest.zip'
        return url

    @property
    def blueprint_file_name(self):
        """string representing name of the file"""
        raise NotImplementedError(
            'Property blueprint_file_name implemented by subclass.')

    @property
    def plugin_mapping(self):
        """string representing the plugin mapping in plugin YAML"""
        raise NotImplementedError(
            'Property plugin_mapping implemented by subclass.')

    @property
    def blueprint_dir(self):
        """get the directory where the manager blueprint is initialize.
        :returns: path to the manager blueprint directory
        :rtype: string
        """

        # Create dir if it doesn't exist.
        if 'ECOSYSTEM_SESSION_BLUEPRINT_DIR' not in os.environ:
            blueprint_dir = tempfile.mkdtemp()
            # Create the local profile blueprint.
            create_blueprint(
                self.blueprinturl,
                os.path.join(
                    blueprint_dir,
                    'blueprint.zip'),
                blueprint_dir,
                os.path.join(
                    blueprint_dir,
                    self.blueprint_archive,
                    self.blueprint_file_name))
            os.environ['ECOSYSTEM_SESSION_BLUEPRINT_DIR'] = blueprint_dir
        return os.environ['ECOSYSTEM_SESSION_BLUEPRINT_DIR']

    @property
    def test_application_prefix(self):
        """some prefix for appending to resource names"""
        if 'CIRCLE_BUILD_NUM' in os.environ:
            return os.environ['os.environ']
        return os.environ.get('TEST_APPLICATION_PREFIX', '1234')

    def initialize_manager_profile(self, manager_ip=None, password=None):
        """initialize manager profile"""
        manager_ip = manager_ip or self.manager_ip
        password = password or self.password
        initialize_cfy_profile(
            '{0} -u admin -p {1} -t default_tenant'.format(
                manager_ip, password))

    def check_resource_method(self):
        """assert a resource status"""
        raise NotImplementedError(
            'Property check_resource_method implemented by subclass.')

    def setup_cfy_local(self):
        """initialize or load a local profile.
        :returns: return the local env
        :rtype: cloudify.workflows.local._Environment
        """

        cfy_storage = FileStorage()
        cfy_storage.__init__(self.blueprint_dir)
        if os.environ.get('ECOSYSTEM_SESSION_LOADED', False):
            return load_env(cfy_storage)
        else:
            cfy_local = init_env(
                os.path.join(
                    self.blueprint_dir,
                    self.blueprint_archive,
                    self.blueprint_file_name),
                inputs=self.inputs,
                storage=cfy_storage,
                ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)
            os.environ['ECOSYSTEM_SESSION_LOADED'] = 'true'
            return cfy_local

    def install_manager(self):
        """install a cloudify manager using local profile

        :returns: nothing
        :rtype: NoneType
        """

        self.addCleanup(self.uninstall_manager)
        self.cfy_local.execute(
            'install',
            task_retries=45,
            task_retry_interval=10)
        self.node_instances = \
            self.cfy_local.storage.get_node_instances()
        self.manager_ip = self.get_manager_ip()
        os.environ['BOOTSTRAPPED'] = 'true'
        self.check_manager_resources()

    def uninstall_manager(self):
        """uninstall a cloudify manager using local profile

        :returns: nothing
        :rtype: NoneType
        """

        if 'BOOTSTRAPPED' in os.environ:
            initialize_cfy_profile()
            self.cfy_local.execute(
                'uninstall',
                task_retries=45,
                task_retry_interval=10)
        del os.environ['ECOSYSTEM_SESSION_MANAGER_IP']

    def check_manager_resources(self,
                                node_type_prefix=None,
                                id_property=None,
                                check_resource_method=None):
        """get all resources and check they exist

        :param node_type_prefix: the node types of the plugin to check
        :param id_property: the property for resource ID
        :param check_resource_method: the method that checks resources
        :returns: nothing
        :rtype: NoneType
        """

        node_type_prefix = node_type_prefix or self.node_type_prefix
        id_property = id_property or self.id_property
        check_resource_method = \
            check_resource_method or self.check_resource_method

        for resource in get_resource_ids_by_type(
                self.node_instances,
                node_type_prefix,
                self.cfy_local.storage.get_node,
                id_property=id_property):
            check_resource_method(resource_id=resource)

    def upload_plugins(self, plugin_mapping=None):
        """upload plugins after manager install

        :param plugin_mapping: the plugin mapping in plugin yaml
        :returns: nothing
        :rtype: NoneType
        """

        plugin_mapping = plugin_mapping or self.plugin_mapping

        update_plugin_yaml(
            self.test_application_prefix,
            plugin_mapping)

        workspace_path = os.path.join(
            os.path.abspath('workspace'),
            'build')

        upload_plugin(get_wagon_path(workspace_path))

        for plugin in self.plugins_to_upload:
            upload_plugin(plugin[0], plugin[1])

    def cleanup_deployment(self, deployment_id):
        """force uninstall deployment

        :param deployment_id: the deployment to uninstall
        :returns: nothing
        :rtype: NoneType
        """

        execute_command(
            'cfy uninstall -p ignore_failure=true {0}'.format(
                deployment_id))

    def get_manager_ip(self):
        for instance in self.node_instances:
            if instance.node_id == self.server_ip_property:
                return instance.runtime_properties[self.external_id_key]
        raise Exception('No manager IP found.')
