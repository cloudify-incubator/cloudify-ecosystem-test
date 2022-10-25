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
TIMEOUT = 1800
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
