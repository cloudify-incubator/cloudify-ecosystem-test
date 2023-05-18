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

import yaml

CONCAT = 'concat'
GET_SYS = 'get_sys'
GET_INPUT = 'get_input'
GET_SECRET = 'get_secret'
GET_PROPERTY = 'get_property'
GET_ATTRIBUTE = 'get_attribute'
GET_CAPABILITY = 'get_capability'
GET_ENVIRONMENT_CAPABILITY = 'get_environment_capability'
INSTRINSIC_FUNCTIONS = [
    CONCAT,
    GET_SYS,
    GET_INPUT,
    GET_SECRET,
    GET_PROPERTY,
    GET_ATTRIBUTE,
    GET_CAPABILITY,
    GET_ENVIRONMENT_CAPABILITY
]


class CloudifyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = super(CloudifyLoader, self).construct_mapping(
            node, deep=deep)
        return mapping


def repr_str(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar(
            u'tag:yaml.org,2002:str', data, style='>')
    return dumper.org_represent_str(data)


def represent_intrinsic_functions(dumper, data):
    for fn in INSTRINSIC_FUNCTIONS:
        if fn in data:
            return dumper.org_represent_str(
                '{{ {fn}: {val} }}'.format(fn=fn, val=data[fn]))
    return dumper.represent_dict(data)


def increase_indent(self, flow=False, indentless=False):
    indentless = indentless if not indentless else False
    self.indents.append(self.indent)
    if self.indent is None:
        if flow:
            self.indent = self.best_indent
        else:
            self.indent = 0
    elif not indentless:
        self.indent += self.best_indent


yaml.SafeDumper.org_represent_str = yaml.SafeDumper.represent_str
yaml.add_representer(str, repr_str, Dumper=yaml.SafeDumper)
yaml.add_representer(
    dict, represent_intrinsic_functions, Dumper=yaml.SafeDumper)
yaml.SafeDumper.increase_indent = increase_indent
yaml.SafeDumper.add_representer(
    type(None),
    lambda dumper, _: dumper.represent_scalar(u'tag:yaml.org,2002:null', '~')
  )


def load_yaml(path):
    f = open(path)
    content = yaml.load(f, CloudifyLoader)
    f.close()
    return content


def dump_yaml(data, path, clean_fns=False):
    with open(path, 'w') as f:
        yaml.safe_dump(
            data,
            f,
            default_flow_style=False,
            sort_keys=False,
            width=float('inf')
        )
    if clean_fns:
        fin = open(path, 'r')
        lines = fin.readlines()
        fin.close()
        fou = open(path, 'w')
        for line in lines:
            for fn in INSTRINSIC_FUNCTIONS:
                if fn in line:
                    line = line.replace("'", '')
                    break
            fou.write(line)
        fou.close()
