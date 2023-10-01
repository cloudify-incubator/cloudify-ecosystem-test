import os
import re
import sys
import yaml
import logging
import subprocess
from re import match, compile
from yaml import safe_load
from yaml.parser import ParserError

try:
    from packaging.version import parse as parse_version
except ImportError:
    from distutils.version import LooseVersion as parse_version

from .github_stuff import (
    raise_if_unmergeable,
    get_pull_request_jira_ids,
    get_repository,
    get_pull_requests,
    find_pull_request_numbers,
    check_if_label_in_pr_labels)
from .new_cicd.github import (
    with_github_client,
    get_list_of_commits_from_branch
)

VERSION_EXAMPLE = """
version_file = open(os.path.join(package_root_dir, 'VERSION'))
version = version_file.read().strip()"""

CHANGELOG = 'CHANGELOG.txt'
INCLUDE_NAMES = ['plugin.yaml', 'v2_plugin.yaml']
PLUGIN_PACKAGES = ['fabric_plugin' ,
                   'openstack_plugin',
                   'serverless_plugin', 
                   'managed_nagios_plugin']

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def does_protected_branch_have_build_source(pr):
    string_pattern = '[0-9.]*-build'
    patt = compile(string_pattern)
    if pr.base.ref in ['main', 'master'] and not patt.match(pr.head.ref):
        logging.error(
            'Protected branches "main" and "master" require build branch. '
            'Branch name is {}'.format(pr.head.ref))
        sys.exit(1)


@with_github_client
def validate_pulls(repo_name=None,
                   branch_name=None,
                   github_client=None,
                   repository=None,
                   **kwargs):
    if repo_name:
        repo = github_client.get_repo(
            '{}/{}'.format(kwargs.get('organization_name'), repo_name))
        pulls = repo.get_pulls()
    else:
        pulls = repository.get_pulls()
    for pull in pulls:
        if pull.head.ref == branch_name:
            does_protected_branch_have_build_source(pull)


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
    logging.info('OPENING: {}'.format(file_path))
    with open(file_path, 'r') as stream:
        try:
            return safe_load(stream)
        except ParserError:
            logging.error('{path} is not in YAML format.'.format(
                path=file_path))
            raise


def update_changelog(plugin_directory, branch_name, version):

    commits_from_branch = get_list_of_commits_from_branch(branch_name)

    changelog_yaml = read_yaml_file(
        os.path.join(plugin_directory, CHANGELOG)) or {}
    commits_from_changelog = changelog_yaml.get(version, [])

    # need to be list type
    if isinstance(commits_from_changelog, str):
        commits_from_changelog = [commits_from_changelog]

    # Go through the list of commit_message in *-Build
    for commit_message in commits_from_branch:
        # If the message is not already in the changelog Add it
        if commit_message.commit.message not in commits_from_changelog:
            commits_from_changelog.append(commit_message.commit.message)

    # Overwrite the list with the updated list
    changelog_yaml[version] = commits_from_changelog
    with open(os.path.join(plugin_directory, CHANGELOG), 'w') as f:
        yaml.dump(changelog_yaml,
                  f,
                  default_flow_style=False)


def check_changelog_version(version, file_path):
    if not check_is_latest_version(version, file_path):
        raise Exception('Version {version} not in {path}.'.format(
            version=version, path=file_path))


def check_is_latest_version(version, file_path):
    dict_file = read_yaml_file(file_path)
    list_of_versions = []
    for i in dict_file:
        list_of_versions.append(str(i))

    sorted_l = sorted(list_of_versions, key=parse_version)
    return version == sorted_l.pop()


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


def read_file(rel_path):
    with open(rel_path, 'r') as fp:
        return fp.read()


def get_version_py(plugin_directory):
    for f in os.listdir(plugin_directory):
        """ The folders we are looking for 'cloudify_{name}' This is the template.
        But fabric_plugin is an exception."""
        if os.path.isdir(f) and is_valid_plugin_package_name(f):
            lib = os.path.join(plugin_directory, f)
            if not os.path.isdir(lib):
                continue
            for file in os.listdir(lib):
                if '__version__.py' == file:
                    line = read_file(os.path.join(lib, file))
                    # The version line.
                    return re.search(r"\d+\.\d+\.\d+", line).group()
            raise Exception(
                'Failed to get version from file __version__.py')


