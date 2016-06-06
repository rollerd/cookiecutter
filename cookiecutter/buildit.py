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

    venv_name = False
    if build_step_data.get('virtualenv', None):
        venv_name = build_virtualenv(build_step_data['virtualenv'])
        build_step_data.pop('virtualenv')

    for step in build_step_data:
        step_name = 'build_' + step
        if step_name in globals():
            globals()[step_name](build_step_data[step], repo_dir=repo_dir, venv_name=venv_name)
        else:
            build_arbitrary(build_step_data[step], repo_dir=repo_dir, venv_name=venv_name)


def build_virtualenv(venv_data):
    try:
        venv_name = venv_data['name']
    except KeyError as err:
        msg = "Missing 'name' param for virtualenv in build.yml config"
        raise MissingBuildFileParamException(msg, err)

    print("\033[93mCreating virtualenv...\033[0m")
    sys.stdout.flush()
    subprocess.call("""source {0} && mkvirtualenv -q """.format(VENV_WRAPPER_PATH) + pipes.quote(venv_name), executable='bash', shell=True)
    print("\033[92mFinished\033[0m")
    return venv_name


def build_requirements(data, repo_dir=None, venv_name=None):
    if not venv_name:
        err = "Missing venv name"
        msg = "Cannot install requirements without specifying a virtualenv in the build.yml config"
        raise MissingBuildFileParamException(msg, err)

    try:
        req_file_path = data['file']
    except KeyError as err:
        msg = "Missing 'file' param under requirements in build.yml"
        raise MissingBuildFileParamException(msg, err)

    with work_in(repo_dir):
        print("\033[93mInstalling project requirements...\033[0m", end='')
        sys.stdout.flush()
        s = subprocess.Popen(['{0}/{1}/bin/pip'.format(VENV_DIR, venv_name), '-q', 'install', '-r', './{0}'.format(req_file_path)])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_collectstatic(data, repo_dir=None, venv_name=None):
    if not data:
        return

    if not venv_name:
        err = "Missing venv name"
        msg = "Cannot call collectstatic without specifying a virtualenv in the build.yml config"
        raise MissingBuildFileParamException(msg, err)

    with work_in(repo_dir):
        print("\033[93mRunning collectstatic...\033[0m", end='')
        sys.stdout.flush()
        s = subprocess.Popen(['{0}/{1}/bin/python'.format(VENV_DIR, venv_name), 'manage.py', 'collectstatic', '--noinput', '-v', '0'])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_npm(data, repo_dir=None, venv_name=None):
    if not data:
        return

    print("\033[93mRunning npm install...\033[0m")

    with work_in(repo_dir):
        s = subprocess.Popen(['npm', '--loglevel=silent', 'install'])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_bower(data, repo_dir=None, venv_name=None):
    if not data:
        return

    print("\033[93mRunning bower install...\033[0m")

    with work_in(repo_dir):
        s = subprocess.Popen(['./node_modules/bower/bin/bower', 'install'])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_gulp(data, repo_dir=None, venv_name=None):
    if not data:
        return

    print("\033[93mRunning gulp build...\033[0m")

    with work_in(repo_dir):
        s = subprocess.Popen(['./node_modules/gulp/bin/gulp.js', 'build'])
        s.communicate()
        print("\033[92mFinished\033[0m")


def build_apache_config(data, repo_dir=None, venv_name=None):
    try:
        hosted_location = data.pop('hosted_location')
    except KeyError as err:
        msg = "hosted_location must be specified under apache_config in the build.yml file"
        raise MissingBuildFileParamException(msg, err)

    if not venv_name:
        err = "Missing venv name"
        msg = "Cannot call apache_config builder without specifying a virtualenv in the build.yml config"
        raise MissingBuildFileParamException(msg, err)

    data_to_list = ['--{0},{1}'.format(k,v).split(',') for k,v in data.items()]
    remaining_params = [item for sublist in data_to_list for item in sublist]

    print("\033[93mCreating apache conf...\033[0m", end='')
    sys.stdout.flush()

    s = subprocess.Popen(['python', '/home/vagrant/django-deployment-script-jenkins/create_httpd_conf.py',
                          hosted_location, '--path_to_venv', '{0}/{1}'.format(VENV_DIR, venv_name)]  + remaining_params)
    s.communicate()
    print("\033[92mFinished\033[0m")


def build_arbitrary(data, repo_dir=None, venv_name=None):
    print("\033[93mRunning arbitrary command...\033[0m")
    sys.stdout.flush()

    with work_in(repo_dir):
        s = subprocess.Popen(data)
        s.communicate()

    print("\033[92mFinished\033[0m")
