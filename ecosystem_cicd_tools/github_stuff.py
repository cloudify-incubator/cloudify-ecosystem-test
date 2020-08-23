
import logging
from os import environ
from re import sub, split, IGNORECASE

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
    except (GithubException, AssertionError):
        logging.info('Commit {commit_id} not found.'.format(
            commit_id=commit_id))


def create_release(name, version, message, commit, repo=None):
    logging.info('Attempting to create new release {name}.'.format(name=name))
    repo = repo or get_repository()
    if isinstance(commit, Commit.Commit):
        commit = commit.commit
    try:
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
    for release in releases:
        if "latest" in release.title:
            continue
        if version_family and not release.title.startswith(version_family):
            continue
        return release


def get_pull_request(name, repo=None):
    """Get a PR by name"""
    logging.info('Attempting to get PR {name}'.format(name=name))
    repo = repo or get_repository()
    return repo.get_pull(name)


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


def get_documentation_branches(message):
    """
    Get a list of branches containing this plugin change documentation.
    :param message:
    :return:
    """
    logging.info('Getting documentation branches from {message}'.format(
        message=message))
    # Split the commit message into stuff before and after the key.
    # I.E. 'this is my commit message \n __DOCS__: CY-1234, CY-4321'
    if '__NODOCS__' in message:
        logging.info('__NODOCS__ in commit message'
                     '...skipping requirement.')
        return ['__NODOCS__']
    message = split(
        '__DOCS__:',
        sub('\s|\t', '', message),
        flags=IGNORECASE)
    # Delete the irrelevant stuff before the key.
    # I.E. 'this is my commit message \n '
    if len(message) != 2:
        logging.error('Use the __DOCS__ key only once per commit.')
        logging.debug('If your merge squashes commits,'
                      'you need to handle it before hand.')
        # TODO: Figure out what to do about squashed commits.
        return []
    return [b for b in message[-1].split(',') if b.startswith('CY-')]


def _merge_documentation_pulls(docs_repo, docs_branches):

    if '__NODOCS__' in docs_branches:
        return
    elif not docs_branches:
        raise Exception('There are no docs branches in the commit, '
                        'and __NODOCS__ is not specified in the commit.')

    # For each pull, merge it.
    pulls = docs_repo.get_pulls(state='open')
    for docs_branch in docs_branches:
        for pull in pulls:
            if pull.head.ref == docs_branch:
                logging.info('Merging {pull}'.format(pull=pull.number))
                pull.merge(merge_method='squash')


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

    # Get the parent commits.
    branch = repo.get_branch(branch)
    # Get the closed PRs that have heads for those commits.
    right_msg = split('Merge\spull\srequest\s#',
                      branch.commit.commit.message)[-1]
    pr_number = split('\s', right_msg)[0].replace('#', '')

    pull_request = repo.get_pull(int(pr_number))
    # Get the commits in that PR.
    # Check those commit messages for Docs Branches.
    # For each commit, read its message, and collect the documentation
    # branches.
    docs_branches = []
    for commit in pull_request.get_commits():
        docs_branches = docs_branches + get_documentation_branches(
            commit.commit.message)
    logging.info('Will merge these docs branches: {docs_branches}'.format(
        docs_branches=docs_branches))

    _merge_documentation_pulls(docs_repo, docs_branches)

