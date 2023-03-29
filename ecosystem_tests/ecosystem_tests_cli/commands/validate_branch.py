import os
import re
from ..logger import logger
from ...ecosystem_tests_cli import ecosystem_tests
from ecosystem_tests.dorkl.commands import handle_process
from ecosystem_cicd_tools.validations import validate_pulls


@ecosystem_tests.command(name='validate-pulls',
                         short_help='validate pulls.')
@ecosystem_tests.options.repo
@ecosystem_tests.options.branch
def validate_pull_request(repo, branch):
    repo = repo or get_repo()
    branch = branch or get_branch()
    logger.info('Checking branch {} on repo {}'.format(branch, repo))
    validate_pulls(repo, branch)


def get_branch():
    if 'CIRCLE_BRANCH' in os.environ:
        return os.environ['CIRCLE_BRANCH']
    command = 'git rev-parse --abbrev-ref HEAD'
    return get_git_data(command)


def get_repo():
    if 'CIRCLE_PROJECT_REPONAME' in os.environ:
        return os.environ['CIRCLE_PROJECT_REPONAME']
    command = 'git remote get-url origin'
    repo_url = get_git_data(command)
    if repo_url:
        return re.split(r'\.|\/', repo_url)[-2]


def get_git_data(command):
    try:
        return handle_process(command)
    except Exception:
        logger.error('Failed to resolve command: {}'.format(command))
