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

from ...dorkl.runners import blueprint_validate
from ...ecosystem_tests_cli import ecosystem_tests
from ..utilities import (prepare_test_env,
                         validate_and_generate_test_ids)


@ecosystem_tests.command(name='validate-blueprint',
                         short_help='Validate blueprints.')
@prepare_test_env
@ecosystem_tests.options.blueprint_path
@ecosystem_tests.options.container_name
def validate_blueprint(blueprint_path,
                       container_name):
    """
    Perform blueprint validation on the given blueprints.
    """
    bp_test_ids = validate_and_generate_test_ids(blueprint_path, None)
    for blueprint, test_id in bp_test_ids:
        blueprint_validate(blueprint_file_name=blueprint,
                           blueprint_id=test_id)
