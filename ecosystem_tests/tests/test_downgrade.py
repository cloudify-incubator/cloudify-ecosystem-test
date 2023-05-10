
import os
import shutil
import tempfile
import unittest
from ..ecosystem_tests_cli.commands.downgrade_plugin_yaml import contexts  # noqa

PLUGIN_1_4 = """
plugins:

  foo:
    executor: central_deployment_agent
    package_name: cloudify-foo-plugin
    package_version: '10000.000111.1010101010101010101010'

data_types:

  bar:
    properties:
      baz:
        description: |
          this is foo
        type: node_instance
      qux:
        type: list
        item_type: dict

node_types:

  quxx:
    derived_from: corge
    properties:
      groult:
        type: node_id
      groult2:
        type: boolean
    interfaces:
      thud:
        create:
          implementation: taco
          inputs:
            bell:
              type: deployment_id

relationships:

  garply:
    derived_from: waldo
    source_interfaces:
      plugh:
        xyzzy:
          implementation: ~
          inputs:
            fred:
              type: blueprint_id
"""

PLUGIN_1_3 = """plugins:
  foo:
    executor: central_deployment_agent
    package_name: cloudify-foo-plugin
    package_version: 10000.000111.1010101010101010101010
data_types:
  bar:
    properties:
      baz:
        type: string
      qux:
        type: list
node_types:
  quxx:
    derived_from: corge
    properties:
      groult:
        type: string
      groult2:
        type: boolean
    interfaces:
      thud:
        create:
          implementation: taco
          inputs:
            bell:
              type: string
relationships:
  garply:
    derived_from: waldo
    source_interfaces:
      plugh:
        xyzzy:
          implementation: ~
          inputs:
            fred:
              type: string
"""


def tempdir_handler(fn):
    def inner_function(*args, **kwargs):
        tempdir = tempfile.mkdtemp()
        try:
            fn(tempdir, *args, **kwargs)
        finally:
            shutil.rmtree(tempdir)
    return inner_function


class TestDowngrade(unittest.TestCase):

    @tempdir_handler
    def test_file_context(tempdir, self, *_, **__):
        source_yaml = os.path.join(tempdir, 'plugin_1_4.yaml')
        try:
            contexts.FileContext(source_yaml, 'plugin.yaml')
        except SystemExit:
            # Good
            pass
        else:
            raise Exception(
                'Should have raised, '
                'because plugin_1_4.yaml does not exist.')

        with open(source_yaml, 'w') as f:
            f.write('\n')

        ctx = contexts.FileContext(source_yaml, 'plugin.yaml')

        self.assertTrue(ctx.path_object.exists())
        self.assertTrue(ctx.parent_path_object.exists())
        self.assertFalse(ctx.target_path_object.exists())

        ctx.target_path_object.touch()
        no_good = ctx.target_path_object.absolute()
        try:
            ctx = contexts.FileContext(
                source_yaml, 'plugin.yaml', False)
        except SystemExit:
            # Good
            pass
        else:
            raise Exception(
                'Should have raised, '
                'because {} does exists.'.format(no_good))

        ctx = contexts.FileContext(
            source_yaml, 'plugin.yaml', True)
        self.assertTrue(ctx.path_object.exists())
        self.assertTrue(ctx.parent_path_object.exists())
        self.assertFalse(ctx.target_path_object.exists())

    @tempdir_handler
    def test_main_context(tempdir, self, *_, **__):
        source_yaml = os.path.join(tempdir, 'plugin_1_4.yaml')
        with open(source_yaml, 'w') as f:
            f.write(PLUGIN_1_4)
        ctx = contexts.Context(
            source_yaml, '1.4', '1.3', False)
        ctx.full_downgrade()
        self.assertFalse(ctx.file.target_path_object.exists())
        ctx.create_new_plugin_yaml()
        self.assertTrue(ctx.file.target_path_object.exists())
        with open(ctx.file.target_path_object.absolute(), 'r') as f:
            self.maxDiff = None
            self.assertEqual(f.read(), PLUGIN_1_3)
