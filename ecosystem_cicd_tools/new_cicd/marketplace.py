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

import requests

URL = 'https://9t51ojrwrb.execute-api.eu-west-1.amazonaws.com/prod/' \
      'scrape-plugins-git-webhook'

1
def call_plugins_webhook(plugin_name, plugin_version, github_user):
    result = requests.post(
        URL,
        {
            'plugin_name': plugin_name,
            'version': plugin_version,
            'creator': github_user,
        }
    )
    if not result.ok:
        raise RuntimeError(
            'Failed to update marketplace with plugin release.')
