#!/bin/bash

# remote host and credentials
RHOST=dashboard.argo.grnet.gr
RUSER=backup
SSHKEY=/root/.ssh/backup
# remote parent dir
RPARENTDIR=/home/backup
# local hostname, used for remote dir construction
# could use `hostname -f` but better be safe than sorry
HOSTNAME=sdc-test.argo.grnet.gr
# remote destination path
RPATH="$RPARENTDIR"/"$HOSTNAME"/
#
# local directories to be rsynced
#
DIRECTORY="/var/backup_vre"
LPATH="/var/backup_vre"
# use rsync for copy
COPYCMD=(/usr/bin/rsync -e "/usr/bin/ssh -i $SSHKEY" -va)
#
# you shouldn't have to change anything below this line (famous last words)
#
printf -- "--------------------------------------------------------------------------------------\n"
printf "Backup of files to host %s begins at %s\n" "$RHOST" "`date`"
printf -- "--------------------------------------------------------------------------------------\n"
#for LPATH in "${DIRECTORIES[@]}"
#do
  printf "%q " "${COPYCMD[@]}" "$LPATH" "$RUSER"@"$RHOST":"$RPATH"
  printf "\n"
  "${COPYCMD[@]}" "$LPATH" "$RUSER"@"$RHOST":"$RPATH"
#done
printf -- "--------------------------------------------------------------------------------------\n"
printf "Backup of files to host %s completed at %s\n" "$RHOST" "`date`"
printf -- "--------------------------------------------------------------------------------------\n\n"