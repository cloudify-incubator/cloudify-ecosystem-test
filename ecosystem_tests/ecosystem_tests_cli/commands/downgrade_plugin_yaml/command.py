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

from .contexts import Context
from .options import (
    source,
    target,
    overwrite,
    yaml_path,
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
def downgrade(yaml_path=None,
              source=None,
              target=None,
              overwrite=False):
    yaml_path = yaml_path or 'plugin_1_4.yaml'
    source = source or '1.4'
    target = target or '1.3'
    ctx = Context(yaml_path, source, target, overwrite)
    ctx.full_downgrade()
    ctx.create_new_plugin_yaml()
