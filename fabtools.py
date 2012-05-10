# -*- coding: utf-8 -*-
# fabtools.py
#
# Copyright (c) 2012 Henning Glatter-Gotz
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# fabtools.py - Collection of tasks for fabric
#
# To include it in the fabfile.py add this near the top
#
# import sys
# sys.path[:0] = ["path_to_where_this_lives/fabtools"]
# import fabtools

import os
from fabric.api import *
from fabric.colors import red, green

try:
    import yaml
except ImportError:
    if confirm(red('pyYaml module not installed. Install it now?', bold=True)):
        install_py_yaml()
        exit(0)
    else:
        exit(1)


def load_yaml(path):
    """
    Load a yaml file located at 'path' and return the content as a dictionary.
    If the yaml file does not exist an empty dictionary will be returned.
    """
    if os.path.exists(path):
        f = open(path)
        data = yaml.load(f)
        f.close()
        return data
    else:
        return {}


def load_yaml_config(path, env = ''):
    """
    Load an environment aware yaml configuration file into a dictionary.
    If a configuration depends on the target of the deployment it is possible
    to pass the name of the environment to this function (env). In such a case
    the yaml configuration file must look like this:

    all:
        key1: defaultValue1
        :
    prod:
        key1: prod_value1
        key2: prod_value2
        :
    dev:
        key1: dev_value1
        key2: dev_value2
        :

    'all' is the default that will be returned if no env value is passed.
    'prod' and 'dev' in the above example are the names of the environments
    present in this file.
    Calling the function with 'prod' as the value for env will return the key/
    value pairs from the 'all' section with the values from the 'prod' section
    overriding any that might have been loaded from the all section.
    """
    config = load_yaml(path)

    if config:
        if 'all' in config:
            all = config['all']
        else:
            return {}
        if env != '':
            if env in config:
                all.update(config[env])
                return all
            else:
                return {}

    return config


def load_settings(path):
    """
    Take given file path and return dictionary of any key=value pairs found.
    Copy and paste from fabric project's main.py.
    """
    if os.path.exists(path):
        comments = lambda s: s and not s.startswith("#")
        settings = filter(comments, open(path, 'r'))
        return dict((k.strip(), v.strip()) for k, _, v in
            [s.partition('=') for s in settings])
    # Handle nonexistent or empty settings file
    return {}


def pear_detect(package):
    """
    Detect if a pear package is installed.
    """
    if which('pear'):
        pear_out = local('pear list -a', True)
        if pear_out.find(package) == -1:
            return False
        else:
            return True
    else:
        print(red('pear is not installed', True))
        return False


def which(program):
    """
    Return the path of an executable file.
    Borrowed from http://stackoverflow.com/a/377028/250780
    """
    import os
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)

    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def git_archive_all(path, archive_file_name):
    """
    Creates a gzipped tar file as git-archive would, but includes all the
    submodules if any exist.

     --path The path where the achrive is created
     --archive_file_name The file name of the archive

    Original source from https://github.com/ikame/fabric-git-archive-all
    """
    import os
    import tarfile

    def ls_files(prefix=''):
        """
        Does a `git ls-files` on every git repository (eg: submodules)
        found in the working git repository and returns a list with all the
        filenames returned by each `git ls-files`

         --full-name Forces paths to be output relative to the project top
           directory
         --exclude-standard adds standard git exclusions
           (.git/info/exclude, .gitignore, ...)
        """
        cmd = 'git ls-files --full-name --exclude-standard'
        raw_files = local(cmd, capture=True)
        files = []

        for filename in raw_files.split('\n'):
            if (os.path.isdir(filename) and
                os.path.exists(os.path.join(filename, '.git'))):
                os.chdir(filename)
                files.extend(ls_files(prefix=filename))
            else:
                files.append(os.path.join(prefix, filename))

        return files

    cwd = os.getcwd()
    os.chdir(path)
    files = ls_files()
    os.chdir(path)
    project_tar = tarfile.open(archive_file_name, 'w:gz')

    for filename in files:
        project_tar.add(filename)

    project_tar.close()
    os.chdir(cwd)

    print(green('Archive created at %s/%s' % (path, archive_file_name)))


def is_git_dirty():
    """
    Determine if the current working copy is dirty - have files been modified
    or are there untracked files.
    """
    dirty_status = local('git diff --quiet || echo "*"', capture=True)
    if dirty_status == '*':
        return True

    untracked_count = int(local('git status --porcelain 2>/dev/null| grep "^??" | wc -l', capture=True))
    if untracked_count > 0:
        return True

    return False


def get_git_commit():
    """
    Get the commit SHA1 (short) of the current branch.
    """
    return local('git rev-parse --short HEAD', capture=True)


def install_py_yaml():
    """
    Install the pyYaml module
    """
    local('curl -O http://pyyaml.org/download/pyyaml/PyYAML-3.10.tar.gz && tar -xzf PyYAML-3.10.tar.gz && cd PyYAML-3.10 && python setup.py install && cd .. && rm -rf PyYAML-3.10.tar.gz PyYAML-3.10')
