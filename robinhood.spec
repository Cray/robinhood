# default ON
%bcond_without lustre
%bcond_without lhsm
%bcond_without mysql
%bcond_without backup
# default OFF
%bcond_with shook
%bcond_with recovtools

# target install dir for web gui
%define installdir_www  /var/www/html

###### end of macro definitions #####

Name: robinhood
Version: 3.0

Vendor: CEA, HPC department <http://www-hpc.cea.fr>
Prefix: %{_prefix}

%if %{with lustre}
%if %{defined lversion}
%define config_dependant .lustre_client%{lversion}
%else
%define config_dependant .lustre_client
%endif
%endif

Release: 0.alpha1%{?config_dependant}%{?dist}


Summary: Robinhood - Policy engine and reporting tool for large filesystems
License: CeCILL-C
Group: Applications/System
Url: http://robinhood.sourceforge.net
Source0: robinhood-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: glib2-devel >= 2.16
BuildRequires: libattr-devel
BuildRequires: mailx
%if %{with lustre}
Requires: lustre-client >= %{lversion}
BuildRequires: lustre-client >= %{lversion}
%endif
%if %{with mysql}
BuildRequires: /usr/include/mysql/mysql.h
%endif
Obsoletes: robinhood-tmpfs < 3.0, robinhood-backup < 3.0, robinhood-lhsm < 3.0

%description
Robinhood is a tool for monitoring and purging file systems. It is designed to
process all its tasks in parallel, so it is particularly adapted for managing
large file systems with millions of entries and petabytes of data.

With support for: %{?with_lustre:Lustre} %{?with_backup:Backup} %{?with_shook:shook}

Generated using options: 


%package adm
Summary: admin/config helper for Robinhood PolicyEngine
Group: Applications/System
Release: 0.alpha1.noarch

%description adm
This RPM provides an admin/config helper for Robinhood PolicyEngine (command rbh-config).


%package webgui
Summary: Web interface to vizualize filesystems stats
Group: Applications/System
Release: 0.alpha1.noarch
Requires: php, php-mysql, php-xml, php-gd, php-pdo

%description webgui
Web interface to vizualize filesystems stats.
This uses robinhood database to display misc. user and group stats.


%if %{with recovtools}
%package recov-tools
Summary: Tools for MDS recovery.
Group: Applications/System

%description recov-tools
Tools for MDS recovery.
%endif

%package tests
Summary: Test suite for Robinhood
Group: Applications/System
Requires: robinhood robinhood-adm
Release: 0.alpha1.noarch

%description tests
Lustre and Posix tests for Robinhood.

%prep
%setup -q -n robinhood-%{version}

%build
./configure  %{?configure_flags:configure_flags} \
        --mandir=%{_mandir} \
        --libdir=%{_libdir}
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/robinhood.d/templates
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/robinhood.d/includes
mkdir -p $RPM_BUILD_ROOT/%{_initrddir}
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/ld.so.conf.d

%if %{with lhsm}
install -m 644 doc/templates/includes/lhsm.inc $RPM_BUILD_ROOT/%{_sysconfdir}/robinhood.d/includes/
%endif
install -m 644 doc/templates/includes/tmpfs.inc $RPM_BUILD_ROOT/%{_sysconfdir}/robinhood.d/includes/
install -m 644 doc/templates/includes/alerts.inc $RPM_BUILD_ROOT/%{_sysconfdir}/robinhood.d/includes/
install -m 644 doc/templates/example.conf $RPM_BUILD_ROOT/%{_sysconfdir}/robinhood.d/templates/
install -m 644 doc/templates/basic.conf $RPM_BUILD_ROOT/%{_sysconfdir}/robinhood.d/templates/

%if %{defined suse_version}
install -m 755 scripts/robinhood.init.sles $RPM_BUILD_ROOT/%{_initrddir}/robinhood
%else
install -m 755 scripts/robinhood.init $RPM_BUILD_ROOT/%{_initrddir}/robinhood
%endif

mkdir $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig
install -m 644 scripts/sysconfig_robinhood $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/robinhood

