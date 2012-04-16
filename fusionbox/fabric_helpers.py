from contextlib import contextmanager as _contextmanager

from fabric.api import *
from fabric.contrib.console import *


env.tld = '.com'
env.use_ssh_config = True


@_contextmanager
def virtualenv(dir):
    with prefix('source %s/bin/activate' % dir):
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


def is_repo_clean():
    """
    Checks if a remote repo has uncommitted changes.
    """
    with settings(warn_only=True):
        return run("git status 2>&1 | grep 'nothing to commit' > /dev/null").succeeded


def update_git(branch):
    """
    Checks out and updates ``branch`` on the remote git repo.  Returns the
    previous commit hash for ``branch`` on remote before update.
    """
    if not is_repo_clean():
        if not confirm("Remote repo is not clean.  Stash and continue?"):
            abort("Remote repo dirty.  Aborting.")
        run("git stash")
    run("git checkout %s" % branch)
    remote_head = run("git rev-list --no-merges --max-count=1 HEAD")
    run("git pull origin %s" % branch)
    return remote_head


def stage(pip=False, migrate=False, syncdb=False, branch=None):
    """
    stage will update the remote git version to your local HEAD, collectstatic, migrate and
    update pip if necessary.

    Set ``env.project_name`` and ``env.short_name`` appropriately to use.
    ``env.tld`` defaults to ``.com``
    """
    branch = branch or local('git branch | grep "^\*" | sed "s/^\* //"', capture=True)

    with cd('/var/www/%s%s' % (env.project_name, env.tld)):
        version = update_git(branch)
        update_pip = pip or files_changed(version, "requirements.txt")
        migrate = migrate or files_changed(version, "*/migrations/* %s/settings.py requirements.txt" % env.project_name)
        syncdb = syncdb or files_changed(version, "*/settings.py")
        with virtualenv('/var/python-environments/%s' % env.short_name):
            if update_pip:
                run("pip install -r ./requirements.txt")
            if syncdb:
                run("./manage.py syncdb")
            if migrate:
                run("./manage.py backupdb")
                run("./manage.py migrate")
            run("./manage.py collectstatic --noinput")
        run("sudo touch /etc/vassals/%s.ini" % env.short_name)


def deploy():
    """
    Like stage, but always migrates, pips, and uses the live branch
    """
    stage(True, True, True, "live")