def is_valid_plugin_package_name(f):
    is_package_special_name = f in PLUGIN_PACKAGES
    is_bad_details = (f.startswith('.') or 
                      'egg-info' in f or 
                      f == 'cover' or
                      f == 'examples' or 
                      'sdk' in f)
    is_correct_name = f.startswith('cloudify_')

    return (is_package_special_name or is_correct_name) and not is_bad_details


def get_plugins(path):
    """
    Returns a list of yaml files.
    like: [plugin.yaml , plugin_1_4.yaml, plugin_1_5.yaml, plugin_v2.yaml]
    """
    assets_list = []
    search_string = '^plugin_\\d+_\\d+\\.yaml$'
    if os.path.exists(path):
        for f in os.listdir(path):
            if f in INCLUDE_NAMES:
                assets_list.append(f)
            name = re.search(search_string, f)
            if name and f == name.group():
                assets_list.append(f)

    if not assets_list:
        raise Exception('Failed to get the plugin list')
    return assets_list


def get_version_in_plugin(rel_file, name):
    lines = read_file(os.path.join(rel_file, name))
    for line in lines.splitlines():
        if 'package_version' in line:
            split_line = line.split(':')
            line_no_space = split_line[-1].replace(' ', '')
            line_no_quotes = line_no_space.replace('\'', '')
            return line_no_quotes.strip('\n')


def validate_plugin_version(plugin_directory=None, branch_name=None):
    """
    Validate plugin version.
    :param plugin_directory: The script should send the absolute path.
    :param branch_name: The name of the branch if its *-build.
    :return: official version
    """

    plugin_directory = plugin_directory or os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

    plugins_asset = get_plugins(plugin_directory)
    version = get_version_py(plugin_directory)

    # check and update all plugins yaml
    check_version_plugins_and_update(plugin_directory, plugins_asset, version)

    # check or update (CHANGELOG if "*-build" branch name)
    if branch_name:
        update_changelog(plugin_directory, branch_name, version)
    else:
        check_changelog_version(version,
                                os.path.join(plugin_directory, CHANGELOG))
    logging.info('The official version of this plugin is {version}'
                 .format(version=version))
    return version


def check_version_plugins_and_update(path, plugins, version):
    path_plugin = os.path.join(os.path.abspath(path))
    for file_name in plugins:
        version_in_plugin = get_version_in_plugin(path_plugin, file_name)
        if version_in_plugin > version:
            raise Exception('Version mismatch, please check manually.'
                            ' The version in {file_name} is greater than '
                            '__verison__.py'
                            .format(file_name=file_name,
                                    version_in_plugin=version_in_plugin,
                                    version=version ))
        if version_in_plugin != version:
            edit_version_in_plugin_yaml(path_plugin, file_name, version)


def edit_version_in_plugin_yaml(rel_file, file_name, version):
    logging.info('Update version in {}'.format(file_name))
    pattern = re.compile("(package_version:\s*)'\d+.\d+.\d+'")
    replacement = "package_version: '{}'".format(version)

    with open(os.path.join(rel_file, file_name), 'r') as f:
        lines = f.readlines()
    c = -1
    for line in lines:
        c += 1
        if pattern.search(line):
            break

    lines[c] = re.sub(pattern, replacement, lines[c])
    with open(os.path.join(rel_file, file_name), 'w') as fp:
        fp.writelines(lines)


def _validate_documenation_pulls(docs_repo, jira_ids):
    merges = 0
    pulls = docs_repo.get_pulls(state='open')
    logging.info('validate documentation pulls jira_ids = {}'.format(jira_ids))
    for jira_id in jira_ids:
        for pull in pulls:
            if jira_id in pull.head.label:
                raise_if_unmergeable(pull)
                merges += 1
    if not merges:
        raise Exception(
            'No documentation PRs were found in {}. '
            'If your PR includes the label "enhancement", '
            'then you are expected to submit docs PRs. '.format(
                docs_repo.name))


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

    pr_numbers = find_pull_request_numbers(branch, repo)
    if not pr_numbers and branch not in ['master', 'main', '2.X-master']:
        logging.info('A PR has not yet been opened.')
        return
    logging.info('Found these PR numbers: {}'.format(pr_numbers))

    pull_requests = get_pull_requests(pr_numbers)
    logging.info('Found these PRs: {}'.format(pull_requests))
    jira_ids = get_pull_request_jira_ids(pulls=pull_requests)

    if not check_if_label_in_pr_labels(pr_numbers):
        return
    _validate_documenation_pulls(docs_repo, jira_ids)
