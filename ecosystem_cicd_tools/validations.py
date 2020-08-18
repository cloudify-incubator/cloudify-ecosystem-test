import os
import logging
from re import match
from yaml import safe_load
from yaml.parser import ParserError

from .github_stuff import (
    get_documentation_branches,
    permit_merge,
    get_repository)

VERSION_EXAMPLE = """
version_file = open(os.path.join(package_root_dir, 'VERSION'))
version = version_file.read().strip()"""


def get_plugin_version(file_path=None):
    """

    :param file_path: Should be something like `cloudify-aws-plugin/VERSION`.
    :return: version
    """
    file_path = file_path or os.path.join(
        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                os.pardir
            )
        ),
        'VERSION')
    if not os.path.exists(file_path):
        logging.error(
            'Plugins must store version in a VERSION file in your plugin. '
            'That file should be read into setup.py like this: ' +
            VERSION_EXAMPLE)
        raise Exception('Invalid plugin version storage.')
    with open(file_path) as infile:
        version = infile.read().strip()
        if not bool(match('([\d.]+)[\d$]', version)):
            raise Exception(
                'Version {version} is not a legal version.'.format(
                    version=version))


def read_yaml_file(file_path):
    with open(file_path, 'r') as stream:
        try:
            return safe_load(stream)
        except ParserError:
            logging.error('{path} is not in YAML format.'.format(
                path=file_path))
            raise


def check_changelog_version(version, file_path):
    if version not in read_yaml_file(file_path):
        raise Exception('Version {version} not in {path}.'.format(
            version=version, path=file_path))


def check_plugin_yaml_version(version, file_path):
    """

    :param version:
    :param file_path:
    :return:
    """

    error = False

    logging.debug(
        'Checking plugin YAML version with {version} {file_path}'.format(
            version=version, file_path=file_path))

    plugin_yaml = read_yaml_file(file_path)

    for _, v in plugin_yaml['plugins'].items():

        package_version = v['package_version']
        package_source = v.get('source')

        logging.debug('Package version {package_version}'.format(
            package_version=package_version))
        logging.debug('Package source {package_source}'.format(
            package_source=package_source))

        if version not in package_version:
            error = True
            logging.error('Version {version} '
                          'does not match {package_version}.'.format(
                              version=version,
                              package_version=package_version))

        if package_source and version not in package_source:
            error = True
            logging.error('Version {version} '
                          'does not match {package_source}.'.format(
                              version=version,
                              package_source=package_source))

    if error:
        raise Exception('Version {version} does not match plugin.yaml.')


def validate_plugin_version(plugin_directory=None,
                            version_file='VERSION',
                            plugin_yaml='plugin.yaml',
                            changelog='CHANGELOG.txt'):
    """
    Validate plugin version.

    :param plugin_directory: The script should send the absolute path.
    :param version_file: The name of the file containing the version.
    :param plugin_yaml: The name of the plugin YAML file.
    :param changelog: The name of the CHANGELOG.txt.
    :return:
    """

    plugin_directory = plugin_directory or os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
    version = get_plugin_version(os.path.join(plugin_directory, version_file))
    check_plugin_yaml_version(
        version, os.path.join(plugin_directory, plugin_yaml))
    check_changelog_version(version, os.path.join(plugin_directory, changelog))


def validate_documentation_pulls(commit_message, repo=None):
    """
    Merge any pulls in the docs repo with documentation for this change.
    :param commit_message:
    :param repo:
    :return:
    """
    repo = repo or get_repository(
        org='cloudify-cosmo', repo_name='docs.getcloudify.org')
    branches = get_documentation_branches(commit_message)
    pulls = repo.get_pulls(state='open')
    for branch in branches:
        for pull in pulls:
            if pull.head.ref == branch:
                permit_merge(pull)
