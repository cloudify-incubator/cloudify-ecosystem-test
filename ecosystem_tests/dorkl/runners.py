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
import base64
import traceback
from time import sleep
from datetime import datetime
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

from nose.tools import nottest

from ecosystem_tests.dorkl.constansts import (RERUN,
                                              logger,
                                              RESUME,
                                              UPDATE,
                                              CANCEL,
                                              TIMEOUT,
                                              DONOTHING,
                                              ROLLBACK_FULL,
                                              UNINSTALL_FORCE,
                                              VPN_CONFIG_PATH,
                                              ROLLBACK_PARTIAL,
                                              RED,
                                              GREEN,
                                              YELLOW,
                                              BLUE,
                                              PINK,
                                              CYAN,
                                              RESET,
                                              BOLD,
                                              UNDERLINE)
from ecosystem_tests.dorkl.exceptions import (EcosystemTimeout,
                                              EcosystemTestException)
from ecosystem_tests.dorkl.cloudify_api import (use_cfy,
                                                license_upload,
                                                verify_endpoint,
                                                executions_list,
                                                executions_start,
                                                blueprint_exists,
                                                deployment_delete,
                                                deployment_update,
                                                executions_resume,
                                                blueprints_delete,
                                                blueprints_upload,
                                                cleanup_on_failure,
                                                wait_for_execution,
                                                deployments_create,
                                                upload_test_plugins,
                                                create_test_secrets,
                                                upload_test_plugins_dev,
                                                cancel_multiple_executions,
                                                get_deployment_output_by_name,
                                                get_blueprint_id_of_deployment)
from ecosystem_tests.dorkl.commands import (docker_exec,
                                            cloudify_exec,
                                            copy_file_to_docker)


def prepare_test(plugins=None,
                 secrets=None,
                 plugin_test=False,
                 pip_packages=None,
                 yum_packages=None,
                 execute_bundle_upload=True,
                 use_vpn=False,
                 workspace_path=None):
    """
    Prepare the environment for executing a plugin test.



    :param plugins: A list of plugins to install. `plugin_test` must be True.
    :param secrets: A list of secrets to create.
    :param plugin_test: Do want to use wagons in the workspace for this test?
    :param pip_packages: A list of packages to install (on manger) with pip.
    :param yum_packages: A list of packages to install (on manger) with yum.
    :param execute_bundle_upload: Whether to upload the plugins bundle.
    :param use_vpn:
    :param workspace_path: THe path to the build directory if not circleci
    :return:
    """

    pip_packages = pip_packages or []
    yum_packages = yum_packages or []
    use_cfy()
    license_upload()
    upload_test_plugins(plugins,
                        plugin_test,
                        execute_bundle_upload,
                        workspace_path=workspace_path)
    create_test_secrets(secrets)
    yum_command = 'yum install -y python-netaddr git '
    if use_vpn:
        yum_packages.append('openvpn')
    if yum_packages:
        yum_command = yum_command + ' '.join(yum_packages)
    docker_exec(yum_command)
    pip_command = '/opt/mgmtworker/env/bin/pip install netaddr ipaddr '
    if pip_packages:
        pip_command = pip_command + ' '.join(pip_packages)
    docker_exec(pip_command)
    if use_vpn:
        value = base64.b64decode(os.environ['vpn_config'])
        file_temp = NamedTemporaryFile(delete=False)
        with open(file_temp.name, 'w') as outfile:
            outfile.write(value)
        docker_path = copy_file_to_docker(file_temp.name)
        docker_exec('mv {0} {1}'.format(docker_path, VPN_CONFIG_PATH))


