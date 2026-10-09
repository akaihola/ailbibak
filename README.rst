=================================================
                    ailbibak
=================================================
a version history preserving remote backup script
-------------------------------------------------

This script was inspired by the rsnapshot project.

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
    Backs up the source directory to a new snapshot on the backup
    host. With ``-m`` it stores a message with the snapshot.

ailbibak-status
    Lists the files which have changed since the latest snapshot.

ailbibak-diff
    Shows those changes in the diff format.

ailbibak-push.cmd
    The Windows version of ailbibak-push.

ailbibak
    The first version. It copies the source, which may be on another
    host, to a new snapshot in the current directory.

Usage
-----

Run ailbibak-push in the directory you want to back up. The first
time, it offers to create ``.ailbibak/ailbibak.conf`` and
``.ailbibak/excludes.txt``. The created excludes file includes only
the ``.ailbibak`` directory, so edit both files before you run
ailbibak-push again.

Each snapshot is a directory named by its date and time, such as
``backup/2026-10-09_18-05-56``. Files which haven't changed are hard
links to the previous snapshot, and ``backup/current`` points to the
latest snapshot.

ailbibak never removes old snapshots. It also expects bash as the
login shell on the backup host.

.. _rsnapshot: https://rsnapshot.org/
.. _restic: https://restic.net/
.. _BorgBackup: https://www.borgbackup.org/
.. _Kopia: https://kopia.io/
.. _btrbk: https://digint.ch/btrbk/
