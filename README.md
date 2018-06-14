# cloudify-ecosystem-test

This is a basic set of utilities (and setup class) to run live tests on plugins and blueprints.

It is intended for use with Github and CircleCI. Although it should be easy to adapt it to some other build system like Jenkins.


## Usage

In the repository that you want to test, add a test somewhere, like `./manager_tests/test_manager.py`.

Inside of that file, add the test class.

```python
from ecosystem_tests import TestLocal, utils


class TestCloud(TestLocal):
    pass
```

By default, this blueprint installs a manager using the environment setup blueprint. (You can override that.) You need to implement the `inputs` function to provide the inputs to this blueprint.

```python
    def inputs(self):
        try:
            return {
                'username': os.environ['username'],
                'password': os.environ['password'],
            }
        except KeyError:
            raise
```

You also will need to override the setup method:

```python

    @classmethod
    def setUp(self):
        sensitive_data = [
            os.environ['CLOUD_USERNAME'],
            os.environ['CLOUD_PASSWORD'],
        ]
        super(TestCloud, self).setUp(
            'cloud.yaml', sensitive_data=sensitive_data)
        self.install_manager()
        self.manager_ip = utils.get_manager_ip(self.node_instances)

```

In the `sensitive_data` variable, provide any strings that you want to mask in the command output.

Make sure to provide the name of the blueprint in the environment setup that you want to install your manager with. (There is no file called `cloud.yaml`.)

Also, this function installs the manager.

Then add some tests:

```python
    def test_node_instances_after_setup(self):
    	""" Test that all cloudify.azure.nodes.* were created in Azure"""
        for resource in utils.get_resource_ids_by_type(
                self.node_instances,
                'cloudify.azure.nodes',
                self.cfy_local.storage.get_node):
            list_resources = 'az resource list --name {0}'.format(resource)
            self.assertEqual(0, utils.execute_command(list_resources))
```
