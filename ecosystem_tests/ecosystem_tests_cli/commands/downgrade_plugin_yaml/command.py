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

from .utils import add_space
from .contexts import Context
from .options import (
    source,
    target,
    overwrite,
    yaml_path,
    clean_fns,
    v2,
)
from ....ecosystem_tests_cli import ecosystem_tests

helptext = """Create DSL version-specific
compatible plugin YAML files. For example,
downgrade a 1.5 YAML to 1.4.
"""


@ecosystem_tests.command(
    name='downgrade-plugin-yaml',
    short_help=helptext)
@yaml_path
@source
@target
@overwrite
@clean_fns
@v2
def downgrade(yaml_path=None,
              source=None,
              target=None,
              overwrite=False,
              clean_fns=False,
              v2=False):
    yaml_path = yaml_path or 'plugin_1_4.yaml'
    source = source or '1.4'
    target = target or '1.3'
    ctx = Context(yaml_path, source, target, overwrite)
    ctx.full_downgrade()
    ctx.create_new_plugin_yaml(clean_fns)
    if source == '1.4' and target == '1.3' and v2:
        ctx_v2 = Context(yaml_path, target, 'v2', False)
        ctx_v2.create_v2_plugin_yaml(clean_fns)
