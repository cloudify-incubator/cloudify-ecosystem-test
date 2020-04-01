
# Standard Imports
import os
import re
import sys
import shutil
import tempfile

# Third Parties Imports
import unittest
from cloudify.workflows.local import init_env, load_env, FileStorage
from cloudify.test_utils.local_workflow_decorator \
    import IGNORED_LOCAL_WORKFLOW_MODULES

# Local Imports
from utils import (
    initialize_cfy_profile,
    create_password,
    create_blueprint,
    execute_command,
    upload_plugins_utility)


IP_ADDRESS_REGEX = "(?:[0-9]{1,3}\.){3}[0-9]{1,3}"

CFY_LOCAL_FILE = 'test'


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


class EcosystemTestBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if 'ECOSYSTEM_SESSION_PASSWORD' not in os.environ:
            os.environ['ECOSYSTEM_SESSION_PASSWORD'] = create_password()

    @classmethod
    def tearDownClass(cls):
        cfy_storage = FileStorage(storage_dir=CFY_LOCAL_FILE)
        cfy_local = cls.load_cfy_local(cfy_storage)
        cls.uninstall_manager(cfy_local)
        shutil.rmtree(CFY_LOCAL_FILE)
        try:
            del os.environ['ECOSYSTEM_SESSION_MANAGER_IP']
            del os.environ['ECOSYSTEM_SESSION_LOADED']
            del os.environ['ECOSYSTEM_SESSION_PASSWORD']
            del os.environ['CLOUDIFY_STORAGE_DIR']
            del os.environ['ECOSYSTEM_SESSION_BLUEPRINT_DIR']
        except KeyError:
            pass

    def setUp(self):
        super(EcosystemTestBase, self).setUp()
        if self.password not in self.sensitive_data:
            self.sensitive_data.append(self.password)
        sys.stdout = PasswordFilter(self.sensitive_data, sys.stdout)
        sys.stderr = PasswordFilter(self.sensitive_data, sys.stderr)
        self.cfy_local = self.setup_cfy_local()
        if 'ECOSYSTEM_SESSION_MANAGER_IP' in os.environ:
            self.manager_ip = \
                os.environ['ECOSYSTEM_SESSION_MANAGER_IP']
        else:
            self.install_manager()
            self.initialize_manager_profile()
            self.upload_plugins()

    @staticmethod
    def load_cfy_local(_storage):
        return load_env(name='local', storage=_storage)

    @staticmethod
    def uninstall_manager(cfy_local):
        cfy_local.execute(
            'uninstall',
            task_retry_interval=15,
            parameters={'ignore_failure': 'true'})

    @property
    def password(self):
        return os.environ['ECOSYSTEM_SESSION_PASSWORD']

    @property
    def plugins_to_upload(self):
        """plugin yamls to upload to manager"""
        return []

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
        return 'cloudify-environment-setup-{0}'.format(
            self.manager_blueprint_version)

    @property
    def storage_dir(self):
        if 'CLOUDIFY_STORAGE_DIR' not in os.environ:
            cloudify_storage = tempfile.mkdtemp()
            os.environ['CLOUDIFY_STORAGE_DIR'] = cloudify_storage
        return os.environ['CLOUDIFY_STORAGE_DIR']

    @property
    def manager_blueprint_version(self):
        return 'latest'

    @property
    def blueprinturl(self):
        """URL to manager blueprint"""
        url = 'https://github.com/cloudify-examples/' \
              'cloudify-environment-setup/archive/{0}.zip'.format(
                  self.manager_blueprint_version)
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
    def application_prefix(self):
        """some prefix for appending to resource names"""
        if 'CIRCLE_BUILD_NUM' in os.environ:
            return os.environ['CIRCLE_BUILD_NUM']
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

        cfy_storage = FileStorage(storage_dir=CFY_LOCAL_FILE)
        if not os.environ.get('ECOSYSTEM_SESSION_LOADED', False) or not \
                os.path.exists(os.path.join(CFY_LOCAL_FILE, 'local/data')):
            os.environ['ECOSYSTEM_SESSION_LOADED'] = 'true'
            return init_env(
                os.path.join(
                    self.blueprint_dir,
                    self.blueprint_archive,
                    self.blueprint_file_name),
                inputs=self.inputs,
                storage=cfy_storage,
                ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)
        return self.load_cfy_local(cfy_storage)

    def install_manager(self):
        """install a cloudify manager using local profile

        :returns: nothing
        :rtype: NoneType
        """

        self.cfy_local.execute('install', task_retry_interval=15)
        self.node_instances = \
            self.cfy_local.storage.get_node_instances()
        ip = self.get_manager_ip()
        os.environ['ECOSYSTEM_SESSION_MANAGER_IP'] = ip
        self.manager_ip = ip

    def upload_plugins(self,
                       plugin_mapping=None,
                       application_prefix=None,
                       plugins_to_upload=None):
        """upload plugins after manager install

        :param plugin_mapping: the plugin mapping in plugin yaml
        :returns: nothing
        :rtype: NoneType
        """

        plugin_mapping = plugin_mapping or self.plugin_mapping
        application_prefix = application_prefix or self.application_prefix
        plugins_to_upload = plugins_to_upload or self.plugins_to_upload

        upload_plugins_utility(
            plugin_mapping, application_prefix, plugins_to_upload)

    def cleanup_deployment(self, deployment_id):
        """force uninstall deployment

        :param deployment_id: the deployment to uninstall
        :returns: nothing
        :rtype: NoneType
        """

        execute_command(
            'cfy executions start uninstall '
            '-p ignore_failure=true -d {0}'.format(
                deployment_id))

    def get_manager_ip(self):
        for instance in self.node_instances:
            if instance.node_id == self.server_ip_property:
                return instance.runtime_properties[self.external_id_key]
        raise Exception('No manager IP found.')
