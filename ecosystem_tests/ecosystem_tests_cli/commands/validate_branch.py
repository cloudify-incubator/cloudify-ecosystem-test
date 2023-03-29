from ecosystem_cicd_tools.validations import validate_pulls
from ecosystem_tests.dorkl.commands import handle_process
from ...ecosystem_tests_cli import ecosystem_tests
from ..logger import logger
import re


@ecosystem_tests.command(name='validate-pulls',
                         short_help='validate pulls.')
@ecosystem_tests.options.repo
@ecosystem_tests.options.branch
def validate_pull_request(repo, branch):
    repo = repo or get_repo()
    branch = branch or get_branch()
    validate_pulls(repo, branch)


def get_branch():
    command = 'git rev-parse --abbrev-ref HEAD'
    return get_git_data(command)


def get_repo():
    command = 'git remote get-url origin'
    repo_url = get_git_data(command)
    if repo_url:
        return re.split(r'\.|\/', repo_url)[-2]


def get_git_data(command):
    try:
        return handle_process(command)
    except Exception:
        logger.error('Failed to resolve command: {}'.format(command))
