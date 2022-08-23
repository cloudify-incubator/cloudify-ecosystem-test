import os
import time
from copy import deepcopy
from urllib.parse import urlparse
from cfy_lint.yamllint_ext.utils import (get_node_types_for_plugin_version,
                                         get_plugin_versions_from_marketplace,
                                         get_plugin_id_from_marketplace)

from . import s3
from . import github
from . import logging
from . import plugins_json
from . import marketplace


@github.with_github_client
def upload_assets_to_release(assets, release_name, repository, **_):
    """ Upload a bunch of assets to release.
    Example assets:
    {
        'plugin.yaml': 'cloudify-aws-plugin/plugin.yaml',
        'v2_plugin.yaml': 'cloudify-aws-plugin/v2_plugin.yaml',
        'cloudify_aws_plugin-3.0.4-centos-Core-py36-none-linux_aarch64.wgn': 'cloudify-aws-plugin/cloudify_aws_plugin-3.0.4-centos-Core-py36-none-linux_aarch64.wgn',
    }
    Example release name: latest, or '3.0.5'

    :param assets:
    :param release_name:
    :param repository:
    :param _:
    :return:
    """  # noqa

    release_name = release_name or github.get_most_recent_release(repository)

    release = github.get_release(release_name, repository)

    if not release:
        raise RuntimeError(
            'The release {release} does not exist.'.format(release=release))
    for label, path, in assets.items():
        github.upload_asset(release, path, label)
        s3.upload_plugin_asset_to_s3(path, repository.name, release_name)

    if repository.name.endswith('-plugin'):
        marketplace.call_plugins_webhook(
            repository.name,
            release_name,
            os.environ.get('CIRCLE_USERNAME', 'earthmant')
        )

    time.sleep(180)
    plugin_id = get_plugin_id_from_marketplace(assets['plugin.yaml'])
    version = get_plugin_versions_from_marketplace(plugin_id)
    try:
        new_version = version[-1]
        if new_version != release:
            raise RuntimeError(
                'Failed to update marketplace with plugin release.')

        node_types = get_node_types_for_plugin_version(assets['plugin.yaml'],
                                                       version)
        if not node_types:
            raise RuntimeError(
                'Failed to update marketplace with plugin release.')
    except:
        raise RuntimeError(
            'Failed to update marketplace with plugin release.')


@github.with_github_client
def get_latest_version(repository, **kwargs):
    logging.logger.info(
        'Getting latest version for {}/{}'.format(
            kwargs.get('organization_name'),
            kwargs.get('repository_name')
        )
    )
    latest_release = github.get_most_recent_release(repository)
    logging.logger.info('Got this version: {}'.format(latest_release))
    return latest_release


def populate_plugins_json(plugin_yaml_name='plugin.yaml'):
    json_content = []
    for i in range(0, len(plugins_json.JSON_TEMPLATE)):
        plugin_content = deepcopy(plugins_json.JSON_TEMPLATE[i])
        parsed_url = urlparse(plugin_content['releases'])
        repository_name = parsed_url.path.split('/')[-2]
        assert repository_name == plugin_content['name']
        organization_name = parsed_url.path.split('/')[-3]
        version = get_latest_version(
            repository_name=repository_name,
            organization_name=organization_name)
        logging.logger.info('Got this version: {}'.format(version))
        plugin_yaml_url = s3.get_plugin_yaml_url(
            plugin_name=repository_name,
            filename=plugin_yaml_name,
            plugin_version=version,
        )
        wagons_list = plugins_json.get_wagons_list(
            plugin_name=repository_name,
            plugin_version=version
        )
        plugin_content = deepcopy(plugins_json.JSON_TEMPLATE[i])
        plugin_content['version'] = version
        plugin_content['link'] = plugin_yaml_url
        plugin_content['yaml'] = plugin_yaml_url
        plugin_content['wagons'] = wagons_list
        json_content.append(plugin_content)
    return json_content
