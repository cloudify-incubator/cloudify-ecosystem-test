# Cloudify Ecosystem Test

[![CircleCI](https://circleci.com/gh/cloudify-incubator/cloudify-ecosystem-test.svg?style=shield&circle-token=cad0039061d763209714b1728f4e28453e0c56a8)](https://circleci.com/gh/cloudify-incubator/cloudify-ecosystem-test)

This is the Cloudify Ecosystem CICD toolkit. These are testing tools for Cloudify. However, there is really more here. Also, you will find tools for building and packaging and publishing Cloudify Ecosystem assets.

1) Blueprint testing tools.
2) Plugin testing tools.
3) Plugin Bundle Packaging.
4) Plugin release to Github and S3.
5) Integration with an IDE.

You can use all of these tools on your laptop to develop, test, and release blueprints and plugins.

Finally, this toolkit is designed to be super easy to use! So you can probably get no sleep for days, and still be able to test your plugins!

## Requirements

* Cloudify Ecosystem Test. `pip install https://github.com/cloudify-incubator/cloudify-ecosystem-test/archive/latest.zip`
* Start a Cloudify Manager on your laptop with [Docker](https://docs.cloudify.co/latest/install_maintain/installation/manager-image/).
* A Cloudify License, if you are not using Cloudify Community.
* Any credentials that you need to authenticate with your Cloud provider API.
* Any Cloudify plugins that are not part of your build steps.

### Cloudify Manager Setup

Advanced users of the toolkit can automate Cloudify Manager setup using this toolkit. But I suggest for simple use cases that you use an already configured manager.

1) Upload your Cloudify license. `cfy license upload /home/user/path/to/license.yaml`
2) Upload your plugins. `cfy plugins bundle-upload`
3) Create your secrets. `cfy secrets create .... -s ######` or `cfy secrets create ..... -f /home/user/path/to/secret-file`


# Blueprint testing tools

