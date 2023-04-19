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
import tempfile
import subprocess
from git import Repo
from github import Github
from ..logger import logger
from datetime import datetime
from ...ecosystem_tests_cli import ecosystem_tests
from ecosystem_cicd_tools.new_cicd.github import (with_github_client, 
                                                  prepare_files_for_pr, 
                                                  create_branch)

FILE_TYPE = ".yaml"
AF_CMD = "cfy-lint -b {} -af"
DATE_FORMAT = "%Y-%m-%d_%H-%M-%S-%f"
LINT_CMD = "cfy-lint -b {} --format JSON"
BLUEPRINT_START = "tosca_definitions_version:"


@ecosystem_tests.command(
        name='blueprint-linting',
        short_help='validate blueprints in a repo using cfy-lint autofix.')
@ecosystem_tests.options.github_token
@ecosystem_tests.options.repo
@ecosystem_tests.options.org
@ecosystem_tests.options.pull_request_title
def blueprint_linting(github_token=None,
                      repo=None,
                      org=None,
                      pull_request_title=None):

    _blueprint_linting(github_token=github_token,
                       repository_name=repo,
                       organization_name=org,
                       pull_request_title=pull_request_title)


@with_github_client
def _blueprint_linting(repository,
                       github_token,
                       repository_name,
                       organization_name,
                       pull_request_title,
                       *_,
                       **__):
    # prep variables
    github_token = github_token or os.environ("GITHUB_TOKEN")
    branch_name = time = datetime.now().strftime(DATE_FORMAT)
    directory = tempfile.mkdtemp(prefix=time)
    pull_request_title = pull_request_title or "cfy-lint autofix " + time
    commit_message = "blueprint fixed using cfy-lint autofix"
    # clone repo to dest_folder
    cloned_repo = Repo.clone_from(repository.clone_url, os.path.join(
        os.getcwd(), directory))

    # check if there are issues in the blueprints
    files_to_fix = run_command_on_dir(directory, LINT_CMD)
    if not files_to_fix:
        # return 0
        raise StopIteration

    source_branch = create_branch(repository, branch_name)
    cloned_repo.git.pull()
    cloned_repo.git.checkout(branch_name)
    run_command_on_dir(directory, AF_CMD)

    # check status
    status = cloned_repo.git.status()
    status_no_change = "On branch {}\nYour branch is up to date with " \
        "'origin/{}'.\n\nnothing to commit, working tree clean".format(
            branch_name, branch_name)
    if not status == status_no_change:
        prepare_files_for_pr(cloned_repo, github_token, commit_message)
        create_pr(repository, pull_request_title, branch_name, source_branch)


def run_command_on_dir(directory, command):
    i = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(FILE_TYPE):
                # If the file matches the desired name,
                # execute the command on it
                full_path = os.path.join(root, file)
                with open(full_path, "r") as f:
                    first_line = f.readline().strip()
                    if BLUEPRINT_START in first_line:
                        full_command = command.format(full_path)
                        p = subprocess.Popen(full_command.split(),
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
                        stdout, stderr = p.communicate()
                        for line in stderr:
                            i += 1
    return i


def create_pr(git_repo, title, branch_name, source_branch):
    body = "this was create using ecosystem-test blueprint linting"
    pr = git_repo.create_pull(
        title=title, body=body, head=branch_name, base=source_branch)
