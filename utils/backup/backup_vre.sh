#!/bin/bash

set -ex
DATE=`date +%d-%m-%y`

# Create directory to copy files for back up
TEMP_DIR="/var/backup_vre/backup_vre_${DATE}/"
mkdir -p ${TEMP_DIR}

# Copy NextCloud files to backup directory
cp -R /root/vrehome/nextcloud/nextcloud_all ${TEMP_DIR}

# Copy 3 latest sql backup files to backup directory
cd /root/vrehome/mysql_backups/dashboard_mysql
ls -lt | tail -n3 | awk -v dir_path=${TEMP_DIR} '{system("cp " $9 " " dir_path)}'

# Create a tarball with the backup
cd /var/backup_vre/
tar -czvf backup_vre_${DATE}.tar.gz ./backup_vre_${DATE}

# Remove temp dir
rm -rf ${TEMP_DIR}

# Copy files to Archive server (Read script bellow for more information)
/root/vrehome/utils/scp_files.sh
