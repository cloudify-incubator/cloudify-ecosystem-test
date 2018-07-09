# cloudify-ecosystem-test

This is a basic set of tools to run integration tests for Cloudify plugins and blueprints.

We use it for workstation tests and on Circle CI.

## Creating Tests

In the repository that you want to test, add a test somewhere, like `./manager_tests/test_manager.py`.

Inside of that file, add a test class.

```python
from ecosystem_tests import EcosystemTestBase


class TestCloud(EcosystemTestBase):
```

There are several methods and properties that you need to implement if you intend to use them:

_Methods:_

  * `check_resource_method`: a method that can be used to check if a resource exists or not against your plugin.

_Example check_resource_method:_

In this example, we are running the Azure CLI command to see if a resource exists. A `0` return code indicates that no error was raised, meaning such a resource exists.

A `255` error code may indicate that the resource was not found.

```python
    def check_resource_method(self, resource_id, exists=0):
            list_resources = \
                'az resource list --name {0}'.format(resource_id)
            self.assertEqual(
                exists, utils.execute_command(list_resources))
```

_Properties:_

  * `sensitive_data`: a list of strings that you want to filter out of test stdout and stderr.
  * `node_type_prefix`: a substring of your plugin's node type, for example `cloudify.nodes.awssdk` or `cloudify.openstack.nodes`.
  * `plugin_mapping`: the plugin path that all operations include, for example `pkg` or `awssdk`.
  * `inputs`: the inputs for your manager installation.
  * `blueprint_file_name`: the blueprint filename in your manager installation blueprint, for example `blueprint.yaml` or `azure.yaml` or `sample.yaml`.
  * `external_id_key`: the runtime property that your plugin uses to save the unique ID in your IaaS plugin, for example `external_id` or `aws_resource_id` or `name`.
  * `server_ip_property`: the runtime property that you plugin uses to store the private IP address for a server in your IaaS.

_Example sensitive_data property:_

```python
    @property
    def sensitive_data(self):
        return [
            os.environ['AWS_SECRET_ACCESS_KEY'],
            os.environ['AWS_ACCESS_KEY_ID']
        ]
```

_Example inputs property:_

```python
    @property
    def inputs(self):
        try:
            return {
                'password': os.environ['ECOSYSTEM_SESSION_PASSWORD'],
                'ec2_region_name': 'eu-central-1',
                'ec2_region_endpoint': 'ec2.eu-central-1.amazonaws.com',
                'availability_zone': 'eu-central-1b',
                'aws_secret_access_key': os.environ['AWS_SECRET_ACCESS_KEY'],
                'aws_access_key_id': os.environ['AWS_ACCESS_KEY_ID']
            }
        except KeyError:
            raise
```

**Writing a Test**

When you write a test, you can write your own test methods or use the `check_deployment` method to use a generic test.

The `check_deployment` method installs a blueprint, checks for the state of certain resources, tears down the deployment, and then checks again that those resources were deleted.

This is useful if you have existing feature blueprints that you use in testing your features.

_Example check_deployment:_

```python

    def test_autoscaling(self):
        blueprint_path = 'examples/autoscaling-feature-demo/test.yaml'
        blueprint_id = 'autoscaling-{0}'.format(
            self.application_prefix)
        self.addCleanup(self.cleanup_deployment, blueprint_id)
        autoscaling_nodes = ['autoscaling_group']
        utils.check_deployment(
            blueprint_path,
            blueprint_id,
            self.node_type_prefix,
            autoscaling_nodes,
            self.check_resources_in_deployment_created,
            self.check_resources_in_deployment_deleted
        )
```

You can write your own test methods as well.

There are other tools in the Ecosystem test tools that you can use to make your tests more thorough, for example the `create_external_resource_blueprint` takes an existing blueprint and converts it to use external resources for certain nodes.

_Example create_external_resource_blueprint usage:_

This snippet is from a test using the Nodecellar example. Here we have already run the Nodecellar example, and we want to convert that blueprint to test that the same resources can be "externalized".

```python
# Nodes that we want to make external.
aws_nodes = [
    'security_group',
    'haproxy_nic',
    'nodejs_nic',
    'mongo_nic',
    'nodecellar_ip'
]
# Nodes that we do not want to make external
skip_transform = [
    'aws',
    'vpc',
    'public_subnet',
    'private_subnet',
    'ubuntu_trusty_ami'
]
new_blueprint_path = utils.create_external_resource_blueprint(
    blueprint_path,
    aws_nodes,
    deployment_nodes,  # All nodes to keep in the blueprint
    resource_id_attr='aws_resource_id',
    nodes_to_keep_without_transform=skip_transform)
failed = utils.execute_command(
    'cfy install {0} -b nc-external'.format(new_blueprint_path))
```

You can then run all whatever checks you want on the deployment.

## Using with CircleCI

Assuming you are testing a plugin on a Cloudify Manager, you need to build a wagon using the current code commit, and persist that wagon to the Cloudify Manager test:

```yaml
  wagon:
    docker:
      - image: amd64/centos:centos7.3.1611
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: yum -y install python-devel gcc openssl git libxslt-devel libxml2-devel openldap-devel libffi-devel openssl-devel libvirt-devel
      - run:
          name: Download pip
          command: curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
      - run:
          name: Install pip
          command: python get-pip.py
      - run:
          name: Upgrade pip
          command: pip install --upgrade pip==9.0.1
      - run:
          name: Install virtualenv
          command: pip install virtualenv
      - run:
          name: Init virtualenv
          command: virtualenv env
      - run:
          name: Install wagon
          command: pip install wagon==0.3.2
      - run:
          name: many_linux
          command: echo "manylinux1_compatible = False" > "env/bin/_manylinux.py"
      - run:
          name: make workspace
          command: mkdir -p workspace/build
      - run:
          name: Create wagon
          command: source env/bin/activate && wagon create -s . -v -o workspace/build -f -a '--no-cache-dir -c constraints.txt'
      - persist_to_workspace:
          root: workspace
          paths:
            - build/*
```

Your main job is the Cloudify Manager test.

This example shows how to prepare the test to "bootstrap" a manager using the Cloudify Environment Setup.

```yaml
  cloudify-manager:
    docker:
      - image: amd64/centos:centos7.3.1611
    steps:
      - checkout
      - attach_workspace:
          at: workspace
      - run:
          name: Install dependencies
          command: yum -y install python-devel gcc openssl git libxslt-devel libxml2-devel openldap-devel libffi-devel openssl-devel libvirt-devel
      - run:
          name: Download pip
          command: curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
      - run:
          name: Install pip
          command: python get-pip.py
      - run:
          name: Upgrade pip
          command: pip install --upgrade pip==9.0.1
      - run:
          name: Install virtualenv
          command: pip install virtualenv
      - run:
          name: Init virtualenv
          command: virtualenv env
      - run:
          name: install cloudify
          command: pip install cloudify==4.3.2
      - run:
          name: install openstack plugin from branch
          command: pip install -e .
      - run:
          name: install test requirements
          command: pip install awscli nose testtools https://github.com/cloudify-cosmo/cloudify-fabric-plugin/archive/1.5.1.zip https://github.com/cloudify-incubator/cloudify-utilities-plugin/archive/1.7.1.zip https://github.com/cloudify-incubator/cloudify-ecosystem-test/archive/2.0.zip
      - run:
          name: execute test
          command: nosetests -s manager_tests/test_awssdk.py
```

You can also use a Cloudify Manager Docker image:

```yaml
  cloudify-manager:
    machine:
      enabled: true
      python:
        version: pypy-2.2.1
    steps:
      - checkout
      - attach_workspace:
          at: workspace
      - run:
          name: download manager docker image
          command: wget http://repository.cloudifysource.org/cloudify/4.3.2/ga-release/cloudify-docker-manager-4.3.2ga.tar
      - run:
          name: load docker image
          command: docker load -i cloudify-docker-manager-4.3.2ga.tar
      - run:
          name: retain space by dumping the tar
          command: rm cloudify-docker-manager-4.3.2ga.tar
      - run:
          name: start docker container
          command: docker run --name cfy_manager -d --restart unless-stopped -v /sys/fs/cgroup:/sys/fs/cgroup:ro --tmpfs /run --tmpfs /run/lock --security-opt seccomp:unconfined --cap-add SYS_ADMIN --network host docker-cfy-manager:latest
      - run:
          name: install cloudify
          command: pip install cloudify==4.3.2
      - run:
          name: install utilities plugin from branch
          command: pip install -e .
      - run:
          name: init CLI profile
          command: cfy profiles use localhost -u admin -p admin -t default_tenant
      - run:
          name: install test requirements
          command: pip install nose testtools https://github.com/cloudify-incubator/cloudify-ecosystem-test/archive/2.0.zip
      - run:
          name: execute test
          command: nosetests -s manager_tests/test_utilities.py
```

You can configure CircleCI to run these tests only on build and master branches:

```yaml
workflows:
  version: 2
  tests:
    jobs:
      - unittests
      - wagon:
          filters:
            branches:
              only: /([0-9\.]*\-build|master|dev)/
      - cloudify-manager:
          context: ecosystem
          requires:
            - wagon
          filters:
            branches:
              only: /([0-9\.]*\-build|master|dev)/
```

## Running tests on your workstation

You can simulate how these tests will run in your build system, by executing them locally:

Steps:

  1. Build the wagon and put in a folder in your plugin called `workspace/build`. For example, I have `cloudify-awssdk-plugin/workspace/build/cloudify_awssdk_plugin-2.3.4-py27-none-linux_x86_64-centos-Core.wgn`.

  1. Export the credentials that you will need to your shell environment, `export MY_IAAS_PASSWORD=password` and `export MY_IAAS_USERNAME=username`.

  1. If you want to skip installation of your Cloudify Manager, just export the IP of your Cloudify Manager and connection credentials to the shell environment:

```bash
$ export ECOSYSTEM_SESSION_MANAGER_IP=127.0.0.1
$ export ECOSYSTEM_SESSION_MANAGER_USER=dev_john
$ export ECOSYSTEM_SESSION_PASSWORD=password
$ export ECOSYSTEM_SESSION_MANAGER_TENANT=development
```

Then you can execute your tests:

```bash
$ nosetests -s manager_tests/test_me.py`
```

**WARNING: Right now we don't revert changes that we do to the plugin YAML during test, so that's on you to make sure we don't trash the plugin YAML :)**
