import codecs
from poyo import parse_string, PoyoException
from .find import find_build_file
from .utils import work_in
from .exceptions import MissingBuildFileParamException

import os
import pipes
import subprocess
import sys

VENV_WRAPPER_PATH = os.environ['VIRTUALENVWRAPPER_SCRIPT']
VENV_DIR = os.environ['VIRTUALENVWRAPPER_HOOK_DIR']

def build_project(repo_dir):
    build_file_path = find_build_file(repo_dir)

    with work_in(repo_dir):
        build_file = os.path.split(build_file_path)[1]

        with open(build_file) as f:
            ymldata = f.read()

        data = parse_string(ymldata)

    venv = False
    if data.get('virtualenv', None):
        venv = build_virtualenv(data['virtualenv'])

    if data.get('requirements', None):
        build_requirements(repo_dir, data['requirements'], venv)

    if data.get('collectstatic', None):
        build_collectstatic(repo_dir, venv)

    if data.get('npm', None):
        build_npm(repo_dir)

    if data.get('bower', None):
        build_bower(repo_dir)

    if data.get('gulp', None):
        build_gulp(repo_dir)

    if data.get('apache_config', None):
        build_apache_config(data['apache_config'], venv)


def build_virtualenv(data):
    venv_name = data.get('name', None)
    if not venv_name:
        raise MissingBuildFileParamException('Missing "name" param for virtualenv in build.yml config')
    print("\033[93mCreating virtualenv...\033[0m")
    sys.stdout.flush()
    subprocess.call("""source {0} && mkvirtualenv -q """.format(VENV_WRAPPER_PATH) + pipes.quote(venv_name), executable='bash', shell=True)
    print("\033[92mFinished\033[0m")
    return venv_name


def build_requirements(repo_dir, data, venv):
    if not venv:
        raise MissingBuildFileParamException('Cannot install requirements without specifying a virtualenv in the build.yml config')

    req_file_path = data['file']
    venv_name = venv

    with work_in(repo_dir):
        print("\033[93mInstalling project requirements...\033[0m", end='')
        sys.stdout.flush()
        s = subprocess.Popen(['{0}/{1}/bin/pip'.format(VENV_DIR, venv_name), '-q', 'install', '-r', './{0}'.format(req_file_path)])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_collectstatic(repo_dir, venv):
    if not venv:
        raise MissingBuildFileParamException("Cannot call collectstatic without specifying a virtualenv in the build.yml config")

    venv_name = venv

    with work_in(repo_dir):
        print("\033[93mRunning collectstatic...\033[0m", end='')
        sys.stdout.flush()
        s = subprocess.Popen(['{0}/{1}/bin/python'.format(VENV_DIR, venv_name), 'manage.py', 'collectstatic', '--noinput', '-v', '0'])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_npm(repo_dir):
    print("\033[93mRunning npm install...\033[0m")

    with work_in(repo_dir):
        s = subprocess.Popen(['npm', '--loglevel=silent', 'install'])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_bower(repo_dir):
    print("\033[93mRunning bower install...\033[0m")

    with work_in(repo_dir):
        s = subprocess.Popen(['./node_modules/bower/bin/bower', 'install'])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_gulp(repo_dir):
    print("\033[93mRunning gulp build...\033[0m")

    with work_in(repo_dir):
        s = subprocess.Popen(['./node_modules/gulp/bin/gulp.js', 'build'])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_apache_config(data, venv_name):
    if not data.get('server_path', None):
        raise MissingBuildFileParamException("server_path must be specified under apache_config in the build.yml file")

    server_path = data.get('server_path')

    print("\033[93mCreating apache conf...\033[0m", end='')
    sys.stdout.flush()
    s = subprocess.Popen(['python', '/home/vagrant/django-deployment-script-jenkins/create_httpd_conf.py',
                          server_path, '--path_to_venv', '{0}/{1}'.format(VENV_DIR, venv_name)])
    s.communicate()
    print("\033[92mFinished\033[0m")