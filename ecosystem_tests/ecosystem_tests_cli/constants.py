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

from ..dorkl.constansts import (RERUN,
                                RESUME,
                                UPDATE,
                                CANCEL,
                                TIMEOUT,
                                DONOTHING,
                                ROLLBACK_FULL,
                                UNINSTALL_FORCE,
                                ROLLBACK_PARTIAL,
                                LICENSE_ENVAR_NAME,
                                MANAGER_CONTAINER_ENVAR_NAME)

DEFAULT_BLUEPRINT_PATH = 'blueprint.yaml'
DEFAULT_LICENSE_PATH = 'license.yaml'
DEFAULT_CONTAINER_NAME = 'cfy_manager'
DEFAULT_UNINSTALL_ON_SUCCESS = True
DEFAULT_DIRECTORY_PATH = './'
DEFAULT_REPO = None
DEFAULT_BRANCH = None
