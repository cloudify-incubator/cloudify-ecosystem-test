import os
import unittest

from .. import utils


class TestEcosytem(unittest.TestCase):

    def setUp(self):
        def create_environment_variables(additional_kvs=None):
            environment_vars = {
                'ECOSYSTEM_SESSION_MANAGER_IP': 'localhost',
                'ECOSYSTEM_SESSION_PASSWORD': 'password',
            }
            if additional_kvs:
                environment_vars.update(additional_kvs)
            for k, v in environment_vars.items():
                os.environ[k] = v
        create_environment_variables()

    @property
    def test_nodes(self):
        return ['node1', 'node2', 'node3']

    @property
    def deployment_nodes(self):
        data = [
            {
                'id': 'node2',
                'type': 'cloudify.nodes.Compute',
                'instances': [
                    {
                        'id': 'node2-1',
                        'runtime_properties': {
                            'external_id': 'node2-1'
                        }
                    }
                ]
            },
            {
                'id': 'node2',
                'type': 'cloudify.nodes.Root',
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
                'type': 'cloudify.nodes.Container',
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
            'inputs': {
                'input1': {
                    'type': 'string'
                },
            },
            'node_templates': {
                'node2': {
                    'properties': {
                        'resource_id': 'node2-1',
                        'use_external_resource': True,
                    },
                    'type': 'cloudify.nodes.Root'
                },
                'node3': {
                    'properties': {
                        'resource_id': 'node3-1',
                        'use_external_resource': True,
                    },
                    'type': 'cloudify.nodes.Container'
                },
            },
        }
        return data

    @property
    def blueprint_path(self):
        return os.path.join(
            os.path.dirname(__file__), 'resources', 'blueprint.yaml')

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
