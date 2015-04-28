#!/usr/bin/env python

import os
import sys
import subprocess


class Error(Exception):
    pass


class PyGitBump(object):
    PGB = '[PyGit-Bump] {}'
    PATH_ERR = '\n' + PGB.format('Provided path is not valid [path:\'{}\']\n')
    CMD_ERR = '\n' + PGB.format('Error while executing command [{}]\n')

    def set_working_dir(self):
        """
        Determine git project path and set working directory to this project.
        """
        # hooks are located in .git/hooks, so working directory is two level up
        project_path = os.path.abspath(
            os.path.join(os.path.dirname(sys.argv[0]), '..', '..')
        )
        os.chdir(project_path)
        # because python was initiated in .git/hooks dir, it knows nothing
        # about our project. Trying import any project's module will raise
        # ImportError. To avoid that, we must add project to python paths
        sys.path.append(project_path)
        # project path is saved for further processing
        self.pwd = project_path

    def shell_cmd(self, command):
        """
        Run shell command and return results, or raise error if fail.
        """
        try:
            return subprocess.check_output(command, shell=True)
        except subprocess.CalledProcessError:
            raise Error(self.CMD_ERR.format(command))

    def get_config_value(self, var):
        """
        Read from config and parse it.
        """
        command = 'git config --list | grep "pgb.{}="'
        result = self.shell_cmd(command.format(var))
        index = len('pgb.'+var+'=')
        return str(result[index:]).strip('\n')

    def check_branch(self):
        branches = self.get_config_value('branch').split(',')
        # get current branch
        curr_branch = self.shell_cmd('git symbolic-ref --short HEAD')
        # check if branch is one of fallowed one, also by checking
        # only main part of the branch name. For example 'release'
        # will be matched with 'release/1.0.0' etc.
        if any([curr_branch.startswith(b) for b in branches]):
            return True
        return False

    def validate_path(self):
        """
        First this function tries to import current version. Secondly absolute
        path to file is recognized. At last the position of version variable
        in file is saved for future processing.
        """
        # last dot specifies version variable name, that is why the path
        # is splitted into [path.to.file, variable_name]
        raw_path = self.get_config_value('path')
        path = raw_path.rsplit('.', 1)

        try:
            self.var_name = path[1]
            version = __import__(path[0], fromlist=[self.var_name])
            self.curr_ver = getattr(version, self.var_name)
            # convert python way of module locations into unix style
            ver_file = path[0].replace('.', '/') + '.py'
            self.file_path = os.path.join(self.pwd, ver_file)
            # find the line of a file where the variable is placed
            with open(self.file_path, 'r') as f:
                for index, line in enumerate(f.readlines(), 1):
                    if line.startswith(self.var_name):
                        self.index = index
                        break
        except (ImportError, IndexError, IOError, AttributeError):
            raise Error(self.PATH_ERR.format(raw_path))

    def bump(self, version):
        """
        Write new version number to file.
        """
        sed_cmd = 'sed -i "{0}s/{1}.*/{1} = \'{2}\'/" {3}'.format(
            self.index, self.var_name, version, self.file_path
        )
        self.shell_cmd(sed_cmd)
        txt = 'Version changed from {} to {}'.format(self.curr_ver, version)
        print self.PGB.format(txt) + '\n'

    def ask_txt(self):
        txt_start = 'Version of project: {}; '.format(self.curr_ver)
        txt_end = 'Would you like to change it? [y/N]: '
        return self.PGB.format(txt_start + txt_end)

    def ask_ver_txt(self):
        return self.PGB.format('Please provide new version number: ')


if __name__ == "__main__":
    # check if this is python 2. If not, do nothing!
    if sys.version_info[:1] == (2,):
        # When git hooks are invoked, stdin is pointed to /dev/null.
        # The work-around is to re-assign stdin back to /dev/tty.
        sys.stdin = open('/dev/tty', 'r')

        try:
            pgb = PyGitBump()
            pgb.set_working_dir()
            # check if current branch is targeted branch, if not do nothing
            if pgb.check_branch():
                pgb.validate_path()
                print '\n', # for better formating
                while True:
                    choice = raw_input(pgb.ask_txt())
                    if choice in ('y', 'Y'):
                        new_ver = raw_input(pgb.ask_ver_txt())
                        pgb.bump(new_ver)
                        break
                    elif choice in ('n', 'N', ''):
                        break
        except Error, e:
            print e