@echo off
setlocal
if "%1" == "-h" goto usage
if "%1" == "--help" goto usage
if "%1" == "" (
	SET CONFIGFILE=%cd%\ailbibak.conf.cmd
) else (
	SET CONFIGFILE=%1
)
if not exist "%CONFIGFILE%" (
	echo.
	echo Configuration file %CONFIGFILE% not found.
	goto create_config
)
goto main

:create_config
echo.
SET /p CREATECONFIG="Do you want to have a sample configuration file created (Y/N)?"
if "%CREATECONFIG%" == "Y" goto config_do
if "%CREATECONFIG%" == "y" goto config_do
if "%CREATECONFIG%" == "yes" goto config_do
if "%CREATECONFIG%" == "YES" goto config_do
if "%CREATECONFIG%" == "Yes" goto config_do
goto exit

:config_do
REM handle configuration file
IF EXIST %CONFIGFILE% goto main

REM generate default setting file
echo REM configuration file> %CONFIGFILE%
echo.>> %CONFIGFILE%
echo REM ## SOURCE: Local folder to backup, with trailing slash, eg. /home/meikalainen/ or /Documents\ and\ Settings/meikalainen>> %CONFIGFILE%
echo set SOURCE=/path/to/your/source/folder>> %CONFIGFILE%
echo.>> %CONFIGFILE%
echo REM ## BACKUP_LOGIN: username@domain for ssh. If you omit the username, ssh will use the Windows username, for example mydomain.fi *or* meikalainen@mydomain.fi>> %CONFIGFILE%
echo set BACKUP_LOGIN=meikalainen@mydomain.fi>> %CONFIGFILE%
echo.>> %CONFIGFILE%
echo REM ## REMOTE_FOLDER backup folder on the remote server with trailing slash, relative to the home directory, for example backups/my_documents/ *or* backups/settings/>> %CONFIGFILE%
echo set REMOTE_FOLDER=path/to/your/backup/folder/>> %CONFIGFILE%
echo.>> %CONFIGFILE%
echo REM ## EXCLUDES: the path to the  excludes-file (defines which files to exclude and include)>> %CONFIGFILE%
echo set EXCLUDES=your_excludes_file>> %CONFIGFILE%
echo.
echo #
echo # A default configuration file (%CONFIGFILE%) has been created.
echo # Review and edit that file, then run this process again.
echo #
goto exit

:main
call %CONFIGFILE%
if "%REMOTE_FOLDER%" == "" SET %REMOTE_FOLDER% = ./
rsync -av --rsync-path='R(){ N=${!#};C=${@:(-3):1};D=`date "+%%Y-%%m-%%d_%%H-%%M-%%S"`^&^&mkdir -p $N^&^&rsync "$@"^&^&cd $N^&^&rm -f $C^&^&cd ..^&^&mv `basename $N` $D^&^&cd $D^&^&ln -s $PWD $C;};R' --link-dest=../current --delete --iconv=ISO-8859-1,utf8 --exclude-from="%EXCLUDES%" "%SOURCE%" "%BACKUP_LOGIN%":"%REMOTE_FOLDER%"new
goto exit

:usage
echo Usage: ailbibak [-h] [--help] [config-file-path]
echo Default config-file-path = ailbibak.conf.cmd
echo Config-file-name has to have .cmd -extension

:exit
endlocal