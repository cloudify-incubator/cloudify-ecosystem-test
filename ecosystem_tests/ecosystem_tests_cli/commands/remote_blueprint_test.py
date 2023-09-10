########
# Copyright (c) 2014-2022 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import pytest
from pathlib import Path

import yaml
from nose.tools import nottest

from ecosystem_cicd_tools.new_cicd.ec2 import check_eip_quota
from ecosystem_tests.nerdl.runners import basic_blueprint_test_dev
from ecosystem_tests.ecosystem_tests_cli.utilities import (
    get_universal_path)
from ecosystem_tests.ecosystem_tests_cli.commands.local_blueprint_test import (
    handle_dry_run,
    nested_test_executor
)
from ecosystem_tests.ecosystem_tests_cli import (
    logger,
    utilities,
    decorators,
    ecosystem_tests
)


@nottest
@ecosystem_tests.command(name='remote-blueprint-test',
                         short_help='Test blueprint Remotely.')
@decorators.prepare_test_env
@ecosystem_tests.options.blueprint_path
@ecosystem_tests.options.test_id
@ecosystem_tests.options.inputs
@ecosystem_tests.options.timeout
@ecosystem_tests.options.on_failure
@ecosystem_tests.options.uninstall_on_success
@ecosystem_tests.options.on_subsequent_invoke
@ecosystem_tests.options.cloudify_token
@ecosystem_tests.options.cloudify_tenant
@ecosystem_tests.options.cloudify_hostname
@ecosystem_tests.options.nested_test
@ecosystem_tests.options.dry_run
@ecosystem_tests.options.required_ips
@decorators.timer_decorator
def remote_blueprint_test(blueprint_path,
                          test_id,
                          inputs,
                          timeout,
                          on_failure,
                          uninstall_on_success,
                          on_subsequent_invoke,
                          cloudify_token,
                          cloudify_tenant,
                          cloudify_hostname,
                          nested_test,
                          dry_run,
                          required_ips):

    bp_test_ids = utilities.validate_and_generate_test_ids(
        blueprint_path, test_id)
    check_eip_quota(required_ips)

    if dry_run:
        return handle_dry_run(bp_test_ids,
                              inputs,
                              timeout,
                              on_failure,
                              uninstall_on_success,
                              on_subsequent_invoke,
                              nested_test=nested_test,
                              cloudify_host=cloudify_host,
                              cloudify_tenant=cloudify_tenant)

    for blueprint, test_id in bp_test_ids:
        os.environ['__ECOSYSTEM_TEST_ID'] = test_id
        blueprint = Path(blueprint).resolve().as_posix()
        logger.logger.info('Starting with {}:{}'.format(test_id, blueprint))
        basic_blueprint_test_dev(
            blueprint_file_name=blueprint,
            test_name=test_id,
            inputs=inputs,
            timeout=timeout,
            on_subsequent_invoke=on_subsequent_invoke,
            on_failure=on_failure,
            uninstall_on_success=uninstall_on_success,
            user_defined_check=nested_test_executor if nested_test else None,
            user_defined_check_params={
                'nested_tests': nested_test
            } if nested_test else None)
        del os.environ['__ECOSYSTEM_TEST_ID']
