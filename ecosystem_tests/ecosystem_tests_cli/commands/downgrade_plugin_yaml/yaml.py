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

from yaml import SafeDumper
import yaml

SafeDumper.add_representer(
    type(None),
    lambda dumper, _: dumper.represent_scalar(u'tag:yaml.org,2002:null', '~')
  )


def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def dump_yaml(data, path):
    with open(path, 'w') as f:
        yaml.safe_dump(
            data,
            f,
            default_flow_style=False,
            sort_keys=False)