@nottest
def _basic_blueprint_test(blueprint_file_name,
                          test_name,
                          inputs=None,
                          timeout=None,
                          endpoint_name=None,
                          endpoint_value=None):
    """
    Simple blueprint install/uninstall test.
    :param blueprint_file_name:
    :param test_name:
    :param inputs:
    :param timeout:
    :return:
    """

    timeout = timeout or TIMEOUT
    if inputs != '':
        inputs = inputs or os.path.join(
            os.path.dirname(blueprint_file_name), 'inputs/test-inputs.yaml')
    logger.info('Blueprints list: {0}'.format(
        cloudify_exec('cfy blueprints list')))
    blueprints_upload(blueprint_file_name, test_name)
    logger.info('Deployments list: {0}'.format(
        cloudify_exec('cfy deployments list')))
    deployments_create(test_name, inputs)
    sleep(5)
    logger.info(GREEN + 'Installing...' + RESET)
    try:
        executions_list(test_name)
        executions_start('install', test_name, timeout)
    except EcosystemTimeout:
        # Give 5 seconds grace.
        executions_list(test_name)
        wait_for_execution(test_name, 'install', 10)
    else:
        wait_for_execution(test_name, 'install', timeout)
    if endpoint_name and endpoint_value:
        verify_endpoint(
            get_deployment_output_by_name(
                test_name,
                endpoint_name
            ), endpoint_value)
    logger.info(BLUE + 'Uninstalling...' + RESET)
    executions_start('uninstall', test_name, timeout)
    wait_for_execution(test_name, 'uninstall', timeout)
    try:
        deployment_delete(test_name)
        blueprints_delete(test_name)
    except Exception as e:
        logger.info(RED +
                    'Failed to delete blueprint, {0}'.format(str(e)) +
                    RESET)


@contextmanager
def vpn():
    """Run tests while VPN is executing.
    Does not actually work in circle ci :("""
    logger.info('Starting VPN...')
    proc = docker_exec('openvpn {config_path}'.format(
        config_path=VPN_CONFIG_PATH), detach=True)
    # TODO: Find a way to poll the VPN without killing it. :(
    sleep(10)
    logger.info('VPN is supposed to be running...')
    try:
        yield proc
    except Exception as e:
        # TODO: Learn about potential Exceptions here.
        logger.info(RED + 'VPN error {0}'.format(str(e)) + RESET)
        pass
        # Apparently CircleCI does not support VPNs. !!!!
    finally:
        logger.info('Stopping VPN...')
        proc.terminate()


@nottest
def basic_blueprint_test(blueprint_file_name,
                         test_name,
                         inputs=None,
                         timeout=None,
                         use_vpn=False,
                         endpoint_name=None,
                         endpoint_value=None):
    if use_vpn:
        with vpn():
            try:
                _basic_blueprint_test(blueprint_file_name,
                                      test_name,
                                      inputs,
                                      timeout,
                                      endpoint_name=endpoint_name,
                                      endpoint_value=endpoint_value)
            except Exception as e:
                logger.error(RED + 'Error: {e}'.format(e=str(e)) + RESET)
                cleanup_on_failure(test_name)
    else:
        try:
            _basic_blueprint_test(blueprint_file_name,
                                  test_name,
                                  inputs,
                                  timeout,
                                  endpoint_name=endpoint_name,
                                  endpoint_value=endpoint_value)
        except Exception as e:
            logger.error(RED + 'Error: {e}'.format(e=str(e)) + RESET)
            cleanup_on_failure(test_name)


def is_first_invocation(test_name):
    """
    Check if this is the first invocation of the test,
    by check existence of blueprint and deployment with test_name id.
    param: test_name: The test name.
    """
    logger.info(
        'Checking if {test_name} in deployments list '.format(
            test_name=test_name))
    deployments_list = cloudify_exec('cfy deployments list')

    def _map_func(bl_or_dep_dict):
        return bl_or_dep_dict["id"]

    if test_name in [_map_func(deployment) for deployment in deployments_list]:
        logger.info('Not first invocation!')
        return False
    else:
        logger.info('First invocation!')
        return True


def validate_on_subsequent_invoke_param(on_subsequent_invoke=None):
    if on_subsequent_invoke not in [RESUME, RERUN, UPDATE]:
        raise EcosystemTestException(
            'on_subsequent_invoke param must be one of:'
            ' resume, rerun, update')


