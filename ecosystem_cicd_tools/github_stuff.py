
import logging
from os import environ
from re import sub, split, findall, IGNORECASE

from github import Github, Commit
from github.GithubException import UnknownObjectException, GithubException

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def get_client(github_token=None):
    github_token = github_token or environ['RELEASE_BUILD_TOKEN']
    return Github(github_token)


def get_repository(client=None, org=None, repo_name=None):
    client = client or get_client()
    org = org or environ.get('CIRCLE_PROJECT_USERNAME')
    repo_name = repo_name or environ.get('CIRCLE_PROJECT_REPONAME')
    logging.info('Attempting to get repo {name} from org {org}.'.format(
        name=repo_name, org=org))
    return client.get_repo('{org}/{repo}'.format(org=org, repo=repo_name))


def get_commit(commit_id=None, repo=None):
    commit_id = commit_id or environ['CIRCLE_SHA1']
    logging.info('Attempting to get commit {name}.'.format(name=commit_id))
    repo = repo or get_repository()
    if isinstance(commit_id, Commit.Commit):
        commit_id = commit_id.commit
    try:
        return repo.get_commit(commit_id)
    except (UnknownObjectException, GithubException, AssertionError):
        logging.info('Commit {commit_id} not found.'.format(
            commit_id=commit_id))


def create_release(name, version, message, commit, repo=None):
    logging.info('Attempting to create new release {name}.'.format(name=name))
    repo = repo or get_repository()
    logging.info('Got repo {repo}'.format(repo=repo))
    if isinstance(commit, Commit.Commit):
        commit = commit.commit
    try:
        logging.info('Create release params '
                     '{tag}, {name}, {message}, {commit}'.format(
            tag=version,
            name=name,
            message=message,
            commit=commit))
        return repo.create_git_release(
            tag=version, name=name, message=message,
            target_commitish=commit)
    except (GithubException, AssertionError):
        return repo.create_git_release(tag=version, name=name, message=message)


def get_release(name, repo=None):
    repo = repo or get_repository()
    logging.info('Attempting to get release {name} from repo {repo}.'.format(
        name=name, repo=repo.name))
    try:
        return repo.get_release(name)
    except UnknownObjectException:
        logging.info(
            'Failed to get release {name} from repo {repo}.'.format(
                name=name, repo=repo.name))
        return


def get_assets(release_name):
    logging.info('Attempting to get assets from release {name}'.format(
        name=release_name))
    release = get_release(release_name)
    return release.get_assets()


def upload_asset(release_name, asset_path, asset_label):
    logging.info('Attempting upload new asset '
                 '{path}:{label} to release {name}.'.format(
                     path=asset_path,
                     label=asset_label,
                     name=release_name))
    release = get_release(release_name)
    try:
        release.upload_asset(asset_path, asset_label)
    except GithubException as e:
        if e.status != 422:
            logging.info('Failed to upload new asset: '
                         '{path}:{label} to release {name}.'.format(
                             path=asset_path,
                             label=asset_label,
                             name=release_name))
            raise
        for asset in get_assets(release.title):
            if asset.label == asset_label:
                asset.delete_asset()
                release.upload_asset(asset_path, asset_label)


def update_release(name, message, commit, prerelease=False, repo=None):
    repo = repo or get_repository()
    logging.info(
        'Attempting to update release {name} '
        'for repo {repo} {message}.'.format(
            name=name, repo=repo.name, message=message))
    release = repo.get_release(name)
    if isinstance(commit, Commit.Commit):
        commit = commit.commit
    try:
        return release.update_release(
            name, message, draft=False, prerelease=prerelease,
            target_commitish=commit)
    except (GithubException, AssertionError):
        return release.update_release(
            name, message, draft=False, prerelease=prerelease)


def delete_latest_tag_if_exists():
    repo = get_repository()
    logging.info(
        'Attempting  to delete Tag with name "latest" in '
        'repository {repo}.'.format(
            repo=repo.name))
    try:
        latest_tag_ref = repo.get_git_ref('tags/latest')
    except UnknownObjectException:
        logging.info(
            'Tag with name "latest" doesnt exists.'.format(repo=repo.name))
        return
    latest_tag_ref.delete()


