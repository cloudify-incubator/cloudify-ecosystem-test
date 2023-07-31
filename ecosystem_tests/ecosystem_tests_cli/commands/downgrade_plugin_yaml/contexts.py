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

import os
import re
import sys
from pathlib import Path
from .yaml import (
    dump_yaml,
    load_yaml
)

from ...logger import logger

OBJECT_BASED_TYPES_DSL_1_4 = [
    'blueprint_id', 'deployment_id', 'capability_value', 'scaling_group',
    'node_id', 'node_type', 'node_instance', 'secret_key', ]
OBJECT_BASED_TYPES_DSL_1_5 = ['operation_name', ]

class FileContext(object):
    def __init__(self, path, filename, overwrite=False):
        self._path = path
        self._filename = filename
        self._path_obj = None
        self._parent_path_obj = None
        self._target_path_obj = None
        self.overwrite = overwrite
        self.set_source_path()
        self.setup_target()

    @property
    def path_object(self):
        return self._path_obj

    @property
    def parent_path_object(self):
        return self.path_object.parent

    @property
    def target_path_object(self):
        return self._target_path_obj

    def set_source_path(self):
        path = Path(self._path)
        self._path_obj = Path(self._path)
        if not self._path_obj.exists():
            logger.error(
                'The source plugin YAML file {} does not exist.'.format(
                    path))
            sys.exit(1)

    def setup_target(self):
        new_filepath = Path(self.parent_path_object.absolute(), self._filename)
        if self.overwrite and new_filepath.exists():
            os.remove(new_filepath.absolute())
        elif new_filepath.exists():
            logger.error(
                'The new file {} already exists. '
                'Either use that file or delete it.'.format(
                    new_filepath.absolute())
            )
            sys.exit(1)
        self._target_path_obj = new_filepath