def validate_on_failure_param(on_failure=None):
    if on_failure not in [DONOTHING, CANCEL, ROLLBACK_FULL,
                          ROLLBACK_PARTIAL, UNINSTALL_FORCE]:
        raise EcosystemTestException(
            'on_failure param should be one of: donothing, cancel, '
            'rollback-full, rollback-partial, uninstall-force')


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
    """
    blueprint test.
    :param blueprint_file_name: Path to blueprint for the test, notice that
    if there is a deployment for this test_name,this parameter will be
    ignored(except if on_subsequent_invoke value is "update")
    :param test_name:
    :param inputs: Inputs for deployment create / deployment update.
    :param timeout:
    :param on_subsequent_invoke: Should be one of: resume,rerun,update
    :param on_failure:  What should test do in failure.
    Should be one of: donothing(do nothing), cancel(cancel install/update
    workflow if test fails), rollback-full, rollback-partial, uninstall-force.
    The default value is rollback-partial.
    :param uninstall_on_success: Perform uninstall if the test succeeded,
    and delete the test blueprint.
    :param: user_defined_check: Function that performs user defined checks
     after the deployment installation succeeds.
    :param: user_defined_check_params: dictionary contains parameters
      for user defined check.
    :return:
    """
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

        except Exception:
            logger.error(traceback.format_exc())
            handle_test_failure(test_name, on_failure, timeout)
            raise EcosystemTestException(
                'Test {test_id} failed first invoke.'.format(
                    test_id=test_name))
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
            raise EcosystemTestException(
                'Test {test_id} failed subsequent invoke.'.format(
                    test_id=test_name))


@nottest
def first_invocation_test_path(blueprint_file_name,
                               test_name,
                               inputs=None,
                               timeout=None,
                               uninstall_on_success=True,
                               user_defined_check=None,
                               user_defined_check_params=None
                               ):
    logger.info('Blueprints list: {0}'.format(
        cloudify_exec('cfy blueprints list')))
    blueprints_upload(blueprint_file_name, test_name)
    logger.info('Deployments list: {0}'.format(
        cloudify_exec('cfy deployments list')))
    deployments_create(test_name, inputs)
    sleep(5)
    start_install_workflow(test_name, timeout)
    run_user_defined_check(user_defined_check, user_defined_check_params)
    if uninstall_on_success:
        handle_uninstall_on_success(test_name, timeout)


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
        resume_install_workflow(test_name, timeout)
    elif on_subsequent_invoke == RERUN:
        logger.warning('Rerunning install workflow of existing test. '
                       'blueprint_file_name and inputs are ignored!!')
        start_install_workflow(test_name, timeout)
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
        start_install_workflow(test_name, timeout)
    run_user_defined_check(user_defined_check, user_defined_check_params)
    if uninstall_on_success:
        handle_uninstall_on_success(test_name, timeout)


def handle_deployment_update(blueprint_file_name,
                             update_bp_name,
                             test_name,
                             inputs,
                             timeout):
    logger.info('updating deployment...')
    try:
        logger.info('Blueprints list: {0}'.format(
            cloudify_exec('cfy blueprints list')))
        blueprints_upload(blueprint_file_name, update_bp_name)
        deployment_update(test_name,
                          update_bp_name,
                          inputs,
                          timeout)
    except EcosystemTimeout:
        # Give 5 seconds grace.
        executions_list(test_name)
        wait_for_execution(test_name, 'update', 10)
    else:
        wait_for_execution(test_name, 'update', timeout)


def handle_uninstall_on_success(test_name, timeout):
    logger.info(BLUE + 'Uninstalling...' + RESET)
    executions_start('uninstall', test_name, timeout)
    wait_for_execution(test_name, 'uninstall', timeout)
    blueprint_of_deployment = get_blueprint_id_of_deployment(test_name)
    logger.info(
        "Blueprint id of deployment {dep_id} is : {blueprint_id}".format(
            dep_id=test_name, blueprint_id=blueprint_of_deployment))
    try:
        deployment_delete(test_name)
        blueprints_delete(blueprint_of_deployment)
    except Exception as e:
        logger.info(RED +
                    'Failed to delete blueprint, {0}'.format(str(e)) +
                    RESET)


def resume_install_workflow(test_name, timeout):
    exec_id = find_install_execution_to_resume(test_name)
    logger.debug('execution to resume: {id}'.format(id=exec_id))
    try:
        logger.info('resuming...')
        executions_resume(exec_id, timeout)
    except EcosystemTimeout:
        # Give 5 seconds grace.
        executions_list(test_name)
        wait_for_execution(test_name, 'install', 10)
    else:
        wait_for_execution(test_name, 'install', timeout)


def start_install_workflow(test_name, timeout):
    logger.info(GREEN + 'Installing...' + RESET)
    try:
        executions_list(test_name)
        executions_start('install', test_name, timeout)
    except EcosystemTimeout:
        # Give 5 seconds grace.
        executions_list(test_name)
        wait_for_execution(test_name, 'install', 10)
    else:
        wait_for_execution(test_name, 'install', timeout)


