
import logging
from os import environ
from re import sub, split, IGNORECASE

from github import Github, Commit, PullRequest
from github.GithubException import UnknownObjectException, GithubException


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


def permit_merge(pull, repo=None):
    """
    Merge a pull request if it is approved and mergeable.
    (Mergeable means that github can do it automatically without our help.)
    :param pull:
    :param repo:
    :return:
    """
    if not isinstance(pull, PullRequest.PullRequest):
        pull = get_pull_request(pull, repo)
    logging.info('Attempting to merge PR {name}'.format(name=pull.id))

    approved = any([r.state
                    for r in pull.get_reviews() if r.state is 'APPROVED'])

    if pull.mergeable and approved:
        return
    else:
        raise Exception(
            'Unable to merge PR {name}, because {state}/{approved}.'.format(
                name=pull.id,
                state=pull.mergeable_state,
                approved=approved))


def get_documentation_branches(message):
    """
    Get a list of branches containing this plugin change documentation.
    :param message:
    :return:
    """
    # Split the commit message into stuff before and after the key.
    # I.E. 'this is my commit message \n DOCUMENTATION: CY-1234, CY-4321'
    if 'NO DOCUMENTATION' in message:
        logging.info('NO DOCUMENTATION in commit message'
                     '...skipping requirement.')
        return []
    message = split(
        'DOCUMENTATION:',
        sub('\s|\t', '', message),
        flags=IGNORECASE)
    # Delete the irrelevant stuff before the key.
    # I.E. 'this is my commit message \n '
    if len(message) != 2:
        raise Exception(
            'The commit message must say \'DOCUMENTATION:\' '
            'Message says: {message}'.format(message=message))
    return [b for b in message[-1].split(',') if b.startswith('CY-')]


def merge_documentation_pulls(commit_message, repo=None):
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
                pull.merge()
