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

import sys
import traceback

from nose.tools import nottest

from ecosystem_tests.nerdl import api
from ecosystem_tests.dorkl.exceptions import EcosystemTimeout
from ecosystem_tests.ecosystem_tests_cli.logger import logger
from ecosystem_tests.dorkl.constansts import (
    RED,
    RESET,
    RERUN,
    RESUME,
    UPDATE,
    CANCEL,
    TIMEOUT,
    DONOTHING,
    ROLLBACK_FULL,
    UNINSTALL_FORCE,
    ROLLBACK_PARTIAL,
)
from ecosystem_tests.dorkl.runners import (
    run_user_defined_check,
    validate_on_failure_param,
    validate_on_subsequent_invoke_param,
)


@nottest
def basic_blueprint_test_dev(blueprint_file_name,
                             test_name,
                             inputs=None,
                             timeout=None,
                             on_subsequent_invoke=None,
                             on_failure=ROLLBACK_PARTIAL,
                             uninstall_on_success=True,
                             user_defined_check=None,
                             user_defined_check_params=None
                             ):

    timeout = timeout or TIMEOUT
    validate_on_failure_param(on_failure)
    if is_first_invocation(test_name):
        try:
            first_invocation_test_path(
                blueprint_file_name,
                test_name,
                inputs=inputs,
                timeout=timeout,
                uninstall_on_success=uninstall_on_success,
                user_defined_check=user_defined_check,
                user_defined_check_params=user_defined_check_params)
        except Exception as e:
            logger.error(traceback.format_exc())
            handle_test_failure(test_name, on_failure, timeout)
            sys.exit(1)
    else:
        validate_on_subsequent_invoke_param(on_subsequent_invoke)
        try:
            subsequent_invocation_test_path(
                blueprint_file_name,
                test_name,
                on_subsequent_invoke=on_subsequent_invoke,
                inputs=inputs,
                timeout=timeout,
                uninstall_on_success=uninstall_on_success,
                user_defined_check=user_defined_check,
                user_defined_check_params=user_defined_check_params)
        except Exception:
            logger.error(RED + traceback.format_exc() + RESET)
            handle_test_failure(test_name, on_failure, timeout)
            sys.exit(1)


def is_first_invocation(test_name):
    """
    Check if this is the first invocation of the test,
    by check existence of blueprint and deployment with test_name id.
    param: test_name: The test name.
    """
    logger.info(
        'Checking if {test_name} in deployments list '.format(
            test_name=test_name))

    if api.deployment_exists(test_name):
        logger.info('Not first invocation!')
        return False
    else:
        logger.info('First invocation!')
        return True


@nottest
def first_invocation_test_path(blueprint_file_name,
                               test_name,
                               inputs=None,
                               timeout=None,
                               uninstall_on_success=True,
                               user_defined_check=None,
                               user_defined_check_params=None
                               ):
    api.list_blueprints()
    api.upload_blueprint(blueprint_file_name, test_name)
    api.list_deployments()
    api.create_deployment(test_name, test_name, inputs)
    api.wait_for_deployment_create(test_name)
    api.wait_for_install(test_name, timeout)
    run_user_defined_check(user_defined_check, user_defined_check_params)
    if uninstall_on_success:
        handle_uninstall_on_success(test_name, timeout)


@nottest
def handle_test_failure(test_name, on_failure, timeout):
    """
    rollback-full,rollback-partial,uninstall-force
    """
    logger.info('Handling test failure...')
    executions_to_cancel = api.list_executions(test_name)
    if on_failure is DONOTHING:
        return
    elif on_failure is CANCEL:
        api.cancel_multiple_executions(executions_to_cancel)
    elif on_failure == ROLLBACK_FULL:
        api.cancel_multiple_executions(executions_to_cancel)
        api.wait_for_workflow(
            test_name,
            'rollback',
            timeout,
            params={'full_rollback': true})
    elif on_failure == ROLLBACK_PARTIAL:
        api.cancel_multiple_executions(executions_to_cancel)
        api.wait_for_workflow(test_name, 'rollback', timeout)
    elif on_failure == UNINSTALL_FORCE:
        api.cancel_multiple_executions(executions_to_cancel)
        api.cleanup_on_failure(test_name, timeout)
    else:
        logger.error(
            'Wrong on_failure param supplied,'
            ' Doing nothing please clean resources on'
            ' the manager manually.')
        sys.exit(1)


@nottest
def subsequent_invocation_test_path(blueprint_file_name,
                                    test_name,
                                    on_subsequent_invoke,
                                    inputs=None,
                                    timeout=None,
                                    uninstall_on_success=True,
                                    user_defined_check=None,
                                    user_defined_check_params=None
                                    ):
    """
    Handle blueprint test path in subsequent test invocation depends on
    on_subsequent_invoke value.
    :param blueprint_file_name: Path to blueprint.
    :param test_name:
    :param on_subsequent_invoke: Should be one of: resume,rerun,update.
    :param inputs:
    :param timeout:
    :param uninstall_on_success: Perform uninstall if the test succeeded,
    and delete the test blueprint.
    """
    logger.debug('on subsequent_invocation_test_path')
    if on_subsequent_invoke == RESUME:
        logger.warning('Resuming install workflow of existing test. '
                       'blueprint_file_name and inputs are ignored!!')
        api.resume_install_workflow(test_name, timeout)
    elif on_subsequent_invoke == RERUN:
        logger.warning('Rerunning install workflow of existing test. '
                       'blueprint_file_name and inputs are ignored!!')
        api.wait_for_install(test_name, timeout)
    elif on_subsequent_invoke == UPDATE:
        update_bp_name = test_name + '-' + datetime.now().strftime(
            "%d-%m-%Y-%H-%M-%S")
        handle_deployment_update(blueprint_file_name,
                                 update_bp_name,
                                 test_name,
                                 inputs,
                                 timeout)
        # We run install after update because of this scenario:
        # The user run test with blueprint X then the test fails, on second
        # invocation the user uses "update" option so the tool runs update
        # with the same blueprint X and it
        # succeeds(because nothing changed in the blueprint)
        api.wait_for_install(test_name, timeout)
    run_user_defined_check(user_defined_check, user_defined_check_params)
    if uninstall_on_success:
        handle_uninstall_on_success(test_name, timeout)


def handle_uninstall_on_success(test_name, timeout):
    api.wait_for_uninstall(test_name, timeout=timeout)
    api.delete_deployment(test_name)
    api.delete_blueprint(test_name)
    api.delete_plugins()


def handle_deployment_update(blueprint_file_name,
                             update_bp_name,
                             test_name,
                             inputs,
                             timeout):
    logger.info('updating deployment...')
    logger.info('Blueprints list: {0}'.format(
        cloudify_exec('cfy blueprints list')))
    api.update_deployment_wrapper(
        blueprint_file_name,
        update_bp_name,
        inputs,
        test_name
    )
