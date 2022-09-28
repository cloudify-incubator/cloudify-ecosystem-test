from ecosystem_cicd_tools.validations import validate_pulls
from ...ecosystem_tests_cli import ecosystem_tests


@ecosystem_tests.command(name='validate-pulls',
                         short_help='validate pulls.')
@ecosystem_tests.options.repo
@ecosystem_tests.options.branch
def validate_pull_request(repo, branch):
    validate_pulls(repo, branch=branch)
