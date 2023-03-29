from ecosystem_cicd_tools.validations import validate_pulls
from ecosystem_tests.dorkl.commands import handle_process
from ...ecosystem_tests_cli import ecosystem_tests
from ..logger import logger


@ecosystem_tests.command(name='validate-pulls',
                         short_help='validate pulls.')
@ecosystem_tests.options.repo
@ecosystem_tests.options.branch
def validate_pull_request(repo, branch):
    if not branch:
        command = 'git rev-parse --abbrev-ref HEAD'
        try:
            branch = handle_process(command)
        except:
            logger.error('Failed to resolve branch: {}'.format(branch))
    validate_pulls(repo, branch)
