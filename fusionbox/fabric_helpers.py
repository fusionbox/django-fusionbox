import tempfile
import shutil
from StringIO import StringIO

from contextlib import contextmanager as _contextmanager

from fabric.api import *
from fabric.contrib.console import *
from fabric.contrib.project import rsync_project


env.workon_home = '/var/python-environments'
@_contextmanager
def virtualenv(dir):
    with prefix('source %s/%s/bin/activate' % (env.workon_home, dir)):
        yield


def files_changed(version, files):
    """
    Between version and HEAD, has anything in files changed?
    """
    if not version:
        return True
    if not isinstance(files, basestring):
        files = ' '.join(files)
    return "diff" in local("git diff %s HEAD -- %s" % (version, files), capture=True)


def update_git(branch):
    """
    Updates the remote git repo to ``branch``. Returns the previous remote git
    version.
    """
    with settings(warn_only=True):
        remote_head = run("cat static/.git_version.txt")
        if remote_head.failed:
            remote_head = None
    try:
        loc = tempfile.mkdtemp()
        put(StringIO(local('git rev-parse %s' % branch, capture=True) + "\n"), 'static/.git_version.txt', mode=0775)
        local("cd `git rev-parse --show-toplevel` && git archive %s | tar xf - -C %s" % (branch, loc))
        local("chmod -R g+rwX %s" % (loc)) # force group permissions
        # env.cwd is documented as private, but I'm not sure how else to do this
        with settings(warn_only=True):
            loc = loc + '/' # without this, the temp directory will get uploaded instead of just its contents
            rsync_project(env.cwd, loc, extra_opts='--chmod=g=rwX,a+rX -l')
    finally:
        shutil.rmtree(loc)
    return remote_head


env.tld = '.com'
def project_tests(tests):
    """
    Executes each Django test suite that is defined in the `tests` list.

    Django tests return status code ``1`` if they fail.  This will cause Fabric
    to halt execution.
    """
    if tests is None:
        return
    if isinstance(tests, basestring):
        apps_to_test = tests.split(';')
    else:
        apps_to_test = tests
    cmd = "python manage.py test %s"
    for app_label in apps_to_test:
        local(cmd % app_label)


def stage(pip=False, migrate=False, syncdb=False, tests=None, branch=None):
    """
    stage will update the remote git version to your local HEAD, collectstatic, migrate and
    update pip if necessary.

    A test argument of a semicolon delimited list of Django test suites to run,
    canceling staging if a test fails.

    Example: ``fab stage:tests=<test_suite1>;<test_suite2>;..``

    Set ``env.project_name`` and ``env.short_name`` appropriately to use.
    ``env.tld`` defaults to ``.com``
    """
    with cd('/var/www/%s%s' % (env.project_name, env.tld)):
        project_tests(tests)
        version = update_git(branch or 'HEAD')
        update_pip = pip or files_changed(version, "requirements.txt")
        migrate = migrate or files_changed(version, "*/migrations/* %s/settings.py requirements.txt" % env.project_name)
        syncdb = syncdb or files_changed(version, "*/settings.py")
        with virtualenv(env.short_name):
            if update_pip:
                run("pip install -r ./requirements.txt")
            if syncdb:
                run("python manage.py syncdb")
            if migrate:
                run("python manage.py backupdb")
                run("python manage.py migrate")
            run("python manage.py collectstatic --noinput")
        run("sudo touch /etc/vassals/%s.ini" % env.short_name)


def deploy():
    """
    Like stage, but always migrates, pips, tests, and uses the live branch.
    """
    stage(True, True, True, getattr(env, 'tests', None), "live")