def find_install_execution_to_resume(deployment_id):
    """
    Find the last install execution to resume.
    :param deployment_id:
    :return:
    """
    executions = executions_list(deployment_id)
    try:
        # Get the last install execution
        ex = [e for e in executions
              if 'install' == e['workflow_id']][-1]
        # For debugging
        logger.info("these are potential executions to resume")
        logger.info([e for e in executions if 'install' == e['workflow_id']])
    except (IndexError, KeyError):
        raise EcosystemTestException(
            'Workflow install to resume for deployment {dep_id} was not '
            'found.'.format(
                dep_id=deployment_id))

    if ex['status'].lower() not in ['failed', 'cancelled']:
        raise EcosystemTestException(
            'Found install execution with id: {id} but with status {status},'
            'can`t resume this execution'.format(
                id=ex['id'], status=ex['status']))
    return ex['id']


def find_executions_to_cancel(deployment_id):
    """
    Find all the executions to cancel.
    :param deployment_id:
    :return:
    """
    executions = executions_list(deployment_id)
    try:
        # Get all install and update executions
        filtered_executions = \
            [e['id'] for e in executions if
             e['workflow_id'] in ['install', 'update'] and e['status'].lower()
             in ['pending', 'started']]
        # For debugging
        logger.info(
            "these are potential executions to cancel: {executions}".format(
                executions=filtered_executions))
    except (IndexError, KeyError):
        logger.info(
            'Workflows to cancel for deployment {dep_id} was not '
            'found.'.format(
                dep_id=deployment_id))
        filtered_executions = []

    return filtered_executions


@nottest
def handle_test_failure(test_name, on_failure, timeout):
    """
    rollback-full,rollback-partial,uninstall-force
    """
    logger.info('Handling test failure...')
    executions_to_cancel = find_executions_to_cancel(test_name)
    if on_failure is DONOTHING:
        return
    elif on_failure is CANCEL:
        cancel_multiple_executions(executions_to_cancel, timeout, force=False)
    elif on_failure == ROLLBACK_FULL:
        cancel_multiple_executions(executions_to_cancel, timeout, force=False)
        executions_start('rollback', test_name, timeout,
                         params='full_rollback=true')
    elif on_failure == ROLLBACK_PARTIAL:
        cancel_multiple_executions(executions_to_cancel, timeout, force=False)
        executions_start('rollback', test_name, timeout)
    elif on_failure == UNINSTALL_FORCE:
        cancel_multiple_executions(executions_to_cancel, timeout, force=False)
        cleanup_on_failure(test_name)
    else:
        raise EcosystemTestException('Wrong on_failure param supplied,'
                                     ' Doing nothing please clean resources on'
                                     ' the manager manually.')


@nottest
def prepare_test_dev(plugins=None,
                     secrets=None,
                     execute_bundle_upload=True,
                     bundle_path=None,
                     yum_packages=None):
    """
    Prepare the environment for executing a blueprint test.



    :param plugins: A list of plugins to install. `plugin_test` must be True.
    :param secrets: A list of secrets to create.
    :param execute_bundle_upload: Whether to upload the plugins bundle.
    :param bundle_path: The path to the build directory if not circleci
    :param yum_packages: A list of packages to install (on manger) with yum.
    :return:
    """
    yum_packages = yum_packages or []
    if yum_packages:
        docker_exec('yum install -y ' + ' '.join(yum_packages))
    use_cfy()
    license_upload()
    upload_test_plugins_dev(plugins,
                            execute_bundle_upload,
                            bundle_path=bundle_path)
    create_test_secrets(secrets)


def run_user_defined_check(user_defined_check, user_defined_check_params):
    if user_defined_check:
        if callable(user_defined_check):
            logger.info('Run user defined check...')
            params = user_defined_check_params or {}
            user_defined_check(**params)
        else:
            raise EcosystemTestException('User defined check is not callable!')


def blueprint_validate(blueprint_file_name,
                       blueprint_id,
                       skip_delete=False,
                       skip_duplicate=False):
    """
    Blueprint upload for validation.
    """
    if not blueprint_exists(blueprint_id):
        blueprints_upload(blueprint_file_name, blueprint_id)
    elif not skip_duplicate:
        raise EcosystemTestException(
            'Blueprint {b} exists and skip_duplicates is False.'.format(
                b=blueprint_id))
    if not skip_delete:
        blueprints_delete(blueprint_id)
