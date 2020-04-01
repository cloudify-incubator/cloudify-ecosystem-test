
import os
from ecosystem_cicd_tools import release


if __name__ == '__main__':

    setup_py = os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)),
        'setup.py')
    version = release.find_version(setup_py)
    current_repo = release.get_repository()
    version_release = release.get_release(version)
    commit = release.get_commit()
    if not version_release:
        release.create_release(
            version, version, "cloudify-ecosystem-tests-v{0}".format(version),
            commit)
    latest_release = release.get_most_recent_release()
    if not latest_release:
        release.create_release('latest')
    release.update_release(
        "latest",
        "The latest release is version {0}.".format(version),
    )
    release.update_latest_release_resources(version)
