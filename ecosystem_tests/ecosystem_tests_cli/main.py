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

from ..ecosystem_tests_cli import ecosystem_tests
from .commands import (validate_plugin_version,
                       validate_blueprint,
                       validate_docs,
                       local_blueprint_test,
                       package_release,
                       prepare_test_manager)


@ecosystem_tests.group(name='ecosystem-test')
def _ecosystem_test():
    """Ecosystem tests Command Line Interface."""
    ecosystem_tests.init()


def _register_commands():
    _ecosystem_test.add_command(local_blueprint_test.local_blueprint_test)
    _ecosystem_test.add_command(prepare_test_manager.prepare_test_manager)
    _ecosystem_test.add_command(validate_blueprint.validate_blueprint)
    _ecosystem_test.add_command(package_release.package_release)
    _ecosystem_test.add_command(
        validate_plugin_version.validate_plugin_version)
    _ecosystem_test.add_command(validate_docs.validate_docs)


_register_commands()

if __name__ == "__main__":
    _ecosystem_test()
