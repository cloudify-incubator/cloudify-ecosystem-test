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

from ...ecosystem_tests_cli import ecosystem_tests
from ecosystem_tests.dorkl.commands import replace_plugin_package_on_manager


@ecosystem_tests.command(name='swap-plugin-code',
                         short_help='Swap plugin code on manager.')
@ecosystem_tests.options.directory
@ecosystem_tests.options.package
@ecosystem_tests.options.plugin_version
def swap_plugin_code(directory, package, plugin_version):

    for packages in [package]:
        replace_plugin_package_on_manager(
            packages[0], plugin_version, directory, )
