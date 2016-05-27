from .find import find_build_file
from .utils import work_in
from .exceptions import MissingBuildFileParamException

from collections import OrderedDict
import os
import pipes
import subprocess
import sys
import yaml

VENV_WRAPPER_PATH = os.environ['VIRTUALENVWRAPPER_SCRIPT']
VENV_DIR = os.environ['VIRTUALENVWRAPPER_HOOK_DIR']

def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)

def build_project(repo_dir):
    build_file_path = find_build_file(repo_dir)

    with work_in(repo_dir):
        build_file = os.path.split(build_file_path)[1]

        with open(build_file, 'r') as f:
            ymldata = f.read()

    build_step_data = ordered_load(ymldata, yaml.SafeLoader)

    venv = False
    if build_step_data.get('virtualenv', None):
        venv = build_virtualenv(build_step_data['virtualenv'])
        build_step_data.pop('virtualenv')

    for step in build_step_data:
        step_name = 'build_' + step
        if step_name in globals():
            globals()[step_name](build_step_data[step], repo_dir=repo_dir, venv=venv)
        else:
            build_arbitrary(build_step_data[step], repo_dir=repo_dir, venv=venv)


def build_virtualenv(data):
    venv_name = data.get('name', None)
    if not venv_name:
        raise MissingBuildFileParamException('Missing "name" param for virtualenv in build.yml config')
    print("\033[93mCreating virtualenv...\033[0m")
    sys.stdout.flush()
    subprocess.call("""source {0} && mkvirtualenv -q """.format(VENV_WRAPPER_PATH) + pipes.quote(venv_name), executable='bash', shell=True)
    print("\033[92mFinished\033[0m")
    return venv_name


def build_requirements(data, **kwargs):
    if not kwargs['venv']:
        raise MissingBuildFileParamException('Cannot install requirements without specifying a virtualenv in the build.yml config')

    req_file_path = data['file']
    venv_name = kwargs['venv']

    with work_in(kwargs['repo_dir']):
        print("\033[93mInstalling project requirements...\033[0m", end='')
        sys.stdout.flush()
        s = subprocess.Popen(['{0}/{1}/bin/pip'.format(VENV_DIR, venv_name), '-q', 'install', '-r', './{0}'.format(req_file_path)])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_collectstatic(data, **kwargs):
    if not data:
        return

    if not kwargs['venv']:
        raise MissingBuildFileParamException("Cannot call collectstatic without specifying a virtualenv in the build.yml config")

    venv_name = kwargs['venv']

    with work_in(kwargs['repo_dir']):
        print("\033[93mRunning collectstatic...\033[0m", end='')
        sys.stdout.flush()
        s = subprocess.Popen(['{0}/{1}/bin/python'.format(VENV_DIR, venv_name), 'manage.py', 'collectstatic', '--noinput', '-v', '0'])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_npm(data, **kwargs):
    if not data:
        return

    print("\033[93mRunning npm install...\033[0m")

    with work_in(kwargs['repo_dir']):
        s = subprocess.Popen(['npm', '--loglevel=silent', 'install'])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_bower(data, **kwargs):
    if not data:
        return
    print("\033[93mRunning bower install...\033[0m")

    with work_in(kwargs['repo_dir']):
        s = subprocess.Popen(['./node_modules/bower/bin/bower', 'install'])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_gulp(data, **kwargs):
    if not data:
        return

    print("\033[93mRunning gulp build...\033[0m")

    with work_in(kwargs['repo_dir']):
        s = subprocess.Popen(['./node_modules/gulp/bin/gulp.js', 'build'])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_apache_config(data, **kwargs):
    if not data.get('server_path', None):
        raise MissingBuildFileParamException("server_path must be specified under apache_config in the build.yml file")

    server_path = data.get('server_path')

    print("\033[93mCreating apache conf...\033[0m", end='')
    sys.stdout.flush()

    s = subprocess.Popen(['python', '/home/vagrant/django-deployment-script-jenkins/create_httpd_conf.py',
                          server_path, '--path_to_venv', '{0}/{1}'.format(VENV_DIR, kwargs['venv'])])
    s.communicate()
    print("\033[92mFinished\033[0m")


def build_arbitrary(data, **kwargs):
    print("\033[93mRunning arbitrary command...\033[0m")
    sys.stdout.flush()

    with work_in(kwargs['repo_dir']):
        s = subprocess.Popen(data)
        s.communicate()

    print("\033[92mFinished\033[0m")
