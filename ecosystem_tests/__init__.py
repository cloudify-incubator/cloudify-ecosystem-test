import os
import tempfile
import testtools
import re
import sys
from utils import initialize_cfy_profile, \
    create_password, create_blueprint
from cloudify.workflows.local import init_env
from cloudify.test_utils.local_workflow_decorator \
    import IGNORED_LOCAL_WORKFLOW_MODULES

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
            raise
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


class TestLocal(testtools.TestCase):

    def inputs():
        raise NotImplementedError(
            'Class create_inputs implemented by subclass.')

    def setup_cfy_local(self):
        blueprint_path = create_blueprint(
            self.blueprinturl, self.blueprint_zip,
            self.blueprintdir, self.blueprint_path)
        return init_env(
            blueprint_path,
            inputs=self.inputs(),
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)

    def setUp(self,
              blueprint_file_name,
              blueprint_archive='cloudify-environment-setup-latest',
              plugins_to_upload=None,
              package_url=None,
              sensitive_data=None):

        self.password = create_password()
        self.sensitive_data = sensitive_data or []
        self.sensitive_data.append(self.password)
        sys.stdout = PasswordFilter(self.sensitive_data, sys.stdout)
        sys.stderr = PasswordFilter(self.sensitive_data, sys.stderr)
        super(TestLocal, self).setUp()
        self.blueprinturl = 'https://github.com/cloudify-examples/' \
                            'cloudify-environment-setup/archive/latest.zip'
        self.blueprintdir = tempfile.mkdtemp()
        self.blueprint_zip = os.path.join(self.blueprintdir, 'blueprint.zip')
        self.blueprint_file_name = blueprint_file_name
        self.blueprint_archive = blueprint_archive
        self.blueprint_path = \
            os.path.join(
                self.blueprintdir,
                self.blueprint_archive,
                self.blueprint_file_name)
        self.package_url = package_url
        self.plugins_to_upload = \
            plugins_to_upload or [(DIAMOND_WAGON, DIAMOND_YAML)]
        self.cfy_local = self.setup_cfy_local()

    def execute_install(self):
        self.cfy_local.execute(
            'install',
            task_retries=45,
            task_retry_interval=10)
        self.node_instances = \
            self.cfy_local.storage.get_node_instances()

    def execute_uninstall(self):
        initialize_cfy_profile()
        self.cfy_local.execute(
            'uninstall',
            task_retries=45,
            task_retry_interval=10)
