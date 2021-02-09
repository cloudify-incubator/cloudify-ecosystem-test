import requests

from .exceptions import EcosystemTestCliException


def create_plugins_list(plugins):
    """Returns a list of tuples of plugins to upload.
       each tuple look like:(wagon_url,plugin.yaml_url)
    :param plugins: tuple of tuples consists of the usr input for plugin
    option.
    """
    plugins_list = []
    for plugin_tuple in plugins:
        check_valid_urls(plugin_tuple)
        # In case the user insert the plugin.yaml as the first argument.
        wagon, yaml = find_wagon_yaml_url(plugin_tuple)
        plugins_list.append((wagon, yaml))
    return plugins_list


def check_valid_urls(plugin_tuple):
    for url in plugin_tuple:
        request = requests.head(url)
        if request.status_code != requests.codes.found and \
                request.status_code != requests.codes.ok:
            raise EcosystemTestCliException('plugin url {url}'
                                            ' is not valid!'.format(url=url))


def find_wagon_yaml_url(plugin_tuple):
    try:
        wagon = \
            [element for element in plugin_tuple if element.endswith('.wgn')][
                0]
        pl_yaml = \
            [element for element in plugin_tuple if element.endswith('.yaml')][
                0]
        return wagon, pl_yaml
    except IndexError:
        raise EcosystemTestCliException(
            'Plugin input -Could not find which url is for wagon and which '
            'is for plugin.yaml for: {plugins}'.format(
                plugins=plugin_tuple))
