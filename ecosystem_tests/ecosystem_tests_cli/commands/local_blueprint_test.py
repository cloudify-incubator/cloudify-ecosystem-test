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

import pytest
from os import environ

import yaml
from nose.tools import nottest

from ..logger import logger
from ...ecosystem_tests_cli import ecosystem_tests, decorators
from ...dorkl.runners import basic_blueprint_test_dev
from ..decorators import prepare_test_env
from ..utilities import validate_and_generate_test_ids
from ecosystem_tests.ecosystem_tests_cli.utilities import (
    get_universal_path)


@nottest
@ecosystem_tests.command(name='local-blueprint-test',
                         short_help='Test blueprint locally.')
@prepare_test_env
@ecosystem_tests.options.blueprint_path
@ecosystem_tests.options.test_id
@ecosystem_tests.options.inputs
@ecosystem_tests.options.timeout
@ecosystem_tests.options.on_failure
@ecosystem_tests.options.uninstall_on_success
@ecosystem_tests.options.on_subsequent_invoke
@ecosystem_tests.options.container_name
@ecosystem_tests.options.nested_test
@ecosystem_tests.options.dry_run
@decorators.timer_decorator
def local_blueprint_test(blueprint_path,
                         test_id,
                         inputs,
                         timeout,
                         on_failure,
                         uninstall_on_success,
                         on_subsequent_invoke,
                         container_name,
                         nested_test,
                         dry_run):

    bp_test_ids = validate_and_generate_test_ids(blueprint_path, test_id)

    if dry_run:
        return handle_dry_run(bp_test_ids,
                              inputs,
                              timeout,
                              on_failure,
                              uninstall_on_success,
                              on_subsequent_invoke,
                              container_name,
                              nested_test)

    for blueprint, test_id in bp_test_ids:
        environ['__ECOSYSTEM_TEST_ID'] = test_id
        blueprint = get_universal_path(blueprint)
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
        del environ['__ECOSYSTEM_TEST_ID']


def handle_dry_run(bp_test_ids,
                   inputs,
                   timeout,
                   on_failure,
                   uninstall_on_success,
                   on_subsequent_invoke,
                   container_name,
                   nested_test):
    dry_run_str = '\nDry run:\n' \
                  'Manager container name: {container_name} \n' \
                  'Tests: \n\n'.format(container_name=container_name)

    for blueprint, test_id in bp_test_ids:
        dry_run_str += 'Test ID: {id} \n' \
                       'Test Blueprint: {bp} \n' \
                       'Test inputs: \n' \
                       '\t{inputs} \n' \
                       'Timeout: {timeout} \n' \
                       'On failure: {on_failure} \n' \
                       'Uninstall on success: {uninstall_on_success}\n' \
                       'On subsequent invoke: {on_subsequent_invoke} \n' \
                       '--------------------' \
                       '\n'.format(id=test_id,
                                   bp=blueprint,
                                   inputs=yaml.dump(inputs,
                                                    default_flow_style=False)
                                   .replace('\n', '\n\t'),
                                   timeout=timeout,
                                   on_failure=on_failure,
                                   uninstall_on_success=uninstall_on_success,
                                   on_subsequent_invoke=on_subsequent_invoke)

    for test in nested_test:
        dry_run_str += 'Nested test: {test} \n' \
                       '--------------------\n'.format(test=test)

    dry_run_str += 'Notes:\n' \
                   '* Tests id`s might change if they randomized by the ' \
                   'tool.\n' \
                   '* On subsequent invoke with rerun/resume the following ' \
                   'are ignored if provided:\n' \
                   '  - blueprint path\n' \
                   '  - inputs '

    logger.info(dry_run_str)


def nested_test_executor(nested_tests=None):
    nested_tests = nested_tests or []
    for nested_test in nested_tests:
        logger.info('Executing nested test: {test_path} '.format(
            test_path=nested_test))
        nested_result = pytest.main(['-s', nested_test])
        if nested_result != 0:
            raise Exception(
                'Nested test {test_path} failed! '
                'Result: {test_result}'.format(
                    test_path=nested_test, test_result=nested_result))
