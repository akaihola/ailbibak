=================================================
                    ailbibak
=================================================
a version history preserving remote backup script
-------------------------------------------------

This script was inspired by the rsnapshot project.

ailbibak is a suite of backup scripts for maintaining versioned
backups using the rsync utility. It works like a simple version
control system for a folder. Each backup is a new revision on a
remote server, and you can store a message with it. Before backing
up, you can list the changed files and see the differences in the
diff format.

Every backup revision is a complete copy of the folder. Files which
haven't changed since the previous revision are hard links to it, so
they take disk space only once.

Status
------

Update 2026-10-09: ailbibak has not been developed since 2008, and
the web site mentioned in the scripts no longer exists. The Unix
scripts still work with rsync 3.5.0 and bash 5.3. Nobody has tested
the Windows script since 2008.

For new backups, use a maintained tool instead:

- rsnapshot_ keeps hard-linked rsync snapshots like ailbibak, and it
  also removes old ones.
- restic_, BorgBackup_ and Kopia_ deduplicate, compress and encrypt
  backups.
- btrbk_ snapshots Btrfs subvolumes and sends them to another host.

Scripts
-------

ailbibak-push
    Backs up a folder to a new backup revision on a remote server.

ailbibak-status
    Lists the files which have changed since the latest backup.

ailbibak-diff
    Compares current directories and files to the latest backup and
    outputs the differences in the diff format.

ailbibak-push.cmd
    The Windows version of ailbibak-push.

ailbibak
    The first version. It copies the source, which may be on another
    host, to a new backup revision in the current folder.

Usage
-----

Run ailbibak-push in the folder you want to back up::

    $ cd /home/meikalainen/documents
    $ ailbibak-push

The first time, it offers to create ``.ailbibak/ailbibak.conf`` and
``.ailbibak/excludes.txt``. Set the rsync destination in
``ailbibak.conf``, eg.::

    DESTINATION=meikalainen@host.mydomain.com:backup/documents

The created excludes file includes only the ``.ailbibak`` folder. To
back up everything except ``*~`` and ``*.bak`` files, remove its last
line, ``- *``.

Then run ailbibak-push again. With ``-m`` you can store a message
with the backup revision::

    $ ailbibak-push -m "Budget for 2009"

Later, list the files you have changed since the latest backup and
see the differences::

    $ ailbibak-status
    $ ailbibak-diff

Instead of running the scripts in the folder, you can give the
folder or its configuration file as an argument::

    $ ailbibak-push -m "Plan for 2009" /home/meikalainen/documents

On the remote server, each backup revision is a folder named by its
date and time, and ``current`` points to the latest one. The message
is in ``.ailbibak/message.txt`` of each revision::

    $ ssh meikalainen@host.mydomain.com ls backup/documents
    2008-11-26_10-49-24
    2008-11-27_09-15-02
    current

ailbibak never removes old backup revisions. It also expects bash as
the login shell on the remote server.

Tests
-----

The tests run each script with bash and zsh, and use both as the
login shell on the remote server. A fake ssh in ``tests/bin`` runs
the remote commands locally, so they need no SSH server. Run them
with uv_::

    $ uvx pytest

The scripts don't work with zsh yet, so the zsh tests fail. To run
only the bash tests::

    $ uvx pytest -k "not zsh"

.. _rsnapshot: https://rsnapshot.org/
.. _restic: https://restic.net/
.. _BorgBackup: https://www.borgbackup.org/
.. _Kopia: https://kopia.io/
.. _btrbk: https://digint.ch/btrbk/
.. _uv: https://docs.astral.sh/uv/
