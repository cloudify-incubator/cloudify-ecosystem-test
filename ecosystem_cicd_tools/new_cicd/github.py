from os import environ
from functools import wraps
from pkg_resources import parse_version

import re
import http
import github
import urllib3
import requests

from .logging import logger


def with_github_client(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):

        kwargs['github_client'] = get_client(kwargs)
        if 'repository' not in kwargs or not kwargs['repository']:
            kwargs['repository_name'] = get_repository_name(kwargs)
            kwargs['organization_name'] = get_organization_name(kwargs)
            repository = get_repository_object(kwargs)
        else:
            repository = kwargs['repository']
            kwargs['repository_name'] = repository.name
            kwargs['organization_name'] = repository.organization.name
        kwargs['repository'] = repository
        kwargs['commit'] = get_commit(kwargs)
        return func(*args, **kwargs)
    return wrapper_func


def get_client(kwargs):
    logger.info('Setting up Github client.')
    if 'github_token' in kwargs:
        github_token = kwargs['github_token']
    elif 'RELEASE_BUILD_TOKEN' in environ:
        github_token = environ['RELEASE_BUILD_TOKEN']
    elif 'GITHUB_TOKEN' in environ:
        github_token = environ['GITHUB_TOKEN']
    else:
        raise RuntimeError(
            'No token provided. '
            f'We have these kwargs {kwargs} '
            f'and environ: {environ}')
    return github.Github(github_token.strip())


def get_repository_name(kwargs):
    logger.info('Getting repository name.')
    repo = kwargs.get(
        'repository_name') or environ.get('CIRCLE_PROJECT_REPONAME')
    if not repo:
        raise RuntimeError(
            'No repository provided. '
            'Add environment variable CIRCLE_PROJECT_REPONAME.')
    return repo


def get_organization_name(kwargs):
    logger.info('Getting organization name.')
    org = kwargs.get(
        'organization_name') or environ.get('CIRCLE_PROJECT_USERNAME')
    if not org:
        raise RuntimeError(
            'No organization provided. '
            'Add environment variable CIRCLE_PROJECT_USERNAME.')
    return org


def get_repository_object(kwargs):
    logger.info('Getting repository object.')
    repository = kwargs['github_client'].get_repo(
        '{org}/{repo}'.format(org=kwargs['organization_name'],
                              repo=kwargs['repository_name']))
    logger.info('The repo object: {}'.format(repository))
    return repository


def get_commit(kwargs):
    logger.info('Getting commit object.')
    commit_id = kwargs.get('commit_id') or environ.get('CIRCLE_SHA1')
    if isinstance(commit_id, github.Commit.Commit):
        commit_id = commit_id.commit
    try:
        return kwargs['repository'].get_commit(commit_id)
    except (github.UnknownObjectException,
            github.GithubException,
            AssertionError):
        logger.error(
            'Commit {commit_id} not found.'.format(commit_id=commit_id))
        return


def get_latest_release(repository):
    return get_release('latest', repository)


def get_most_recent_release(repository=None, **_):
    logger.info('Attempting to get most recent release from repo {repo}.'
                .format(repo=repository.name))
    releases = sorted(
        [str(r.title) for r in repository.get_releases() if r.title and
         check_version_valid(r.title)],
        key=parse_version,
    )
    if releases:
        return releases.pop()


def check_version_valid(text):
    logger.info('Looking for version in {text}.'.format(text=text))
    version = re.findall('(^\\d+.\\d+.\\d+$)', text)
    if text == 'latest' or len(version) == 1:
        return True
    return False


def upload_asset(release, asset_path, asset_label):
    logger.info('Uploading {} {} to {}.'.format(
        asset_path, asset_label, release
    ))
    for asset in release.get_assets():
        if asset.label == asset_label:
            asset.delete_asset()
            upload_asset(release, asset_path, asset_label)
    try:
        release.upload_asset(asset_path, asset_label)
    except (http.client.RemoteDisconnected, urllib3.exceptions.ProtocolError, requests.exceptions.ConnectionError):
        upload_asset(release, asset_path, asset_label)
    except github.GithubException as e:
        if e.status != 422:
            logger.error('Failed to upload new asset: '
                         '{path}:{label} to release {name}.'.format(
                path=asset_path, label=asset_label, name=release))
            raise


@with_github_client
def create_release(name,
                   version,
                   message,
                   commit=None,
                   repository=None,
                   *_,
                   **__):
    if isinstance(commit, github.Commit.Commit):
        commit = commit.commit
    logger.info('Create release params {}, {}, {}, {}'.format(
        version, name, message, commit))
    try:
        return repository.create_git_release(
            tag=version, name=name, message=message, target_commitish=commit)
    except (github.GithubException, AssertionError):
        return repository.create_git_release(
            tag=version, name=name, message=message)


def plugin_release(plugin_name,
                   version=None,
                   plugin_release_name=None,
                   *_,
                   **__):

    plugin_release_name = plugin_release_name or "{0}-v{1}".format(
        plugin_name, version)
    version_release = get_release(version)
    if not version_release:
        version_release = create_release(
            version, version, plugin_release_name, commit)
    return version_release

def prepare_files_for_pr(cloned_repo, github_token, commit_message):
    # the cloned repo is create using the Repo.clone_from(....) 
    # you should use from git import Repo to import it
    cloned_repo.git.add("*")
    cloned_repo.git.commit("-m", commit_message)
    origin = cloned_repo.remote(name="origin")
    origin_url = origin.url
    new_url = origin_url.replace("https://", f"https://{github_token}@")
    origin.set_url(new_url)
    origin.push()


def create_branch(git_repo, branch_name):
    source_branch = git_repo.default_branch
    sb = git_repo.get_branch(source_branch)
    git_repo.create_git_ref(
        ref='refs/heads/' + branch_name, sha=sb.commit.sha)
    return source_branch


@with_github_client
def get_list_of_commits_from_branch(name_branch, repository=None, **_):
    pulls = repository.get_pulls(state='open')
    for pull in pulls:
        if pull.head.ref == name_branch:
            return list(pull.get_commits())
    return []


@with_github_client
def delete_release(release_name, repository=None, **_):
    for resp in repository.get_releases():
        if resp.title == release_name:
            obj = repository.get_release(resp.id)
            obj.delete_release()
            try:
                ref = repository.get_git_ref(f"tags/{resp.tag_name}")
                ref.delete()
            except github.GithubException.UnknownObjectException:
                pass


@with_github_client
def get_release(release_name, repository=None, **_):
    try:
        return repository.get_release(release_name)
    except github.GithubException.UnknownObjectException:
        pass
