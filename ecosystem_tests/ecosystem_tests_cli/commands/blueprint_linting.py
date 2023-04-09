########
# Copyright (c) 2014-2022 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import tempfile
import subprocess
from git import Repo
from github import Github
from ..logger import logger
from datetime import datetime
from ...ecosystem_tests_cli import ecosystem_tests
from ecosystem_cicd_tools.new_cicd.github import with_github_client


@ecosystem_tests.command(
        name='blueprint-linting',
        short_help='validate blueprints in a repo using cfy-lint autofix.')
@ecosystem_tests.options.github_token
@ecosystem_tests.options.repo_name
@ecosystem_tests.options.directory
@ecosystem_tests.options.pull_request_title
def blueprint_linting(github_token=None,
                      repo_name=None,
                      directory=None,
                      pull_request_title=None):

    branch_name = time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")

    github_token = github_token or os.environ("GITHUB_TOKEN")
    org_name = os.environ("CIRCLE_PROJECT_USERNAME")
    repo_name = repo_name or (org_name + "/" + os.environ("CIRCLE_PROJECT_REPONAME"))
    directory = directory or tempfile.mkdtmp(prefix=time)
    pull_request_title = pull_request_title or "cfy-lint autofix " + time

    # Define the name of the files of interest
    file_type = ".yaml"

    command = "cfy-lint -b {} --format JSON"

    # get github objects
    g = Github(github_token)
    # user = g.get_user()
    git_repo = g.get_repo(repo_name)

    # clone repo to dest_folder
    repo = Repo.clone_from(git_repo.clone_url, os.path.join(
        os.getcwd(), directory))

    # check if there are issues in the blueprints
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(file_type):
                    # If the file matches the desired name,
                    # execute the command on it
                    full_path = os.path.join(root, file)
                    full_command = command.format(full_path)
                    p = subprocess.Popen(full_command.split(),
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                    stdout, stderr = p.communicate()
                    for line in stderr.decode('utf-8').split('\r\n'):
                        if line:
                            raise StopIteration
    except StopIteration:
        command = "cfy-lint -b {} -af"
        # create branch
        source_branch = git_repo.default_branch
        sb = git_repo.get_branch(source_branch)
        git_repo.create_git_ref(
            ref='refs/heads/' + branch_name, sha=sb.commit.sha)
        repo.git.pull()
        repo.git.checkout(branch_name)

    if command == "cfy-lint -b {}":
        # return 0
        raise StopIteration

    # run auto fix
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(file_type):
                # If the file matches the desired name,
                # execute the command on it
                full_path = os.path.join(root, file)
                full_command = command.format(full_path)
                p = subprocess.Popen(full_command.split(),
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                for line in stderr.decode('utf-8').split('\r\n'):
                    logger.info(line)

    # check status
    status = repo.git.status()
    status_no_change = "On branch {}\nYour branch is up to date with " \
        "'origin/{}'.\n\nnothing to commit, working tree clean".format(
            branch_name, branch_name)
    if not status == status_no_change:
        # update files
        repo.git.add("*")
        repo.git.commit("-m", "test test test")
        origin = repo.remote(name="origin")
        origin_url = origin.url
        new_url = origin_url.replace("https://", f"https://{github_token}@")
        origin.set_url(new_url)
        origin.push()

        # create PR
        title = pull_request_title
        body = "testing"
        pr = git_repo.create_pull(
            title=title, body=body, head=branch_name, base=source_branch)


