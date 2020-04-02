from ecosystem_cicd_tools.release import plugin_release_with_latest, get_plugin_version


if __name__ == '__main__':
    plugin_release_with_latest('cloudify-ecosystem-tests', get_plugin_version())
