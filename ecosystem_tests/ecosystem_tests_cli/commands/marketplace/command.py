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
from click import option

from ecosystem_tests.ecosystem_tests_cli import (
    ecosystem_tests
)
from ecosystem_cicd_tools.new_cicd.marketplace import (
    get_plugin_id,
    list_versions,
    get_plugin_release_spec_from_marketplace
)

helptext = 'Query the plugin marketplace'
clilogger = logging.getLogger('ecosystem-cli')
clilogger.setLevel(logging.ERROR)
clilogger = logging.getLogger('root')
clilogger.setLevel(logging.ERROR)
logger = logging.getLogger('marketplace-query')
logger.setLevel(logging.INFO)


@ecosystem_tests.command(name='marketplace', short_help=helptext)
@option('-pn', '--plugin-name')
@option('-pv', '--plugin-version')
def marketplace(*args, **kwargs):
    plugin_name = kwargs.get('plugin_name')
    plugin_id = get_plugin_id(plugin_name)
    plugin_version = kwargs.get('plugin_version')
    if not plugin_version:
        plugin_version = list_versions(plugin_id).pop()
    logger.info('Asking the marketplace for...plugin {} {}'.format(
        plugin_name, plugin_version
    ))
    spec = get_plugin_release_spec_from_marketplace(
        plugin_id, plugin_version)
    for yaml_url in spec.get('yaml_urls'):
        if yaml_url['dsl_version'] == 'cloudify_dsl_1_5':
            logger.info('YAML URL: {}'.format(yaml_url.get('url')))
    for wagon_url in spec.get('wagon_urls'):
        if wagon_url['release'] == 'manylinux':
            logger.info('Wagon URL: {}'.format(wagon_url.get('url')))