install -m 644 scripts/ld.so.robinhood.conf $RPM_BUILD_ROOT/%{_sysconfdir}/ld.so.conf.d/robinhood.conf

mkdir -p $RPM_BUILD_ROOT/%{installdir_www}/robinhood
cp -r web_gui/acct/* $RPM_BUILD_ROOT/%{installdir_www}/robinhood/.
cp    web_gui/acct/.htaccess $RPM_BUILD_ROOT/%{installdir_www}/robinhood/.

rm -f $RPM_BUILD_ROOT/%{_libdir}/robinhood/librbh_mod_*.a
rm -f $RPM_BUILD_ROOT/%{_libdir}/robinhood/librbh_mod_*.la

# Add an unmutable copy of the templates for the tests
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/robinhood/doc
cp -a doc/templates $RPM_BUILD_ROOT/%{_datadir}/robinhood/doc

%clean
rm -rf $RPM_BUILD_ROOT

%post
ldconfig
if [ -x %{_initrddir}/robinhood ]; then
  if %{_initrddir}/robinhood status | grep running | grep -v "not running"  >/dev/null 2>&1; then
    %{_initrddir}/robinhood stop
    WASRUNNING=1
  fi
  [ -x /sbin/chkconfig ] && /sbin/chkconfig --del robinhood
  [ -x /sbin/chkconfig ] && /sbin/chkconfig --add robinhood
  if test x$WASRUNNING = x1; then
    %{_initrddir}/robinhood start
  fi
fi

%preun
if [ "$1" = 0 ]; then
  if [ -x %{_initrddir}/robinhood ]; then
     [ -x /sbin/chkconfig ] && /sbin/chkconfig --del robinhood
    if %{_initrddir}/robinhood status | grep running | grep -v "not running" >/dev/null 2>&1; then
      %{_initrddir}/robinhood stop
    fi
  fi
fi

%postun
ldconfig

%files adm
%{_sbindir}/rbh-config

%if %{with recovtools}
%files recov-tools
%{_sbindir}/*lovea
%{_sbindir}/gen_lov_objid
%{_sbindir}/ost_fids_remap
%endif

%if %{with shook}
%files robinhood-annex
%{_sbindir}/rbh-rebind
%endif

%files webgui

# set apache permissions
%defattr(750,root,apache)
%{installdir_www}/robinhood

%files tests
%defattr(-,root,root,-)
%dir %{_datadir}/robinhood/
%{_datadir}/robinhood/tests/
%{_datadir}/robinhood/doc/

%files
%defattr(-,root,root,-)
#%doc README
#%doc COPYING
#%doc ChangeLog

# everythink in sbin, except rbh-config which is in adm
%if %{with shook}
%exclude %{_sbindir}/rbh-rebind
%{_sbindir}/rbh-import
%{_sbindir}/rbh-recov
%endif

%if %{with backup}
# NOT ADAPTED TO v3 YET
#%{_sbindir}/rbh-import
#%{_sbindir}/rbh-recov
#%{_sbindir}/rbh-rebind
%{_sbindir}/rbhext_*
%endif

%{_sbindir}/robinhood
%{_sbindir}/rbh-report
%{_sbindir}/rbh-diff
%{_sbindir}/rbh-undelete
%{_bindir}/rbh-du
%{_bindir}/rbh-find

%{_libdir}/robinhood/librbh_mod_*.so*

%{_mandir}/man1/*

%config(noreplace) %{_sysconfdir}/sysconfig/robinhood

%dir %{_sysconfdir}/robinhood.d
%dir %{_sysconfdir}/robinhood.d/includes
%dir %{_sysconfdir}/robinhood.d/templates

%dir %{_sysconfdir}/ld.so.conf.d
%{_sysconfdir}/ld.so.conf.d/robinhood.conf

%if %{with lhsm}
%config %{_sysconfdir}/robinhood.d/includes/lhsm.inc
%endif
%config %{_sysconfdir}/robinhood.d/includes/tmpfs.inc
%config %{_sysconfdir}/robinhood.d/includes/alerts.inc
%config %{_sysconfdir}/robinhood.d/templates/example.conf
%config %{_sysconfdir}/robinhood.d/templates/basic.conf

%{_initrddir}/robinhood

%changelog

* Mon Dec 08 2014 Thomas Leibovici <thomas.leibovici@cea.fr> 2.5.4
- [lustre] Lustre 2.4+: detect all stripe changes and update the DB accordingly.
- [scan] Prevent from dropping entries from DB when opendir or stat fail.
- [DB] Optimization to batch more DB requests.
- [DB] Allow using any MySQL engine (new config parameter: listmanager::mysql::engine).
- [rbh-config] Avoid backup_db to lock the whole tables with innodb.
- [bugfix] Improve robustness to corrupted mtimes.
- [bugfix] Fix possible crash in db_exec_sql.
- [bugfix] Fix possible overflow when executing a custom archive command.
- [backup mode] Clean all non-printable characters in backend path.
- [pkg] libattr-devel is now mandatory to build robinhood.

* Tue Jul 29 2014 Thomas Leibovici <thomas.leibovici@cea.fr> 2.5.3
- [bugfix] custom purge_command: fixed vulnerability to malicious file names.
- [bugfix] changelog processing: fixed errors 'Entry has incomplete path in DB' in some case of rm/create patterns.
- [bugfix] migration policy (fix): don't trigger copy of files that no longer exist.
- [feature] rbh-config: new option 'reset_acct' to rebuild accounting info.
- [feature] changelog reader: new parameter 'dump_file' to dump all incoming changelog records to a file.
- [compat] port to Lustre 2.6.0.

* Wed May 21 2014 Thomas Leibovici <thomas.leibovici@cea.fr> 2.5.2
- rbh-du: fixed major performance regression (since v2.5.0).
- rbh-find: fixed occasional crash.
- HSM and backup modes: fixed a risk of removing an existing entry from the backend (in some situations of hardlink/rename+unlink).
- backup mode: optimized sendfile()-based copy (Linux kernel >= 2.6.33).
- logs: avoid flood of log messages in case of DB connection error.
- alerts: added host name to alert mail title.
- rbh-config empty_db/repair_db: also manage/fix stored procedures.
- cosmetic: fix wrong display of purged blocks for count-based triggers.
- cosmetic: fix migration counter display.
- init script: check that 'ulimit -s' is reasonable.
- fixed build dependancies on Fedora19 and Fedora20.
- code sanity: fixed many 'coverity' warnings + a couple of minor memleaks.
- doc: details about RPM installation locations.
- doc: detail of 'backend' paramaters for backup mode.

* Wed Mar 19 2014 Thomas Leibovici <thomas.leibovici@cea.fr> 2.5.1
- entry processing (major fix): fixed deadlock when the pipeline is full
  and an entry with an unknown parent is encountered.
- purge (enhancement): start purging data from the most used OSTs.
- rbh-find (features): new options: -pool, -exec, -print, -nouser, -nogroup, -lsost
- rbh-find (optimization): automatically switch to bulk DB request mode when
  command argument is filesystem root (+new option -nobulk to disable it).
- logging (enhancement): new config parameters to control log header format
- backup (feature): allow compressing data in archive.
- backup (fix): wrong path in archive when robinhood root directory != mount point.
- backup (fix): fix segfault when importing a single file with a FID-ending name.

* Thu Feb 13 2014 Thomas Leibovici <thomas.leibovici@cea.fr> 2.5.0-1
Summary:
- filesystem disaster recovery features
- new namespace management (new DB schema to properly handle hardlinks, renames...)
- scanning and changelog processing optimizations
- database optimizations (requests batching)
- many other changes, improvements and code cleaning...

Details:
- rbh-diff:
    * new command to detect differences between the filesystem and the information
      in robinhood database.
    * option "--apply=fs" for disaster recovery purpose: restore the filesystem
      metadata from robinhood DB.
    * makes it possible to rebuild a Lustre MDT from scratch, or from a LVM snapshot
      (see "Robinhood Lustre disaster recovery guide" for more details).
- database:
    * new namespace implementation in database with new NAMES table (Cray contribution)
        - fixes/improves hardlink support
        - fixes/improves Lustre ChangeLog hardlink/rename/unlink support
        - saves DB storage space
    * database request batching: significantly increase database ingest rate.
      No longer needs innodb_flush_log_at_tx_commit != 1 to speed up DB operations.
    * additional information in DB that can help for disaster recovery:
      symlink info, access rights, stripe object indexes, stripe order, nlink...
    * set default commit behavior to transaction (prevent from DB inconsistencies)
    * optimized multi-table requests
    * optimization: minimized attribute set in DB update operations
      (don't update attributes that didn't change)
    * Fix: deal with mysql case insensitivity for string matching
    * triggers and stored procedures versioning mechanism
    * prevent from overflows for large INSERT requests, wide stripes...
    * prevent from DB deadlocks
- scanning:
    * --partial-scan option is deprecated and replaced by an optional argument to --scan (e.g. --scan=/fs/subdir).
    * better management of partial scans:
        - better detection of removed entries vs. entries moved from a directory to another.
        - partial scans can be used for initial DB population (even if the DB is initially empty).
    * dealing with dead/deactivated OSTs: don't remove entries from DB if stat() returns ESHUTDOWN.
    * garbage collection of removed entries in DB is a long operation when terminating a scan (and even more
      when terminating a partial scan). Added --no-gc option to skip it (recommanded for partial scans).
    * automatically enabling --no-gc if the DB is initially empty (eg. for initial scan).
    * optimization: use *at() functions (openat, fstatat) and readdir by chunk (using getdents) instead of POSIX lstat() and readdir_r().
    * optimization: use NOATIME flag to access entries as much as possible
    * optimizations of get_stripe and get_fid operations.
    * new --diff option for robinhood --scan and --readlog: output detected changes in a diff-like format.
- Lustre changelogs:
    * changelog batching (Cray contribution): to speed up changelog processing,
      robinhood retains changelog records in memory a short time,
      to aggregate similar/redundant Changelog records on the same entry before
      updating its database.
    * support multiple changelog readers (for DNE) as multiple threads (default)
      or as multiple processes, possibly on different hosts, by giving a MDT index
      to --readlog option.
    * resilience to filesystem umount/mount.
- rbh-report:
    * new option --entry-info to get all the stored information about an entry
    * option --dump-ost can now list multiple OSTs and support ranges notation (e.g. 3,5-8,12-23).
    * --dump-ost output indicates if a file has data on a given OST (could be striped on the OST but have no data on it).
- rbh-find:
    * new option -crtime to filter entries on creation time.
    * output ordering closer to find output
    * added missing info in 'rbh-find -ls' output (nlink, mode, symlink info...)
- robinhood-backup:
    * by default, use a built-in copy function to avoid the cost of forking copy commands.
    * rbh-backup-rebind: tool to rebind an entry in the backend if its fid changed in the filesystem
      for any reason (file copied to a new one to change its stripe, etc...)
    * rbh-backup-recov new features and options:
        --list (list information about entries to be recovered)
        --ost <ost_set> to only recover entries for a given set of OSTs (support range notation):
            the basic use-case is OST disaster recovery.
        --since <time> to only recover entries modified since a given date:
            the basic use case is after restoring an OST snapshot.
    * symlinks archiving to backend made optional (new parameter 'archive_symlinks')
      as they can now be restored using robinhood database information.
    * new parameter: sync_archive_data: force sync'ing data to disk to
      finalize the copy.
- configuration:
    * can specify environment variables in config file (e.g. fs_path = $ROOT_DIR ;)
    * prevent from using a wrong config file (Cray contribution):
        - only check files in /etc/robinhood.d/<purpose>, no longer in the current directory
        - fails if to many config files are available.
- documentation:
    * added man pages for robinhood daemon, rbh-report, rbh-find.

* Mon Jul 22 2013 Thomas Leibovici <thomas.leibovici@cea.fr> 2.4.3
- [lustre] support of Lustre 2.4
    - DNE not fully supported yet: if running multiple MDS,
      run 1 instance of changelog reader per MDT.
    - Detect file layout changes (new changelog record CL_LAYOUT).
- [lustre] added statistics about changelog processing speed.
- [policies] new parameter 'recheck_ignored_classes' to allow/avoid
    rematching entries from ignored classes in migration and purge policies.
- [web ui] security patch to prevent from SQL injection.
- [lustre] fix stack overflow when handling files with wide stripes.
- [DB] better handling of ER_QUERY_INTERRUPTED MySQL error.
- [DB] fixed DB connection leaks.
- Backup & HSM modes:
   - [doc] added config tutorial for backup mode
   - [fix] fix segfault in import command when uid/gid can't be resolved.
   - [rbh-report] fix bad display of total volume with -u or -g.
- Migration policy features and optimizations:
   - [feature] new parameter 'lru_sort_attr' to select LRU sort criteria for policy application.
        Previously based on last modification time, it can now be one of:
        creation, last_archive, last_mod, last_access.
   - [feature] special meaning for condition 'last_archive == 0':
        matches entries that have never been archived.
   - [feature] suspend migration if copy error rate exceed a threshold.
        This is controled by 'suspend_error_pct' and 'suspend_error_min' parameters.
   - [stats] migration stats while migration is running: added skipped and error counters.
   - [optim] avoid rechecking ignored entries at each pass
   - [optim] smoother feeding of migration workers queue
- Code & environment:
   - [build] can specify a path to alternative lustre source tree in ./configure
   - [tests] allow specifying an alternative path to lfs command

* Mon Mar 11 2013 Thomas Leibovici <thomas.leibovici@cea.fr> 2.4.2
- [general] immediate exit on ctrl+C: don't process all queued operations, just finish current.
- [general] LSB compliance if daemon is already started.
- [DB] validation with MariaDB (replacement for MySQL in Fedora19).
- [config] can set default config file using RBH_CFG_DEFAULT environment variable.
- [config] more precise message if no config file is found.
- [rbh-find] added -not/-! option to rbh-find.
- [lustre] fix for 16 chars pool names.
- [bugfix] fixed memleak in rbh-find.
- [bugfix] fixed segfault if checking scan deadline occured exactly when scan ended.
- [logs] display bandwidth and rate stats during migration run.
- [logs] fix: DB get operations were counted twice in stats.
- [cosmetic] removed "connection failed" warning for one shot commands.
- [cosmetic] fix typos in logs.
- [devel] port to automake 1.12 (since Fedora18).
- [shook] port to shook 1.3.5

* Mon Jan 28 2013 Thomas Leibovici <thomas.leibovici@cea.fr> 2.4.1
- [lustre] better file size change detection using CLOSE events
  from MDT ChangeLog (requires Lustre 2.2 or +)
- [scan] optimization: using fstatat and getdents
- [rbh-find] added -atime/-amin options
- [logs] add'l information in logs (DB operations, HSM_rm details)
- [logs] log to stderr if opening of the log file fails
- [fix] scan blocked if final DB operation failed
- [fix] avoid DB lock exhaustion for huge requests
- [backup] manage cross device rename in backend
- [backup] rebind an entry in backend after fid change (e.g. restripe)

* Wed Oct 31 2012 Thomas Leibovici <thomas.leibovici@cea.fr> 2.4.0
- [feature] rbh-du and rbh-find: "du" and "find" clones querying robinhood's database
- [report] new directory stats, top directories per dirent count, per avg file size
- [report] file size profiling: global, per user, per group, per fileclass...
- [report] sorting user/groups by size range (eg. percentage of files < 1G)
- [webUI] "size" section in webUI to display file size profiles
- [feature] Partial scans to update only a subset of the filesystem (also allows distributed scans)
- [packaging] rpm name 'robinhood-tmp_fs_mgr' changed to 'robinhood-tmpfs'
- [packaging] 'rbh-config' command moved to new RPM 'robinhood-adm'
- [report] refurbished rbh-report output format
- [policies] new criteria on file creation time
- [database] use innodb by default for MySQL engine
- [system] ability to detect "fake mtime" (mtime != actual modification time)
- [system] improved filesystem detection,
           using fsname or devid as FS identifier (config driven)
- [scan] can trigger external completion command when a scan ends
- [misc.] can use short config name instead of full path
          (eg. "-f <name>" instead of "-f /full/path/to/name.conf")
- [backup] directory and symlink recovery
- [lustre] port to Lustre 2.2 and 2.3
- [lustre] support for new Changelog record struct (lu-1331)
- [fix] max_rm_count=0 resulted in no rm (instead of unlimited)
- [fix] segfault in realpath() on Ubuntu
- [fix] unsigned arithmetic issue with MySQL 5.5

* Thu Jul 05 2012 Thomas Leibovici <thomas.leibovici@cea.fr> 2.3.4
- Faster and safer shutdown on SIGINT/SIGTERM
- Can use short config name instead of full config file path.
  E.g. "-f myconf" instead of "-f /etc/robinhood.d/tmp_fs/myconf.cfg"
- Consider all non-dirs for classinfo (instead of files only)
- Implemented max_rm_count in hsm remove policy
- clearer messages about DB connection and retries
- added lu543 configure option (must be enabled if this patch
  is integrated to your Lustre distribution)
- Better block counting for purges
- backup/shook modes:
    - import of existing files from backend
    - entry state set to 'archive_running' during migration
    - recovery for entries with 'release pending' or 'restore running' state on startup
      (new parameter: check_purge_status_on_startup)
    - enable DB rebuild if it is lost
    - fix: symlink recovery
    - improvements of rbhext_tool_clnt/svr (timeout, traces, ...)
    - user.shook_state xattr changed to security.shook_state
      (to avoid users to change it)
- Fix: Don't consider 'released' entries for quota-like purge triggers
- Fix: migrate-group did migrate user
- Generate up-to-date template automatically at RPM installation
- 72 new regression tests (all policies conditions and config file parameters are tested)

* Wed Feb 08 2012 Thomas Leibovici <thomas.leibovici@cea.fr> 2.3.3
- [webgui] added FS name to page title and page header
- [webgui] fix: added missing file in RPM (.htaccess)
- [reports] new options for top-users/top-groups: --by-avgsize, --count-min, --reverse
- [reports] Lustre changelog stats in 'rbh-report -a'
- [policies] fix: 'tree' condition must match root entry
- [policies] fix: migration class matching at scan time
- [config] simpler scan parameter 'scan_interval'
- [config] fix: don't reload config of disabled modules on SIGHUP
- [config] fix: on SIGHUP, don't reload parameters specified on cmd line
- [database] retry on connection failure
- [stats] dump process stats on SIGUSR1
- [backup] clean special chars in archive names
- [backup] fix issues in symlink archiving
- [lustre] specific compilation option for jira's LU-543
- [misc] code cleaning, sanity checks, improved traces...

* Wed Aug 03 2011 Thomas Leibovici <thomas.leibovici@cea.fr> 2.3.2
- [webgui] Web interface (beta)
- [quota/alerts] Implemented quota alerts on inode count (users and groups)
- [reporting] New option --by-count for --top-users, to sort users by entry count
- [database] Support of InnoDB MySQL engine
- [database] MySQL 4 compatibility fix
- [bugfix](minor) handling DB deadlock error
- [bugfix](tweak) added acct parameters to default and template outputs
- [alerts](tweak) additional info in the title of quota alert e-mails
- [testing] big tests with 1M entries
- [backup] about backup mode (beta):
    - [bugfix](major) fixed error determining symlink status
    - [bugfix](minor) don't consider 'new' entries in deferred removal
    - [trace] display warning if mtime in FS < mtime in backend

* Tue Jun 07 2011 Thomas Leibovici <thomas.leibovici@cea.fr> 2.3.1
- [bugfix](major) Wrong accounting values if file owner changes
- [bugfix](major) SQL error for widely striped files
- [compat] Compatibility fix for MySQL servers between 5.0.0 and 5.0.32

* Fri May 06 2011 Thomas Leibovici <thomas.leibovici@cea.fr> 2.3.0
- [optim.] instant accounting reports (user/group usage, fs content summary, ...)
- [reporting] split user usage per group (--split-user-groups option)
- [reporting] split group usage per user (--split-user-groups option)
- [feature] new policy criteria for Lustre FileSystems: ost_index
- [reporting] detailed FS scan statistics in "rbh-report -a"
- [misc.] fast and clean abort on ctrl^c (during scan, migration and purge)
- [admin.] automatically disables features that are not defined in config file
- [admin.] "rbh-config backup_db" helper to create a robinhood DB backup
- [misc.] -V option displays Lustre version and release number
- [tweak] changed 'watermark' parameters to 'threshold'
- [tweak] changed 'notify_lw' and 'alert_hw' parameters to 'alert_low' and 'alert_high'
- [database] alternative port or socket file can be used for MySQL connection
- [database] limiting DB access rights for reporting command
- [bugfix](major) fixed inconsistent pool names
- [bugfix](minor) kill -HUP terminated the process if no trigger was defined
- [bugfix](minor) 'unknown' status not correctly filtered in '--dump-status' report
- [bugfix](tweak) added 'reload' in short help of SLES init script
- [misc.] code cleaning, error message cleaning, removed some obsolete code
- [feature] new robinhood flavor to track modifications in a Lustre v2 filesystem, and backup data to an external storage (current status: Alpha testing only).
- [feature] soft rm + command to retrieve removed files
- [feature] disaster recovery command
- [feature] --migrate-file option to archive a single file
- [feature] pre-maintenance mode to smoothly backup the whole filesystem content before a due date.

* Wed Jan 05 2011 Thomas Leibovici <thomas.leibovici@cea.fr> 2.2.3
- [feature] periodic purge trigger
- [feature] options for controlling trigger notifications
- [doc] pdf documentation updated

* Thu Nov 25 2010 Thomas Leibovici <thomas.leibovici@cea.fr> 2.2.2
- [bugfix] fixed major issue of "duplicate key" errors
- [bugfix] FS scan sometimes blocks on Lustre 2
- [misc.] integration to automatic testing suite (Hudson)

* Fri Oct 22 2010 Thomas Leibovici <thomas.leibovici@cea.fr> 2.2.1
- [feature] new purge command: --purge-class to apply purge policy on files in a given class
- [feature] new migration command: --migrate-class to apply migration policy on files in a given class
- [feature] support of syslog for logging
- [report cmd] Added summary line to all reports, with total nbr entries and volume.
- [report cmd] Added '-q' option to hide headers and footers in reports.
- [optim.] changed primary key format to reduce DB requests (require to run "rbh-config empty_db" after upgrading to this version)
- [misc.] new command 'repair_db' in rbh-config, to fix tables after a MySQL server crash.
- [compat.] Support for Lustre MDT changelogs on Lustre v2.0 final
- [compat.] port to FreeBSD

* Mon Sep 20 2010 Thomas Leibovici <thomas.leibovici@cea.fr> 2.2.0p2
- [bugfix] retrieving Lustre pool fails with error "Unsupported Lustre magic number"
- [bugfix] wrong class matching on OST pools when scanning

* Wed Sep 08 2010 Thomas Leibovici <thomas.leibovici@cea.fr> 2.2.0p1
- [bugfix] unescaped SQL strings caused error on filenames with single quotes
- [bugfix] error in init script when RBH_OPT contains several options
- [misc.] a gap in OST index list should displays a warning, not an error
- [pkg] common spec file for both el4, el5 and el6

* Fri Aug 27 2010 Thomas Leibovici <thomas.leibovici@cea.fr> 2.2.0
- [feature] fileclass union/intersection/negation
- [feature] rbh-report displays last matched fileclass
- [feature] new reporting command '--class-info' generates fileclass summary
- [feature] new reporting option '--filter-class' to dump entries per fileclass
- [feature] alert batching: send a mail summary instead of 1 mail per matching entry
- [feature] alert improvements: named alerts, tweak changes
- [feature] special wildcard '**' in 'path ' or 'tree' conditions matches any count of directory levels
- [feature] quota-like purge triggers fully implemented (on group or user)
- [feature] triggers on used inode count in filesystem
- [feature] '--check-triggers' option to check triggers without purging files
- [feature] notification can be sent when a high watermark is reached (for triggers)
- [feature] rbh-config helper now supports batch commands
- [feature] Lustre 2.0 ready
- [optim.] configurable fileclass periodic matching to reduce calls to filesystem
- [optim.] configurable attr/path periodic update in DB to reduce calls to filesystem
- [bugfix] explicit trace when readdir fails
- [bugfix] issue when filtering on fields with NULL values in DB
- [bugfix] check migration timeout on last effective action, not on last queued entry
- [bugfix] name-based conditions complaining about missing auto-generated fields
- [bugfix] race condition when appplying policy lead to handle the same entry several times
- [bugfix] removing removed directories from database for recursive rmdir policies
- [misc.] added documented file in /etc/sysconfig for robinhood service parameters
- [misc.] changing source directory layout
- [misc.] documentation update

* Thu Jul 22 2010 Thomas Leibovici <thomas.leibovici@cea.fr> 2.1.5
- Major bug fix: incomplete database content after scan

* Tue Jun 22 2010 Thomas Leibovici <thomas.leibovici@cea.fr> 2.1.4
- New recursive rmdir policy (for TMP_FS_MGR purpose)
- changed default value for max_pending_operations
  (unlimited value could result in excessive memory usage)
- removing useless fields and redundant information in database
- rh-* commands renamed to rbh-*, to avoid conflicts and confusions
  with RedHat commands.
- check conflicting flags in configure

* Wed Apr 21 2010 Thomas Leibovici <thomas.leibovici@cea.fr> 2.1.3
- Support of relative paths for "path" and "tree" conditions
- Migration timeout mechanism
- SQLite support
- Prompting for database admin password in rh-config script

* Fri Mar 05 2010 Thomas Leibovici <thomas.leibovici@cea.fr> 2.1.2
- Made RPM relocatable
- New configuration helper script: "rh-config"
- New reporting commands: Dump all files (--dump-all) and dump files
  by status (--dump-status).
- BUG FIX: wrong scan duration when using volume-based purge triggers
- Lustre-HSM: Checking previous migrations when restarting
- Lustre-HSM: CL_TIME record support (bz 19505)
- Lustre-HSM: multi-archive support (archive_num)
- Lustre-HSM: new --sync option (immediately archive all modified files)
- Lustre-HSM: changed --handle-events action switch to --readlog

* Thu Dec 10 2009 Thomas Leibovici <thomas.leibovici@cea.fr> 2.1.1
- new reporting options: --dump-ost, --dump-user, --dump-group
- new --filter-path option to reporting tool
- Each purpose has its own service and binary names,
  to allow installing and running several robinhood with
  differents purposes on the same machine.

* Thu Sep 17 2009 Thomas Leibovici <thomas.leibovici@cea.fr> 2.1.0
- Includes most features for Lustre-HSM PolicyEngine (as Beta)
- Note: for testing purpose, this version applies HSM policies to all entries
whatever their HSM status (given that HSM status flags are not fully implemented
in Lustre yet).

* Mon Jul 20 2009 Thomas Leibovici <thomas.leibovici@cea.fr> 2.0.1
- New policy definition semantics, using filesets
- Multiple fileset/policy associations
- Several changes in configuration syntax, to avoid confusions
- Support of OST pool names (on Lustre) for fileset definition and policies
- Optimizations of policy application
- Added features for Lustre-HSM

* Mon Mar 23 2009 Thomas Leibovici <thomas.leibovici@cea.fr> 2.0.0-beta2
- Display warning for unknown parameters in config file
- Cosmetic fixes in config parsing
- Clean shutdown on SIGTERM or SIGINT
- Reloading dynamic parameters on SIGHUP (including numerical values in policy definition)

* Mon Mar 2 2009 Thomas Leibovici <thomas.leibovici@cea.fr> 2.0.0-beta1
- Reporting tool
- Empty directory removal
- Force purge actions on FS/OST
- Misc. improvements (stats, config, logs...)

* Mon Jan 26 2009 Thomas Leibovici <thomas.leibovici@cea.fr> 2.0.0-alpha
- Most Robinhood v1 features are supported