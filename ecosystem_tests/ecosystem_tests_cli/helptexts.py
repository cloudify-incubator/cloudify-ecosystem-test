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

BLUEPRINT_PATH = 'Blueprint path, This option can be used multiple times.'

INPUTS_PARAMS_USAGE = (
    '(Can be provided as path to YAML file, or as '
    '\'key1=value1;key2=value2\'). This argument can be used multiple times.'
)

INPUTS = "Test inputs {0}".format(INPUTS_PARAMS_USAGE)

TEST_TIMEOUT = 'Test timeout (seconds).'

TEST_ID = 'Test id, the name of the test deployment.'

NESTED_TEST = 'Nested tests, will run by pytest, should be specified in the ' \
              'pytest notation like: path/to/module.py::TestClass::test_method'

LICENSE = 'Licence for the manager, should be either path to licence file ' \
          'or base64 encoded licence string.'

SECRETS = 'A secret to update on the manager, should be provided as' \
          ' secret_key=secret_value. This argument can be used multiple times.'

FILE_SECRETS = 'A secret to update on the manager, should be provided as' \
               ' secret_key=file_path. This argument can be used' \
               ' multiple times.'

ENCODED_SECRETS = 'Base 64 encoded secret to update on the manager, ' \
                  'should be provided as ' \
                  'secret_key=secret_value_base_64_encoded. This argument ' \
                  'can' \
                  ' be used multiple times.'

CONTAINER_NAME = 'Manager docker container name. ' \
                 'Default: MANAGER_CONTAINER environment variable or ' \
                 '"cfy_manager" if there is no such environment variable.'

PLUGINS = 'Plugin to upload before test ivocation, shuld be provided as ' \
          '--plugin plugin_wagon_url plugin.yaml_url. ' \
          'This argument can be used multiple times.'

BUNDLE = 'Plugins bundle tgz file path.'

NO_BUNDLE = 'Specify --skip-bundle-upload for not uploading plugins bundle' \
            ' before the test.'

SUBSEQUENT_INVOKE = 'Which action to perform on subsequent invocation of ' \
                    'the test (same test id).Should be one of: ' \
                    'resume, rerun, update.'

ON_FAILURE = 'Which action to perform on test failure.' \
             'Should be one of: false(do nothing), rollback-full, ' \
             'rollback-partial, uninstall-force'

UNINSTALL_ON_SUCCESS = 'Whehter to perform uninstall if the test succeeded,' \
                       'and delete the test blueprint.'