def get_most_recent_release(version_family=None, repo=None):
    repo = repo or get_repository()
    logging.info('Attempting to get most recent '
                 'release for version family {version} '
                 'from repo {repo}.'.format(
                     version=version_family,
                     repo=repo.name))
    releases = repo.get_releases()
    largest_version = get_largest_version(
        [v.title for v in releases if v.title[0].isdigit()])
    for release in releases:
        if release.title == largest_version:
            return release


def get_largest_version(versions):
    largest = '0-0'
    for version in versions:
        manager_version, blueprint_version = version.split('-')
        if manager_version >= largest.split('-')[0] and \
                int(blueprint_version) >= int(largest.split('-')[-1]):
            largest = version
    return largest


def get_pull_requests(numbers, repo=None):
    """Get a PR by number"""
    logging.info('Attempting to get PRs {number}'.format(number=numbers))
    repo = repo or get_repository()
    prs = []
    numbers = numbers or []
    for number in numbers:
        prs.append(repo.get_pull(number))
    return prs


def raise_if_unmergeable(pull):
    """
    Raise a pull request if it is not approved and mergeable.
    (Mergeable means that github can do it automatically without our help.)
    :param pull:
    :return:
    """

    logging.info('Checking if can merge PR {name}.'.format(name=pull.number))
    approved = any([r.state
                    for r in pull.get_reviews()
                    if r.state.upper() == 'APPROVED'])
    if pull.mergeable and approved:
        logging.info('PR {number} is mergeable.'.format(number=pull.number))
        return
    else:
        raise Exception(
            'Unable to merge PR {name},'
            'because state={state}/approved={approved}.'.format(
                name=pull.number,
                state=pull.mergeable_state,
                approved=approved))


def get_pull_request_branch_names(pull_numbers=None, pulls=None, repo=None):
    """
    Find the HEAD branch name of a pull request.
    :param pull_number:
    :param pull:
    :param repo:
    :return:
    """
    prs = []
    pulls = pulls or []
    for pull in pulls:
        prs.append(pull.head.label)
    for pull in get_pull_requests(pull_numbers, repo):
        prs.append(pull.head.label)
    return prs


def get_pull_request_jira_ids(pull_numbers=None, pulls=None, repo=None):
    """
    Return JIRA IDs in the PR HEAD Branch Name.
    :param pull_number: The number of the PR.
    :param pull:
    :param repo:
    :return:
    """
    logging.info('Pull numbers {} pulls {}'.format(pull_numbers, pulls))
    branch_names = get_pull_request_branch_names(pull_numbers, pulls, repo)
    # Find find strings in the form CYBL-1234 or CY-12345.
    ids = []
    for matches in [findall(r'(?:CY|CYBL|RD)\-\d*',
                            branch_name) for branch_name in branch_names]:
        ids.extend(matches)
    return ids


def get_branch_prs(branch_name, repo=None):
    """
    Get the PR number from the current merge commit.
    :param branch_name: The current branch (master).
    :param repo:
    :return:
    """

    repo = repo or get_repository()
    logging.info('Attempting to get PR to branch {branch} {name}'.format(
        branch=branch_name, name=repo.name))
    branch = repo.get_branch(branch_name)
    logging.info('Looking for PR number in {msg}'.format(
        msg=branch.commit.commit.message))
    number_sign_nums = findall(r'\#\d+', branch.commit.commit.message)
    if len(number_sign_nums) < 1:
        raise Exception(
            'The branch name {branch} contains less than one \#. '
            'In order to identify the PR, '
            'we look for \# in the commit message. '.format(
                branch=branch_name))
    return [int(pr.replace('#', '')) for pr in number_sign_nums]


