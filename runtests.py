import subprocess
import unittest
import shutil
import os
import sys

from pygitbump import PyGitBump, Error


# Set working dir
wdir = os.getcwd() + '/.TmpGitDir'
# Branches names
master = 'TestMaster'
devel = 'TestDevel'


def prepare_git_repo():
    """
    Prepare git repository for tests.
    """
    # delete old dir if exist to avoid
    # errors during initialization.
    try:
        shutil.rmtree(wdir)
    except:
        pass
    finally:
        # create git project folder for tests
        # and set workdir to it.
        os.mkdir(wdir)
        os.chdir(wdir)
    # create git configuration
    subprocess.check_call('git init', shell=True)
    subprocess.check_call('git config pgb.branch %s' % master, shell=True)
    subprocess.check_call('git config pgb.path version.__version__', shell=True)
    # create base branch
    subprocess.check_call('git checkout -b %s' % master, shell=True)
    # create version file and write base version
    with open('version.py', 'w') as f:
        f.write('__version__ = 0.0.1')
    # commit version file
    subprocess.check_call('git add version.py', shell=True)
    subprocess.check_call('git commit -m "initial commit"', shell=True)
    # create another branch to allow merging
    subprocess.check_call('git checkout -b %s' % devel, shell=True)
    print('Finished preparing test git repository')
    print('-' * 70)
    print('You may see not only dots below ;) Nothing to worry about!')
    print('-' * 70)


def clear():
    """
    Remove git repository after tests.
    """
    shutil.rmtree(wdir)
    print("\nRemoving Git repository... Done")


class PyGitBumpTestCase(unittest.TestCase):
    def setUp(self):
        self.pgb = PyGitBump()

    def test_ask_ver_txt(self):
        msg = '[PyGit-Bump] Please provide new version number: '
        self.assertEqual(self.pgb.ask_ver_txt(), msg)

    def test_ask_txt(self):
        self.pgb.curr_ver = '0.0.1'
        msg = '[PyGit-Bump] Version of project: 0.0.1; Would you like to change it? [y/N]: '
        self.assertEqual(self.pgb.ask_txt(), msg)

    def test_bump(self):
        self.pgb.index = 1
        self.pgb.var_name = '__version__'
        self.pgb.curr_ver = '0.0.1'
        self.pgb.file_path = wdir + '/version.py'
        self.pgb.bump('0.0.2')
        with open(self.pgb.file_path, 'r') as f:
            self.assertEqual(f.readline(), "__version__ = '0.0.2'")

    def test_error_messages(self):
        self.assertEqual(self.pgb.PGB.format('Test'), '[PyGit-Bump] Test')
        msg1 = '\n[PyGit-Bump] Provided path is not valid [path:\'Test\']\n'
        self.assertEqual(self.pgb.PATH_ERR.format('Test'), msg1)
        msg2 = '\n[PyGit-Bump] Error while executing command [Test]\n'
        self.assertEqual(self.pgb.CMD_ERR.format('Test'), msg2)

    def test_shell_cmd(self):
        self.assertEqual(self.pgb.shell_cmd('echo Test'), 'Test\n')
        with self.assertRaises(Error) as PGBE:
            self.pgb.shell_cmd('Test')
        text = '\n[PyGit-Bump] Error while executing command [Test]\n'
        self.assertEqual(PGBE.exception.message, text)

    def test_check_branch(self):
        self.assertFalse(self.pgb.check_branch())
        subprocess.check_call('git checkout %s' % master, shell=True)
        self.assertTrue(self.pgb.check_branch())
        subprocess.check_call('git checkout %s' % devel, shell=True)

    def test_get_config_value(self):
        self.assertEqual(self.pgb.get_config_value('branch'), 'TestMaster')
        self.assertEqual(self.pgb.get_config_value('path'), 'version.__version__')

    def test_set_working_dir(self):
        os.chdir('./.git/hooks')
        self.pgb.set_working_dir()
        self.assertEqual(self.pgb.pwd, wdir)
        self.assertIn(wdir, sys.path)

    def test_validate_path(self):
        self.pgb.pwd = wdir
        self.pgb.validate_path()
        self.assertEqual(self.pgb.var_name, '__version__')
        self.assertIn(self.pgb.curr_ver, ('0.0.1', '0.0.2'))
        self.assertEqual(self.pgb.file_path, wdir + '/version.py')
        self.assertEqual(self.pgb.index, 1)


if __name__ == '__main__':
    prepare_git_repo()
    PyGitBumpTestSuite = unittest.TestLoader().loadTestsFromTestCase(PyGitBumpTestCase)
    unittest.TextTestRunner().run(PyGitBumpTestSuite)
    clear()