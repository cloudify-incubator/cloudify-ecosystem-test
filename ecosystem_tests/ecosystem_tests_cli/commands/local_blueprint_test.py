########
# Copyright (c) 2014-2021 Cloudify Platform Ltd. All rights reserved
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

from nose.tools import nottest

from ...ecosystem_tests_cli import ecosystem_tests
from ...dorkl.runners import basic_blueprint_test_dev
from ..utilities import (prepare_test_env,
                         validate_and_generate_test_ids)


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
def local_blueprint_test(blueprint_path,
                         test_id,
                         inputs,
                         timeout,
                         on_failure,
                         uninstall_on_success,
                         on_subsequent_invoke,
                         container_name):
    on_failure = False if on_failure == 'False' else on_failure
    bp_test_ids = validate_and_generate_test_ids(blueprint_path, test_id)
    for blueprint, test_id in bp_test_ids:
        basic_blueprint_test_dev(blueprint_file_name=blueprint,
                                 test_name=test_id,
                                 inputs=inputs,
                                 timeout=timeout,
                                 on_subsequent_invoke=on_subsequent_invoke,
                                 on_failure=on_failure,
                                 uninstall_on_success=uninstall_on_success)
