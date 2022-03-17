from ecosystem_cicd_tools.packaging import build_plugins_bundle


if __name__ == '__main__':
    build_plugins_bundle()
    build_plugins_bundle(v2_bundle=True)
