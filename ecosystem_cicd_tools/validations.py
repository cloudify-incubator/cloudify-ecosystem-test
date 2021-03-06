import os
import sys
import logging
import subprocess
from re import match
from yaml import safe_load
from yaml.parser import ParserError

from .github_stuff import (
    raise_if_unmergeable,
    get_pull_request_jira_ids,
    get_repository,
    get_pull_request,
    find_pull_request_number,
    validate_docs_requirement)

VERSION_EXAMPLE = """
version_file = open(os.path.join(package_root_dir, 'VERSION'))
version = version_file.read().strip()"""

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


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
    logging.info('Version {version} is in CHANGELOG.'.format(version=version))


def check_setuppy_version(version, plugin_directory):
    command = '{exec_path} {path} --version'.format(
        exec_path=sys.executable,
        path=os.path.join(plugin_directory, 'setup.py'))
    output = subprocess.check_output(command, shell=True)
    output = output.decode("utf-8")
    if version.strip() != output.strip():
        raise Exception('Plugin YAML {version} does not match '
                        'setup.py {output}.'.format(version=version.strip(),
                                                    output=output.strip()))
    logging.info('Version {version} matches {output}.'.format(
        version=version, output=output))


def read_plugins(file_path):
    plugin_yaml = read_yaml_file(file_path)
    return plugin_yaml['plugins']


def get_plugin_yaml_version(file_path):
    """

    :param file_path:
    :return:
    """

    logging.debug(
        'Checking plugin YAML version with {file_path}'.format(
            file_path=file_path))

    plugins_section = read_plugins(file_path)

    package_version = None
    for _, v in plugins_section.items():

        if package_version and v['package_version'] != package_version:
            raise Exception('More than one plugin version is defined.')

        package_version = v['package_version']
        package_source = v.get('source')

        logging.debug('Package version {package_version}'.format(
            package_version=package_version))
        logging.debug('Package source {package_source}'.format(
            package_source=package_source))

        if not package_version:
            raise Exception('Version not specified in plugin YAML.')

        if package_source and package_version not in package_source:
            raise Exception('Version {version} '
                            'does not match {package_source}.'.format(
                                version=package_version,
                                package_source=package_source))
    return package_version


def validate_plugin_version(plugin_directory=None,
                            plugin_yaml='plugin.yaml',
                            changelog='CHANGELOG.txt'):
    """
    Validate plugin version.

    :param plugin_directory: The script should send the absolute path.
    :param plugin_yaml: The name of the plugin YAML file.
    :param changelog: The name of the CHANGELOG.txt.
    :return:
    """

    plugin_directory = plugin_directory or os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
    version = get_plugin_yaml_version(
        os.path.join(plugin_directory, plugin_yaml))
    check_changelog_version(version, os.path.join(plugin_directory, changelog))
    check_setuppy_version(version, plugin_directory)
    return version


def _validate_documenation_pulls(docs_repo, jira_ids):
    merges = 0
    pulls = docs_repo.get_pulls(state='open')
    for jira_id in jira_ids:
        for pull in pulls:
            if jira_id in pull.head.label:
                raise_if_unmergeable(pull)
                merges += 1
    if not merges:
        raise Exception('No documentation PRs were found.')


def validate_documentation_pulls(repo=None, docs_repo=None, branch=None):
    """
    Check that we are providing documentation.
    :param repo: The current repo (a plugin for example).
    :param docs_repo: The repo to check for Docs PRs.
    :param branch: The current branch. 
    :return:
    """

    logging.info('Validating documentation pull requests are ready.')
    repo = repo or get_repository()
    docs_repo = docs_repo or get_repository(
        org='cloudify-cosmo', repo_name='docs.getcloudify.org')

    branch = branch or os.environ.get('CIRCLE_BRANCH')
    logging.info('Checking pull requests for {branch}'.format(branch=branch))
    pull_request_number = find_pull_request_number(branch, repo)
    if not pull_request_number and branch != 'master':
        logging.info('A PR has not yet been opened.')
        return

    pull_request = get_pull_request(pull_request_number)
    jira_ids = get_pull_request_jira_ids(pull=pull_request)

    for commit in pull_request.get_commits():
        if not validate_docs_requirement(commit.commit.message):
            return
    _validate_documenation_pulls(docs_repo, jira_ids)