class Context(object):

    def __init__(self,
                 path,
                 source=None,
                 target=None,
                 overwrite=False):
        self._data = {}
        self._source = source
        self._target = target
        self._filename = None
        self.set_filename()
        self.file = FileContext(path, self._filename, overwrite)
        self.load_data()
        logger.info(
            'Downgrading {} from version {} to version {}'.format(
                self.absolute_target_path,
                self.source,
                self.target
            )
        )

    @property
    def absolute_target_path(self):
        return self.file.target_path_object.absolute()

    @property
    def absolute_source_path(self):
        return self.file.path_object.absolute()

    @property
    def parent_dir(self):
        return self.file.parent_path_object.absolute()

    @property
    def source(self):
        return self._source

    @property
    def target(self):
        return self._target

    @property
    def data(self):
        return self._data

    def set_filename(self):
        if self.target == 'v2' and self.source == '1.3':
            self._filename = 'v2_plugin.yaml'
        elif self.source == '1.5' and self.target == '1.4':
            self._filename = 'plugin_1_4.yaml'
        elif self.source == '1.5':
            logger.error(
                'Invalid target for source. '
                '1.5 can only be transformed to 1.4.'
            )
            sys.exit(1)
        elif self.source == '1.4' and self.target == '1.3':
            self._filename = 'plugin.yaml'
        else:
            logger.error(
                'Invalid source-target configuration. '
                'Only 1.5 > 1.4 and 1.4 > 1.3 are supported.'
                'Source: {}. Target: {}.'.format(self.source,
                                                 self.target)
            )
            sys.exit(1)

    def load_data(self):
        self._data = load_yaml(self.absolute_source_path)

    def create_new_plugin_yaml(self, clean_fns=False):
        if not self.file.target_path_object.exists():
            self.file.target_path_object.touch()
        dump_yaml(self.data, self.absolute_target_path, clean_fns)
        logger.info('Wrote new plugin yaml at {}'.format(
            self.absolute_target_path))

    def downgrade_labels(self):
        labels = self._data.get('labels')
        if not (self.source == '1.4' and self.target == '1.3'):
            return
        elif labels:
            del self._data['labels']

    def downgrade_blueprint_labels(self):
        blueprint_labels = self._data.get('blueprint_labels')
        if not (self.source == '1.4' and self.target == '1.3'):
            return
        elif blueprint_labels:
            del self._data['blueprint_labels']

    def downgrade_nested(self, nested_dict, new_nested_dict=None):
        new_nested_dict = new_nested_dict or {}
        if not (self.source == '1.4' and self.target == '1.3') \
                and not (self.source == '1.5' and self.target == '1.4'):
            return
        elif nested_dict:
            for name, value in list(nested_dict.items()):
                if self.source == '1.4' and self.target == '1.3':
                    value = self.convert_to_dsl_1_3_types(value)
                elif self.source == '1.5' and self.target == '1.3':
                    value = self.convert_to_dsl_1_4_types(value)
                if value:
                    new_nested_dict[name] = value
        return new_nested_dict

    def downgrade_interfaces(self):
        types = self._data.get('node_types', {})
        for type_name, type_value in list(types.items()):
            interfaces = type_value.get('interfaces', {})
            for interface_name, interface_value in list(interfaces.items()):
                for op_name, op_value in list(interface_value.items()):
                    if isinstance(op_value, str):
                        continue
                    op_inputs = op_value.get('inputs', {})
                    if op_inputs:
                        op_value['inputs'] = self.downgrade_nested(op_inputs)
                    interface_value[op_name] = op_value
                interfaces[interface_name] = interface_value
            if interfaces:
                type_value['interfaces'] = interfaces
            self._data['node_types'][type_name] = type_value

    def downgrade_relationship_interfaces(self):
        types = self._data.get('relationships', {})
        for type_name, type_value in list(types.items()):
            for direction in ['source_interfaces', 'target_interfaces']:
                ifaces = type_value.get(direction, {})
                if ifaces:
                    for interface_name, iface_value in list(
                            ifaces.items()):
                        for op_name, op_value in list(iface_value.items()):
                            if isinstance(op_value, str):
                                continue
                            op_inputs = op_value.get('inputs', {})
                            if op_inputs:
                                op_value['inputs'] = self.downgrade_nested(
                                    op_inputs)
                                iface_value[op_name] = op_value
                        ifaces[interface_name] = iface_value
                    if ifaces:
                        type_value[direction] = ifaces
            self._data['relationships'][type_name] = type_value

    def downgrade_types(self, types_key, internal=None):
        internal = internal or 'properties'
        types = self._data.get(types_key)
        if not (self.source == '1.4' and self.target == '1.3') \
                and not (self.source == '1.5' and self.target == '1.4'):
            return
        elif types:
            for type_name, type_def in list(types.items()):
                properties = type_def.get(internal, {})
                for prop_name, prop_def in list(properties.items()):
                    if self.source == '1.4' and self.target == '1.3':
                        properties[prop_name] = \
                            self.convert_to_dsl_1_3_types(prop_def)
                    elif self.source == '1.5' and self.target == '1.3':
                        properties[prop_name] = \
                            self.convert_to_dsl_1_4_types(prop_def)
                if properties:
                    type_def[internal] = properties
                types[type_name] = type_def
            self._data[types_key] = types

    def downgrade_node_types(self):
        self.downgrade_types('node_types')
        self.downgrade_interfaces()

    def downgrade_data_types(self):
        self.downgrade_types('data_types')

    def downgrade_workflow_params_types(self):
        self.downgrade_types('workflows', 'parameters')

    def convert_to_dsl_1_3_types(self, prop_def):
        prop_type = prop_def.get('type')
        if prop_type in OBJECT_BASED_TYPES_DSL_1_4:
            prop_def['type'] = 'string'
        if 'item_type' in prop_def:
            del prop_def['item_type']
        if 'constraints' in prop_def:
            del prop_def['constraints']
        if 'display_label' in prop_def:
            del prop_def['display_label']
        if 'hidden' in prop_def:
            del prop_def['hidden']
        if 'constraints' in prop_def:
            del prop_def['display']
        if 'description' in prop_def:
            # Deleting because this has no functional value.
            del prop_def['description']
        return prop_def

    def convert_to_dsl_1_4_types(self, prop_def):
        prop_type = prop_def.get('type')
        if prop_type in OBJECT_BASED_TYPES_DSL_1_5:
            prop_def['type'] = 'string'
        return prop_def

    def full_downgrade(self):
        self.downgrade_labels()
        self.downgrade_blueprint_labels()
        self.downgrade_data_types()
        self.downgrade_node_types()
        self.downgrade_workflow_params_types()
        self.downgrade_relationship_interfaces()

    def create_v2_plugin_yaml(self, clean_fns):
        dictionary = self._data.get('plugins', {})
        key = list(dictionary.keys())[0]
        blueprint_labels = {
            'obj-type': {
                'values': [key]
            }
        }
        labels = {
            'obj-type': {
                'values': [key]
            }
        }

        if not self.file.target_path_object.exists():
            self.file.target_path_object.touch()

        self._data = load_yaml('plugin.yaml')
        self._data['blueprint_labels'] = blueprint_labels
        self._data['labels'] = labels
        self.create_new_plugin_yaml(clean_fns)

    def get_lines_file(self):
        file = open(self.absolute_source_path, 'r')
        yaml_lines = file.readlines()
        file.close()
        return yaml_lines

    def write_content_to_file(self, file_path, content):
        with open(file_path, 'w') as file:
            for line in content:
                file.write(line)


    def add_space(self):
        index = 0
        pattern = r'^(?! +)([a-zA-Z_]+):'
        yaml_lines = self.get_lines_file()
        for line in yaml_lines:
            matches = re.findall(pattern, line)
            if matches:
                yaml_lines[index - 1] = yaml_lines[index - 1].replace('\n', '\n\n')
            index +=1
        self.write_content_to_file(self.absolute_target_path, yaml_lines)

    