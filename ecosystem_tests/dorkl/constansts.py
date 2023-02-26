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

import logging
logging.basicConfig()
logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)

MANAGER_CONTAINER_ENVAR_NAME = 'MANAGER_CONTAINER'
TIMEOUT = 2000
VPN_CONFIG_PATH = '/tmp/vpn.conf'
LICENSE_ENVAR_NAME = 'TEST_LICENSE'

RESUME = 'resume'
RERUN = 'rerun'
UPDATE = 'update'

CANCEL = 'cancel'
DONOTHING = 'donothing'
UNINSTALL_FORCE = 'uninstall-force'
ROLLBACK_FULL = 'rollback-full'
ROLLBACK_PARTIAL = 'rollback-partial'

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
PINK = '\033[95m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

DOCKER_MGMT_COMMANDS = """alias jqids="jq -r '.[].id'"

xplugins () {
    for plugin in `cfy plugins list --json | jqids`;
        do cfy plugins delete $plugin;
        done
}

xexec () {
    for deployment in `cfy deployments list --json | jqids`;
        do cfy uninstall -p ignore_failure=true $deployment
        done
}

xdep () {
    for deployment in `cfy deployments list --json | jqids`;
        do cfy deployments delete $deployment
        done
}

xblue () {
    for blueprint in `cfy blueprints list --json | jqids`;
        do cfy blueprints delete $blueprint
        done
}

getpluginbyname () {
    cfy plugins list --json | \
        jq -c --arg var $1 '.[] | select( .package_name | contains($var))'
}

getpluginids () {
    getpluginbyname $1 | jq -r '.id'
}

xplugin () {
    for plugin in `getpluginids $1`;
        do cfy plugins delete $plugin
        done
}
"""