Let's start with the blueprint print testing tools. Let's say that you have a blueprint. For example, our [Hello World Example](https://github.com/cloudify-community/blueprint-examples/tree/latest/hello-world-example).

Say you download that example into a new folder.

```bash
  ::  wget https://github.com/cloudify-community/blueprint-examples/releases/download/latest/hello-world-example.zip
--2020-12-10 09:39:31--  https://github.com/cloudify-community/blueprint-examples/releases/download/latest/hello-world-example.zip
Resolving github.com (github.com)... 140.82.121.4
Connecting to github.com (github.com)|140.82.121.4|:443... connected.
HTTP request sent, awaiting response... 302 Found
Location: https://github-production-release-asset-2e65be.s3.amazonaws.com/169957344/13935200-37f1-11eb-9bdd-7d00f4af162f?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIWNJYAX4CSVEH53A%2F20201210%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20201210T073931Z&X-Amz-Expires=300&X-Amz-Signature=e5a14bf9a51b1388e9bc82a0515437d192b317190ccf491132683943486218f9&X-Amz-SignedHeaders=host&actor_id=0&key_id=0&repo_id=169957344&response-content-disposition=attachment%3B%20filename%3Dhello-world-example.zip&response-content-type=application%2Foctet-stream [following]
--2020-12-10 09:39:32--  https://github-production-release-asset-2e65be.s3.amazonaws.com/169957344/13935200-37f1-11eb-9bdd-7d00f4af162f?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIWNJYAX4CSVEH53A%2F20201210%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20201210T073931Z&X-Amz-Expires=300&X-Amz-Signature=e5a14bf9a51b1388e9bc82a0515437d192b317190ccf491132683943486218f9&X-Amz-SignedHeaders=host&actor_id=0&key_id=0&repo_id=169957344&response-content-disposition=attachment%3B%20filename%3Dhello-world-example.zip&response-content-type=application%2Foctet-stream
Resolving github-production-release-asset-2e65be.s3.amazonaws.com (github-production-release-asset-2e65be.s3.amazonaws.com)... 52.217.90.28
Connecting to github-production-release-asset-2e65be.s3.amazonaws.com (github-production-release-asset-2e65be.s3.amazonaws.com)|52.217.90.28|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 84983 (83K) [application/octet-stream]
Saving to: ‘hello-world-example.zip’

hello-world-example.zip                                                        100%[===================================================================================================================================================================================================>]  82.99K   105KB/s    in 0.8s    

2020-12-10 09:39:33 (105 KB/s) - ‘hello-world-example.zip’ saved [84983/84983]
```

Now unzip the downloaded archive.

```bash
  ::  unzip hello-world-example.zip 
Archive:  hello-world-example.zip
 extracting: hello-world-example/openstack.yaml  
 extracting: hello-world-example/README.md  
 extracting: hello-world-example/gcp.yaml  
 extracting: hello-world-example/azure.yaml  
 extracting: hello-world-example/aws.yaml  
 extracting: hello-world-example/aws-terraform.yaml  
 extracting: hello-world-example/aws-cloudformation.yaml  
 extracting: hello-world-example/scripts/gcp/key.py  
 extracting: hello-world-example/scripts/terraform/inject_ip.py  
 extracting: hello-world-example/resources/terraform/template.zip  
 extracting: hello-world-example/resources/terraform/template/variables.tf  
 extracting: hello-world-example/resources/terraform/template/main.tf  
 extracting: hello-world-example/resources/cloudformation/template.yaml  
 extracting: hello-world-example/apache2/index2.html  
 extracting: hello-world-example/apache2/index.html  
 extracting: hello-world-example/apache2/playbook2.yaml  
 extracting: hello-world-example/apache2/cloudify-logo.png  
 extracting: hello-world-example/apache2/playbook.yaml  
 extracting: hello-world-example/apache2/vhost  
 extracting: hello-world-example/includes/ansible.yaml
```

In order to test one of these files, create a test.

```bash
  ::  vi test.py

```

In the new test file, add our simplest test which is preconfigured for Hello World:

```python

import pytest
from datetime import datetime

from ecosystem_tests.dorkl import basic_blueprint_test

blueprint_list = ['hello-world-example/aws.yaml']
TEST_ID = 'hello-world-{0}'.format(datetime.now().strftime("%Y%m%d%H%M"))


@pytest.fixture(scope='function', params=blueprint_list)
def blueprint_examples(request, test_id=TEST_ID):
    basic_blueprint_test(
        request.param,
        test_id,
        inputs='',
        timeout=3000,
        endpoint_name='application_endpoint',
        endpoint_value=200)


def test_blueprints(blueprint_examples):
    assert blueprint_examples is None

```

This test will install and uninstall all of the blueprints in the `blueprint_list` variable in sequence. After install and before uninstall, it will take the `application_endpoint` deployment output value. It will make a request to the URL. If the URL does returns a `200` return code, then the test will not pass. Finally, the test will execute uninstall. If the test fails, the cleanup still executes uninstall.

The test parameter `endpoint_name` is the output name, for example `application_endpoint` in the Hello World Example. The test parameter `endpoint_value` is the expected return code.

You can now run this test.

```bash  ::  pytest -s test.py 
=================================================================================================================================================== test session starts ===================================================================================================================================================
platform darwin -- Python 3.6.5, pytest-4.6.3, py-1.9.0, pluggy-0.13.1
rootdir: /Users/macos/Desktop/test
plugins: requests-mock-1.8.0
collected 1 item                                                                                                                                                                                                                                                                                                          
....
```

You will see in the test output all of the same output that you would see if you installed the blueprint manually from the CLI.

You can also build new tests with this toolkit.

For example, the [Getting Started](https://github.com/cloudify-community/blueprint-examples/blob/latest/.cicd/test_examples.py#L56) test.

This test is designed to upload component blueprints to your manager, before executing the main install.


# Plugin testing tools

Plugin testing tools are very similar to the blueprint testing tools in that, we are going to test a plugin by running a blueprint that uses that plugin.

Let's use the AWS plugin as an example. Clone the AWS plugin:

```bash
  :: git clone https://github.com/cloudify-cosmo/cloudify-aws-plugin.git
```

For the first test, you should [build a wagon](https://github.com/cloudify-cosmo/cloudify-wagon-build-containers) of the plugin code.

Let's also clone the wagon builders repo:

```bash
  :: git clone https://github.com/cloudify-cosmo/cloudify-wagon-build-containers.git
```

Build the wagon builder image:

```bash
  :: docker build -t cloudify-centos-7-wagon-builder-py3 cloudify-wagon-build-containers/centos_7_py3/
```

Let's now build the AWS plugin wagon:

```bash
  ::  docker run -v /home/user/path/to/cloudify-aws-plugin/:/packaging cloudify-centos-7-wagon-builder-py3:latest
```

Upload the plugin:

```bash
  ::  cfy plugins upload cloudify-aws-plugin/cloudify_aws_plugin-2.5.1-py36-none-linux_x86_64.wgn -y cloudify-aws-plugin/plugin.yaml 
```

You can use the same test from the blueprint test. However, some notes:

1) Again, the list of paths in the `blueprint_list` variable are the blueprints that will be tested.

2) If your test blueprint does not have outputs that can be cURLed, then simple remove these two values: `endpoint_name` and `endpoint_value`:

```python
    basic_blueprint_test(
        request.param,
        test_id,
        inputs='',
        timeout=3000)
```

Run the test:

```bash  ::  pytest -s blueprint-examples/test.py 
=================================================================================================================================================== test session starts ===================================================================================================================================================
platform darwin -- Python 3.6.5, pytest-4.6.3, py-1.9.0, pluggy-0.13.1
rootdir: /Users/macos/Desktop/test
plugins: requests-mock-1.8.0
collected 1 item                                                                                                                                                                                                                                                                                                          
....
```

Now that the test has passed (or failed!), let's say that you want to change some code in your plugin.

So, for example you could add some logging to the VM create function in `/home/user/path/to/cloudify-aws-plugin/cloudify_aws/ec2/resources/instances.py`.

I'll add something to line `103` in AWS Plugin 2.5.1:

```python
    def create(self, params):
        '''
            Create AWS EC2 Instances.
        '''
        self.logger.info('I like to test my plugins during development!')
        return self.make_client_call('run_instances', params)
```

Now, how do I get this code on to my manager? Our toolkit offers a solution. Add this to the test imports section:


```python
import os
from ecosystem_tests.dorkl import (
    basic_blueprint_test,
    update_plugin_on_manager)

plugin_path = os.path.join(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir)
    ),
    'test',
    'cloudify-aws-plugin'
)
update_plugin_on_manager(
    plugin_path, 'cloudify-aws-plugin', ['cloudify-aws-plugin/cloudify_aws'])
```

When I run the test, this will replace the AWS plugin code on our Cloudify Manager with the new code, before the blueprint is tested.

Naturally, you should run all unit tests before you test your new plugin code.

Now I can re-run my Hello World test:

```bash
  ::  pytest -s test.py 
=================================================================================================================================================== test session starts ===================================================================================================================================================
platform darwin -- Python 3.6.5, pytest-4.6.3, py-1.9.0, pluggy-0.13.1
rootdir: /Users/macos/Desktop/test
plugins: requests-mock-1.8.0
collecting ... DEBUG:root:Checking plugin YAML version with /Users/macos/Desktop/test/cloudify-aws-plugin/plugin.yaml
DEBUG:root:Package version 2.5.1
DEBUG:root:Package source https://github.com/cloudify-cosmo/cloudify-aws-plugin/archive/2.5.1.zip
INFO:root:Version 2.5.1 is in CHANGELOG.
INFO:root:Version 2.5.1 matches 2.5.1
.
INFO:logger:Replacing cloudify-aws-plugin/cloudify_aws on manager /opt/mgmtworker/env/plugins/default_tenant/cloudify-aws-plugin/2.5.1/lib/python3.6/site-packages/cloudify_aws
INFO:logger:Executing command docker cp cloudify-aws-plugin/cloudify_aws cfy_manager:/tmp/cloudify_aws...
INFO:logger:Command docker cp cloudify-aws-plugin/cloudify_aws cfy_manager:/tmp/cloudify_aws still executing...
INFO:logger:Command finished docker cp cloudify-aws-plugin/cloudify_aws cfy_manager:/tmp/cloudify_aws...
INFO:logger:Command succeeded docker cp cloudify-aws-plugin/cloudify_aws cfy_manager:/tmp/cloudify_aws...
INFO:logger:Executing command docker exec cfy_manager rm -rf /opt/mgmtworker/env/plugins/default_tenant/cloudify-aws-plugin/2.5.1/lib/python3.6/site-packages/cloudify_aws...
INFO:logger:Command docker exec cfy_manager rm -rf /opt/mgmtworker/env/plugins/default_tenant/cloudify-aws-plugin/2.5.1/lib/python3.6/site-packages/cloudify_aws still executing...
INFO:logger:Command finished docker exec cfy_manager rm -rf /opt/mgmtworker/env/plugins/default_tenant/cloudify-aws-plugin/2.5.1/lib/python3.6/site-packages/cloudify_aws...
INFO:logger:Command succeeded docker exec cfy_manager rm -rf /opt/mgmtworker/env/plugins/default_tenant/cloudify-aws-plugin/2.5.1/lib/python3.6/site-packages/cloudify_aws...
INFO:logger:Executing command docker exec cfy_manager mv /tmp/cloudify_aws /opt/mgmtworker/env/plugins/default_tenant/cloudify-aws-plugin/2.5.1/lib/python3.6/site-packages/cloudify_aws...
INFO:logger:Command docker exec cfy_manager mv /tmp/cloudify_aws /opt/mgmtworker/env/plugins/default_tenant/cloudify-aws-plugin/2.5.1/lib/python3.6/site-packages/cloudify_aws still executing...
INFO:logger:Command finished docker exec cfy_manager mv /tmp/cloudify_aws /opt/mgmtworker/env/plugins/default_tenant/cloudify-aws-plugin/2.5.1/lib/python3.6/site-packages/cloudify_aws...
INFO:logger:Command succeeded docker exec cfy_manager mv /tmp/cloudify_aws /opt/mgmtworker/env/plugins/default_tenant/cloudify-aws-plugin/2.5.1/lib/python3.6/site-packages/cloudify_aws...
INFO:logger:Executing command docker exec cfy_manager chown -R cfyuser:cfyuser /opt/mgmtworker/env/plugins/default_tenant/cloudify-aws-plugin/2.5.1/lib/python3.6/site-packages/cloudify_aws...
INFO:logger:Command docker exec cfy_manager chown -R cfyuser:cfyuser /opt/mgmtworker/env/plugins/default_tenant/cloudify-aws-plugin/2.5.1/lib/python3.6/site-packages/cloudify_aws still executing...
INFO:logger:Command finished docker exec cfy_manager chown -R cfyuser:cfyuser /opt/mgmtworker/env/plugins/default_tenant/cloudify-aws-plugin/2.5.1/lib/python3.6/site-packages/cloudify_aws...
INFO:logger:Command succeeded docker exec cfy_manager chown -R cfyuser:cfyuser /opt/mgmtworker/env/plugins/default_tenant/cloudify-aws-plugin/2.5.1/lib/python3.6/site-packages/cloudify_aws...
```

You'll notice that the output now details the code swap, that we've asked the test to perform.

If we pay careful attention to our test logs, we will notice that our new log message has been added to the plugin code executed on the manager.

```bash
INFO:logger:Command docker exec cfy_manager cfy executions start --timeout 3000 -d hello-world-202012101056 install still executing...
INFO:logger:Execution output: 2020-12-10 09:01:15.788  CFY <hello-world-202012101056> [vm_vr4usn.configure] Sending task 'cloudify_aws.ec2.resources.instances.create'
INFO:logger:Execution output: 2020-12-10 09:01:18.771  LOG <hello-world-202012101056> [vm_vr4usn.configure] INFO: I like to test my plugins during development!
INFO:logger:Command docker exec cfy_manager cfy executions start --timeout 3000 -d hello-world-202012101056 install still executing...
```


# IDE

## Requirements:

  * pytest
  * pytest-logger, add this to your test runner configuration: `--log-cli-level debug -s -v`.


# Ecosystem test CLI

Ecosystem tests CLI introduced in order to improve blueprint testing and continuous development of blueprints.
Moreover, it makes testing blueprints and plugins via CI tools very intuitive.

The CLI has three commands:

* prepare-test-manager
* local-blueprint-test
* validate-blueprint

## prepare-test-manager command

prepare-test-manager command responsible for uploading license, plugins and create secrets on the manager before test invocation.
If the manager has all the assets needed for the test, you can skip this command.

### Options:

`l, --license TEXT` - Licence for the manager, should be either path 
to licence file or base64 encoded licence string. Default: license.yaml

`-s, --secret TEXT` - A secret to update on the manager, should be provided 
as secret_key=secret_value. This argument can be used multiple times.

 `-fs, --file-secret TEXT` - A secret to update on the manager, should be 
 provided as secret_key=file_path. This argument can be used multiple times.

`-es, --encoded-secret TEXT` - Base 64 encoded secret to update on the manager,
should be provided as secret_key=secret_value_base_64_encoded. 
This argument can be used multiple times.

`-p, --plugin TEXT` - Plugin to upload before test invocation, should be
provided as --plugin plugin_wagon_url plugin.yaml_url. This argument can be used
multiple times.

`--bundle-path PATH` - Plugins bundle tgz file path.

`--skip-bundle-upload` - Specify --skip-bundle-upload for not uploading
plugins bundle before the test. Default: False.

`-c, --container-name TEXT` - Manager docker container name. Default: cfy_manager.

`--yum-package TEXT` - Yum package to install on the manager container.

**Notes**:

* Use `-n` when creating base64 encoded values like:
``bash
echo -n  secret_value | base64
``
* To create base64 encoded string of file content use:
```bash
base64 /path/to/file/with/secret/content -w0
```

### Example

```bash
ecosystem-test prepare-test-manager -l $TEST_LICENSE -s aws_access_key_id=<your aws access key id> -s aws_secret_access_key=<your aws secret access key>  --yum-package git
```

This command will:
* Upload license which its content resides in `$TEST_LICENSE` environment variable(base64 encoded!).
* Create two secrets on the manager - `aws_access_key_id` and `aws_secret_access_key`.
* Upload plugins bundle(default value).
* Install `git` package on the manager container using `yum`.

## local-blueprint-test command

This command invokes blueprint tests.
You can invoke multiple blueprints tests in a single command.

### Options:
`-b, --blueprint-path PATH` - Blueprint path, This option can be used multiple times.
Default: blueprint.yaml.

`--test-id TEXT`  -  Test id, the name of the test deployment. CLI will randomize test id if not provided.

`-i, --inputs TEXT` - Test inputs (Can be provided as path to YAML file,
or as 'key1=value1;key2=value2'). This argument can be used multiple times.

`-t, --timeout INTEGER` - Test timeout (seconds). Default: 1800.

`--on-failure` - Which action to perform on test failure.
Should be one of: donothing(do nothing), cancel(cancel install/update workflows if test fails),
rollback-full, rollback-partial, uninstall-force. Default: rollback-partial.

`--uninstall-on-success BOOLEAN` - Whether to perform uninstall if the test 
succeeded,and delete the test blueprint. Default: True.

`--on-subsequent-invoke` - Which action to perform on subsequent invocation of
the test (same test id). Should be one of: resume, rerun, update. Default: rerun.

`-c, --container-name TEXT` - Manager docker container name. Default: cfy_manager.

`--nested-test TEXT` - Nested tests, will run by pytest, should be specified in 
the pytest notation like: path/to/module.py::TestClass::test_method.

`--dry-run` - Perform dry run means process the inputs and settings for the test
and print this information.

**Notes:**

* If multiple blueprints provided in a single test command, do not provide --test-id.

* `--on-failure`  default value is `rollback-partial`, although currently 
  Rollback workflow is part of the Utilities plugin and not built in workflow, so 
  it recommended to use different value for this option while invoking tests. 

* When providing `rerun`,`resume` for `--on-subsequent-invoke` and the tool recognize the test exists,
  inputs like `-b`,`-i` will be ignored because an install workflow will be executed/resumed for the existing deployment.
  it's recommended to provide only `--test-id` in such cases.
  
# Example

```bash
ecosystem-test local-blueprint-test  -b examples/blueprint-examples/virtual-machine/aws-cloudformation.yaml --test-id=virtual-machine -i aws_region_name=us-east-1 -i resource_suffix=$CIRCLE_BUILD_NUM --on-failure=uninstall-force --timeout=3000
```

This command will:
* Upload aws-cloudformation.yaml blueprint. The name of the blueprint on the manager is `virtual-machine`.
  
* Deploy the blueprint with specified inputs. The name of the deployment on the manager is `virtual-machine`.

* If the blueprint upload/install workflow fails(timeout/error), uninstall workflow will be performed,
  and the blueprint will be deleted from the manager.
  
