#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
cookiecutter.find
-----------------

Functions for finding Cookiecutter templates and other components.
"""

import logging
import os

from .exceptions import NonTemplatedInputDirException, MissingBuildFileException


def find_template(repo_dir):
    """
    Determines which child directory of `repo_dir` is the project template.

    :param repo_dir: Local directory of newly cloned repo.
    :returns project_template: Relative path to project template.
    """

    logging.debug('Searching {0} for the project template.'.format(repo_dir))

    repo_dir_contents = os.listdir(repo_dir)

    project_template = None
    for item in repo_dir_contents:
        if 'cookiecutter' in item and '{{' in item and '}}' in item:
            project_template = item
            break

    if project_template:
        project_template = os.path.join(repo_dir, project_template)
        logging.debug(
            'The project template appears to be {0}'.format(project_template)
        )
        return project_template
    else:
        raise NonTemplatedInputDirException


def find_build_file(repo_dir):
    """
    Determines if the build.yml file exists in the project directory

    :param repo_dir: Local directory of project
    :return:
    """
    logging.debug('Searching {0} for build.yml file.'.format(repo_dir))

    repo_dir_contents = os.listdir(repo_dir)

    build_file = None
    for item in repo_dir_contents:
        if 'build.yml' in item:
            build_file = item
            break

    if build_file:
        build_file = os.path.join(repo_dir, build_file)
        logging.debug('The build file appears to be {0}'.format(build_file))
        return build_file
    else:
        raise MissingBuildFileException