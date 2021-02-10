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

from .logger import logger
from ..ecosystem_tests_cli import ecosystem_tests
from .commands import (local_blueprint_test,
                       prepare_test_manager)


@ecosystem_tests.group(name='ecosystem-test')
def _ecosystem_test():
    """Ecosystetm tests Command Line Interface."""
    ecosystem_tests.init()


def _register_commands():
    _ecosystem_test.add_command(local_blueprint_test.local_blueprint_test)
    _ecosystem_test.add_command(prepare_test_manager.prepare_test_manager)


_register_commands()

if __name__ == "__main__":
    _ecosystem_test()