def validate_docs_requirement(message):
    """
    Check if we should have docs or not.
    :param message:
    :return:
    """

    logging.info('Checking if docs are required for this PR.')
    if '__NODOCS__' in message:
        logging.info('__NODOCS__ in commit message. Not checking for docs PRs')
        return False
    logging.info('__NODOCS__ not in commit message. Checking for docs PRs')
    return True


def _merge_documentation_pulls(docs_repo, jira_ids):
    """

    :param docs_repo: The PyGithub Repo Object,
        probably for docs.getcloudify.org.
    :param jira_ids: A list of Jira IDs, like [u'CY-1234', u'CYBL-12345'].
    :return:
    """

    pulls = docs_repo.get_pulls(state='open')
    merges = 0
    for jira_id in jira_ids:
        for pull in pulls:
            if jira_id in pull.head.label:
                logging.info('Merging {pull}'.format(pull=pull.number))
                pull.merge(merge_method='squash')
                merges += 1
    if not merges:
        raise Exception(
            'No documentation PRs were found in {}. '
            'If your PR includes the label "enhancement", '
            'then you are expected to submit docs PRs. '.format(
                docs_repo.name))


def merge_documentation_pulls(repo=None, docs_repo=None, branch='master'):
    """
    Merge any pulls in the docs repo with documentation for this change.
    :param repo: The current repo (a plugin for example).
    :param docs_repo: The repo to check for Docs PRs.
    :param branch: The current branch.
    :return:
    """

    repo = repo or get_repository()
    docs_repo = docs_repo or get_repository(
        org='cloudify-cosmo', repo_name='docs.getcloudify.org')
    pr_numbers = get_branch_prs(branch, repo)
    if not pr_numbers:
        return
    if not check_if_label_in_pr_labels(pr_numbers):
        return
    jira_ids = get_pull_request_jira_ids(pr_numbers)
    _merge_documentation_pulls(docs_repo, jira_ids)


def find_pull_request_numbers(branch, repo):
    """
    Finds PR number associated with a branch.
    If the branch is master then then pr returned is the pr associated with the
    latest merge commit which contains the PR number.
    """
    if branch in ['master', 'main']:
        pull_request_numbers = get_branch_prs(branch, repo)
    else:
        pr_url = environ.get('CIRCLE_PULL_REQUEST', '/0')
        pr = pr_url.split('/')[-1]
        pull_request_numbers = [int(pr)]

    if 0 in pull_request_numbers:
        pull_request_numbers.remove(0)

    return pull_request_numbers


def get_files_changed_in_pr(pr_numbers, repo):
    prs = get_pull_requests(pr_numbers, repo)
    files = []
    for pr in prs:
        files.extend([pr_file.filename for pr_file in pr.get_files()])
    return files


def find_changed_files_in_branch_pr_or_master(repo=None, branch_name=None):
    """
    Finds the changed files in the current branch pr.
    If the branch is master then it finds the files that changed
    in the last pr merged to master.
    """
    repo = repo or get_repository()
    branch = branch_name or environ['CIRCLE_BRANCH']
    pr_numbers = find_pull_request_numbers(branch, repo)
    if not pr_numbers and branch != 'master':
        logging.info('No PR found, list of changed files is empty.')
        return []
    return get_files_changed_in_pr(pr_numbers, repo)


def get_pr_labels(pr_numbers, repo):
    pr_labels = []
    for pr in get_pull_requests(pr_numbers, repo):
        pr_labels.extend(pr.get_labels())
    return pr_labels


def check_if_label_in_pr_labels(pr_numbers, repo=None, label_name=None):
    label_name = label_name or 'enhancement'
    repo = repo or get_repository()
    labels = get_pr_labels(pr_numbers, repo)
    if len(labels) == 0:
        raise Exception(
            'The PR {} in repo {} does not provide any labels. '
            'Please add labels to your PR. '
            'For example, if the PR is for a feature, '
            'then use the label "enhancement". If the PR is for a bug, '
            'then use the label "bug".'.format(pr_numbers, repo.name))
    for label in labels:
        if label_name.lower() in label.name.lower():
            return label
    logging.info('Warning: The label {} was not found in labels {}'.format(
        label_name, labels))
