# -*- coding: utf-8 -*-
# fabtools.py
#
# Copyright (c) 2012 Henning Glatter-Gotz
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
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

# fabtools.py - Collection of helpers for fabric
#
# To include it in the fabfile.py add this near the top
#
# import sys
# sys.path[:0] = ["path_to_where_this_lives/fabtools"]
# import fabtools

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
    Load a yaml file and return the content
    """
    f = open(path)
    yml_content = yaml.load(f)
    f.close()

    return yml_content


def load_config(config_path):
    """
    Load the yaml configuration into the env variable
    """
    config = load_yaml(config_path)

    for k, v in config['env'].iteritems():
        env[k] = v


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


def git_archive_all(output):
    """
    Creates a gzipped tar file as git-archive would, but includes all the
    submodules if any exist. Run this task at root directory of your git
    repository.

    Source from https://github.com/ikame/fabric-git-archive-all
    """
    import os
    import tarfile

    def ls_files(prefix=''):
        """
        Does a `git ls-files` on every git repository (eg: submodules)
        found in the working git repository and returns a list with all the
        filenames returned by each `git ls-files`

         --full-name Forces paths to be output relative to the project top directory
         --exclude-standard adds standard git exclusions (.git/info/exclude, .gitignore, ...)
        """
        command = 'git ls-files --full-name --exclude-standard'
        raw_files = local(command, capture=True)
        files = []

        for filename in raw_files.split('\n'):
            if os.path.isdir(filename) and os.path.exists(os.path.join(filename, '.git')):
                os.chdir(filename)
                files.extend(ls_files(prefix=filename))
            else:
                files.append(os.path.join(prefix, filename))

        return files

    cwd = os.getcwd()
    files = ls_files()
    os.chdir(cwd)

    project_tar = tarfile.open(output, 'w:gz')

    for filename in files:
        project_tar.add(filename)

    project_tar.close()

    print(green('Archive created at %s' % output))


def install_py_yaml():
    """
    Install the pyYaml module
    """
    local('curl -O http://pyyaml.org/download/pyyaml/PyYAML-3.10.tar.gz && tar -xzf PyYAML-3.10.tar.gz && cd PyYAML-3.10 && python setup.py install && cd .. && rm -rf PyYAML-3.10.tar.gz PyYAML-3.10')
