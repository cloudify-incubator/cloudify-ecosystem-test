import filecmp
import os
import tempfile
import unittest

from .. import utils

PROFILE = 'localhost -u admin -p admin -t default_tenant'
FAILED = 1  # Bash return code. Easier to read.
SUCCEED = 0  # Bash return code. Easier to read.
REPO_ARCHIVE = 'https://github.com/cloudify-incubator/' \
               'cloudify-ecosystem-test/archive/master.zip'
WAGON_URL = 'http://repository.cloudifysource.org/' \
            'cloudify/wagons/cloudify-openstack-plugin/2.9.2/' \
            'cloudify_openstack_plugin-2.9.2-py27-none-linux_' \
            'x86_64-centos-Core.wgn'
WAGON_YAML = 'http://www.getcloudify.org/spec/openstack-plugin/' \
             '2.9.2/plugin.yaml'


class TestEcosytem(unittest.TestCase):

    maxDiff = None  # This is for blueprint comparison.

    def setUp(self):
        def create_environment_variables(additional_kvs=None):
            environment_vars = {
                'ECOSYSTEM_SESSION_MANAGER_IP': 'localhost',
                'ECOSYSTEM_SESSION_PASSWORD': 'admin',
            }
            if additional_kvs:
                environment_vars.update(additional_kvs)
            for k, v in environment_vars.items():
                os.environ[k] = v
        create_environment_variables()
        try:
            utils.initialize_cfy_profile(PROFILE)
        except Exception:
            pass

    @property
    def test_nodes(self):
        return ['node1', 'node2', 'node3']

    @property
    def deployment_nodes(self):
        data = [
            {
                'id': 'node1',
                'type': 'cloudify.nodes.Compute',
                'properties': {
                    'agent_config': {
                        'install_method': 'none'
                    }
                },
                'instances': [
                    {
                        'id': 'node1-1',
                        'runtime_properties': {
                            'external_id': 'node1-1'
                        }
                    }
                ]
            },
            {
                'id': 'node2',
                'type': 'node2_type',
                'properties': {
                    'property1': 'property1'
                },
                'instances': [
                    {
                        'id': 'node2-1',
                        'runtime_properties': {
                            'external_id': 'node2-1'
                        }
                    },
                    {
                        'id': 'node2-2',
                        'runtime_properties': {
                            'external_id': 'node2-2'
                        }
                    }
                ]
            },
            {
                'id': 'node3',
                'type': 'cloudify.nodes.Root',
                'properties': {},
                'instances': [
                    {
                        'id': 'node3-1',
                        'runtime_properties': {
                            'external_id': 'node3-1'
                        }
                    }
                ]
            }
        ]
        return data

    @property
    def existing_blueprint_yaml(self):
        # If you changed "resources/blueprint.yaml", this won't work.
        data = {
            'tosca_definitions_version': 'cloudify_dsl_1_3',
            'imports': [
                'http://www.getcloudify.org/spec/cloudify/4.3.1/types.yaml'
            ],
            'node_types': {
                'node2_type': {
                    'derived_from': 'cloudify.nodes.Root',
                    'properties': {
                        'property1': {
                            'type': 'string'
                        }
                    }
                }
            },
            'inputs': {
                'input1': {
                    'type': 'string',
                    'default': 'input1'
                },
            },
            'node_templates': {
                'node1': {
                    'properties': {
                        'resource_id': 'node1-1',
                        'use_external_resource': True,
                        'agent_config': {
                            'install_method': 'none'
                        }
                    },
                    'type': 'cloudify.nodes.Compute'
                },
                'node2': {
                    'properties': {
                        'property1': 'property1',
                        'resource_id': 'node2-1',
                        'use_external_resource': True,
                    },
                    'type': 'node2_type'
                },
                'node3': {
                    'properties': {
                        'resource_id': 'node3-1',
                        'use_external_resource': True,
                    },
                    'type': 'cloudify.nodes.Root'
                },
            },
        }
        return data

    @property
    def blueprint_path(self):
        return os.path.join(
            os.path.dirname(__file__), 'resources', 'blueprint.yaml')

    @property
    def build_dir(self):
        workspace_dir = os.path.join(os.path.dirname(__file__), 'workspace')
        if not os.path.exists(workspace_dir):
            os.mkdir(workspace_dir)
        build_dir = os.path.join(workspace_dir, 'build')
        if not os.path.exists(build_dir):
            os.mkdir(build_dir)
        return build_dir

    @property
    def wagon_path(self):
        wagon_path = os.path.join(self.build_dir, 'file.wgn')
        if not os.path.exists(wagon_path):
            f = open(wagon_path, 'w')
            f.close()
        return wagon_path

    @property
    def deployment_outputs(self):
        return {'output1': 'output1'}

    @property
    def expected_plugin_yaml(self):
        data = {
            'plugins': {
                'plugin': {
                    'executor': 'central_deployment_agent',
                    'source': 'https://github.com/cloudify-incubator/'
                              'cloudify-ecosystem-tests/archive/1234.zip',
                    'package_name': 'example-plugin',
                    'package_version': '1'
                }
            }
        }
        return data

    def test_create_external_resource_blueprint(self):
        self.addCleanup(
            os.remove,
            '{0}-external.yaml'.format(
                self.blueprint_path.split('.yaml')[0]))
        updated_blueprint = utils.create_external_resource_blueprint(
            self.blueprint_path,
            self.test_nodes,
            self.deployment_nodes)
        self.assertEqual(
            utils.read_blueprint_yaml(updated_blueprint),
            self.existing_blueprint_yaml)

    def test_get_wagon_path(self):
        if not os.path.exists(self.wagon_path):
            f = open(self.wagon_path, 'w')
            f.close()
        wagon_path = utils.get_wagon_path(self.build_dir)
        self.assertEqual(self.wagon_path, wagon_path)

    def test_get_wagon_path_no_wagon(self):
        try:
            os.remove(self.wagon_path)
        except OSError:
            pass
        with self.assertRaises(IndexError):
            utils.get_wagon_path(self.build_dir)

    def check_get_node_instances(self,
                                 deployment_id='blueprint',
                                 node_id='node1',
                                 expected=1):
        response = utils.get_node_instances(node_id, deployment_id)
        self.assertTrue(len(response) == expected)

    def check_get_nodes(self,
                        deployment_id='blueprint',
                        expected=3):
        response = utils.get_nodes(deployment_id)
        self.assertTrue(len(response) == expected)

    def check_deployment_outputs(self, deployment_id='blueprint'):
        outputs = utils.get_deployment_outputs(deployment_id)
        self.assertEqual(
            self.deployment_outputs, outputs.get('outputs'))

    def check_secrets(self, secret):
        command = 'cfy secrets {0} -s {1}'.format(
            secret['key'], secret['value'])
        secret_create_failed = utils.execute_command(command)
        self.assertEqual(SUCCEED, secret_create_failed)
        response = utils.get_secrets(secret['key'])
        self.assertNotNone(response)

    def check_get_deployment_resources(self,
                                       deployment,
                                       substring,
                                       exclusions,
                                       expected=1):
        nodes = utils.get_deployment_resources_by_node_type_substring(
            deployment, substring, exclusions)
        self.assertTrue(len(nodes) == expected)
        self.assertTrue(len(nodes[0]['instances']) == expected)

    def test_blueprint_and_deployment(self):

        command = 'cfy blueprints upload {0} -b blueprint'.format(
            self.blueprint_path)
        blueprint_upload_failed = utils.execute_command(command)
        self.assertEqual(SUCCEED, blueprint_upload_failed)

        deployment_create_failed = utils.create_deployment(
            'blueprint', inputs={'input1': 'input1'})
        self.assertEqual(SUCCEED, deployment_create_failed)

        execute_install_failed = utils.execute_install(
            'blueprint')
        self.assertEqual(SUCCEED, execute_install_failed)

        self.check_deployment_outputs()
        self.check_get_nodes()
        self.check_get_node_instances()

        execute_scale_failed = utils.execute_scale(
            'blueprint', scalable_entity_name='node2')
        self.assertEqual(SUCCEED, execute_scale_failed)

        self.check_get_deployment_resources(
            'blueprint',
            'cloudify.nodes',
            'cloudify.nodes.Compute')

        execute_uninstall_failed = utils.execute_uninstall(
            'blueprint')
        self.assertEqual(SUCCEED, execute_uninstall_failed)

    def test_create_password(self):
        password = utils.create_password()
        self.assertTrue(isinstance(password, basestring))

    def test_blueprint_upload_url(self):
        upload_blueprint_failed = utils.upload_blueprint(
            REPO_ARCHIVE, 'blueprint-2',
            'ecosystem_tests/tests/resources/blueprint.yaml')
        self.assertEqual(SUCCEED, upload_blueprint_failed)

    def test_install_nodecellar(self):
        install_nodecellar = utils.install_nodecellar(
            'ecosystem_tests/tests/resources/blueprint.yaml',
            inputs={'input1': 'input1'},
            blueprint_archive=REPO_ARCHIVE,
            blueprint_id='blueprint-3')
        self.assertEqual(SUCCEED, install_nodecellar)

    def test_upload_plugin(self):
        upload_plugin = utils.upload_plugin(
            WAGON_URL, WAGON_YAML)
        self.assertEqual(SUCCEED, upload_plugin)

    def test_update_plugin_yaml(self):
        utils.update_plugin_yaml(
            '1234',
            'plugin',
            'ecosystem_tests/tests/resources/plugin.yaml')
        self.assertEqual(
            self.expected_plugin_yaml,
            utils.read_blueprint_yaml(
                'ecosystem_tests/tests/resources/plugin.yaml'))

    def test_create_blueprint(self):
        blueprint_dir = tempfile.mkdtemp()
        blueprint_zip = os.path.join(blueprint_dir, 'blueprint.zip')
        blueprint_archive = 'cloudify-ecosystem-test-master'
        download_path = \
            os.path.join(
                blueprint_dir,
                blueprint_archive,
                'ecosystem_tests/tests/resources/blueprint.yaml')
        blueprint_path = utils.create_blueprint(
            REPO_ARCHIVE,
            blueprint_zip,
            blueprint_dir,
            download_path)
        self.assertTrue(os.path.isfile(blueprint_path))
        self.assertTrue(filecmp.cmp(
            blueprint_path,
            'ecosystem_tests/tests/resources/blueprint.yaml'))

    def test_get_resource_ids_by_type(self):

        class test_get_resource_ids_by_type_instance(object):
            def __init__(self):
                self.node_id = 'instance'
                self.type = 'type'
                self.runtime_properties = {
                    'name': 'instance'
                }

        mock_instance = test_get_resource_ids_by_type_instance()

        def get_fn(_id):
            return mock_instance
        output = utils.get_resource_ids_by_type(
            [mock_instance],
            'type',
            get_fn)
        self.assertEqual(output, ['instance'])
        setattr(mock_instance, 'type', 'other')
        output = utils.get_resource_ids_by_type(
            [mock_instance],
            'type',
            get_fn)
        self.assertEqual(output, [])

    def test_check_deployment(self):

        def check_nodes(*_):
            pass

        utils.check_deployment(
            'ecosystem_tests/tests/resources/blueprint.yaml',
            'test-4',
            'cloudify.nodes',
            self.test_nodes,
            check_nodes,
            check_nodes)
