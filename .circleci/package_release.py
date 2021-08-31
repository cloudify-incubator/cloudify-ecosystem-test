from os import path, pardir
from ecosystem_cicd_tools.release import (
    plugin_release_with_latest, find_version)

setup_py = path.join(
    path.abspath(path.join(path.dirname(__file__), pardir)),
    'setup.py')

@ecosystem_tests.command(name='release',
                         short_help='package release.')
@ecosystem_tests.options.plugin_name
def package_release(plugin_name):
    plugin_release_with_latest(plugin_name, find_version(setup_py))
