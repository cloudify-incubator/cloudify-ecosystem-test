import os
from functools import wraps

import github

from . import s3
from .logging import logger


def with_github_client(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):

        kwargs['github_client'] = get_client(kwargs)
        kwargs['repository_name'] = get_repository_name(kwargs)
        kwargs['organization_name'] = get_organization_name(kwargs)
        repository = get_repository_object(kwargs)
        kwargs['repository'] = repository
        kwargs['commit'] = get_commit(kwargs)
        func(*args, **kwargs)
    return wrapper_func


def get_client(kwargs):
    logger.info('Setting up Github client.')
    github_token = kwargs.get(
        'github_token') or os.environ.get('RELEASE_BUILD_TOKEN')
    if not github_token:
        raise RuntimeError(
            'No repository provided. '
            'Add environment variable RELEASE_BUILD_TOKEN.')

    return github.Github(github_token)


def get_repository_name(kwargs):
    logger.info('Getting repository name.')
    repo = kwargs.get(
        'repository_name') or os.environ.get('CIRCLE_PROJECT_REPONAME')
    if not repo:
        raise RuntimeError(
            'No repository provided. '
            'Add environment variable CIRCLE_PROJECT_REPONAME.')
    return repo


def get_organization_name(kwargs):
    logger.info('Getting organization name.')
    org = kwargs.get(
        'organization_name') or os.environ.get('CIRCLE_PROJECT_USERNAME')
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
    return repository


def get_commit(kwargs):
    logger.info('Getting commit object.')
    commit_id = kwargs.get('commit_id') or os.environ.get('CIRCLE_SHA1')
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


def get_release(name, repository):
    logger.info('Attempting to get release {name} from repo {repo}.'.format(
        name=name, repo=repository.name))
    try:
        return repository.get_release(name)
    except github.UnknownObjectException:
        logger.error(
            'Failed to get release {name} from repo {repo}.'.format(
                name=name, repo=repository.name))
        return


def get_latest_release(repository):
    return get_release('latest', repository)


def get_most_recent_release(repository):
    logger.info('Attempting to get most recent release from repo {repo}.'
                .format(repo=repository.name))
    releases = sorted(
        repository.get_releases(), key=lambda v: v.title, reverse=True)
    return releases.pop()


def upload_asset(release, asset_path, asset_label):
    logger.info('Uploading {} {} to {}.'.format(
        asset_path, asset_label, release
    ))
    try:
        release.upload_asset(asset_path, asset_label)
    except github.GithubException as e:
        if e.status != 422:
            logger.error('Failed to upload new asset: '
                         '{path}:{label} to release {name}.'.format(
                path=asset_path, label=asset_label, name=release))
            raise
    for asset in release.get_assets():
        if asset.label == asset_label:
            asset.delete_asset()
            release.upload_asset(asset_path, asset_label)


@with_github_client
def upload_assets_to_release(assets, release_name, repository, **_):
    """ Upload a bunch of assets to release.
    Example assets:
    {
        'plugin.yaml': 'cloudify-aws-plugin/plugin.yaml',
        'v2_plugin.yaml': 'cloudify-aws-plugin/v2_plugin.yaml',
        'cloudify_aws_plugin-3.0.4-centos-Core-py36-none-linux_aarch64.wgn': 'cloudify-aws-plugin/cloudify_aws_plugin-3.0.4-centos-Core-py36-none-linux_aarch64.wgn',
    }
    Example release name: latest, or '3.0.5'

    :param assets:
    :param release_name:
    :param repository:
    :param _:
    :return:
    """  # noqa
    release = get_release(release_name, repository)
    if not release:
        raise RuntimeError(
            'The release {release} does not exist.'.format(release=release))
    for label, path, in assets.items():
        upload_asset(release, path, label)
        s3.upload_plugin_asset_to_s3(path, repository.name, release_name)
