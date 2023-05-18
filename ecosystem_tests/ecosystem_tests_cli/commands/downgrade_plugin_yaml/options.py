########
# Copyright (c) 2014-2023 Cloudify Platform Ltd. All rights reserved
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


from click import BOOL, option, STRING


yaml_path = option(
    '-PYP',
    '--yaml-path',
    type=STRING,
    help='Path to Plugin YAML, '
         'e.g --plugin-yaml-path plugin_1_5.yaml'
)
source = option(
    '-s',
    '--source',
    type=STRING,
    help='Either 1.4 or 1.5.'
)
target = option(
    '-t',
    '--target',
    type=STRING,
    help='Either 1.3 or 1.4.'
)
overwrite = option(
    '-xw',
    '--overwrite',
    type=BOOL,
    is_flag=True,
    help='To overwrite target '
    '(e.g., 1.3 is plugin.yaml 1.4 is plugin_1_4.yaml).'
)
clean_fns = option(
    '-xfn',
    '--clean-fns',
    type=BOOL,
    is_flag=True,
    help='Remove single quotes in intrinsic fns.'
)
