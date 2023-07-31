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

import re

def get_lines_file(ctx):
    file = open(ctx.absolute_source_path, 'r')
    yaml_lines = file.readlines()
    file.close()
    return yaml_lines

def write_content_to_file(file_path, content):
    with open(file_path, 'w') as file:
        for line in content:
            file.write(line)


def add_space(ctx):
    index = 0
    pattern = r'^(?! +)([a-zA-Z_]+):'
    yaml_lines = get_lines_file(ctx)
    for line in yaml_lines:
        matches = re.findall(pattern, line)
        if matches:
            yaml_lines[index - 1] = yaml_lines[index - 1].replace('\n', '\n')
        index +=1
    write_content_to_file(ctx.absolute_target_path, yaml_lines)

