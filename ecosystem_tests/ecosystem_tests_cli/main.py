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

from ..ecosystem_tests_cli import ecosystem_tests
from .commands import (merge_docs,
                       validate_docs,
                       upload_assets,
                       create_bundle,
                       upload_plugin,
                       package_release,
                       swap_plugin_code,
                       validate_blueprint,
                       verify_plugins_json,
                       prepare_test_manager,
                       local_blueprint_test,
                       generate_plugins_json,
                       validate_plugin_yamls,
                       validate_plugin_version)


@ecosystem_tests.group(name='ecosystem-test')
def _ecosystem_test():
    """Ecosystem tests Command Line Interface."""
    ecosystem_tests.init()


def _register_commands():
    _ecosystem_test.add_command(merge_docs.merge_docs)
    _ecosystem_test.add_command(validate_docs.validate_docs)
    _ecosystem_test.add_command(upload_assets.upload_assets)
    _ecosystem_test.add_command(create_bundle.create_bundle)
    _ecosystem_test.add_command(upload_plugin.upload_plugin)
    _ecosystem_test.add_command(package_release.package_release)
    _ecosystem_test.add_command(package_release.package_release)
    _ecosystem_test.add_command(swap_plugin_code.swap_plugin_code)
    _ecosystem_test.add_command(validate_blueprint.validate_blueprint)
    _ecosystem_test.add_command(verify_plugins_json.verify_plugins_json)
    _ecosystem_test.add_command(local_blueprint_test.local_blueprint_test)
    _ecosystem_test.add_command(prepare_test_manager.prepare_test_manager)
    _ecosystem_test.add_command(generate_plugins_json.generate_plugins_json)
    _ecosystem_test.add_command(validate_plugin_yamls.validate_plugin_yamls)
    _ecosystem_test.add_command(
        validate_plugin_version.validate_plugin_version)


_register_commands()

if __name__ == "__main__":
    _ecosystem_test()
