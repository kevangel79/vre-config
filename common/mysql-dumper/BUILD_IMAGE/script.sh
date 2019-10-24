#!/bin/bash


echo "$(date): executing mysql backup cronjob..." >> /var/log/cron.log 2>&1

### Healthfile, to be read by healthcheck:
healthfile="/status.txt"
lastrunfile="/lastrunmoment.txt"
echo "NOT_STARTED" > $healthfile


###################
### Environment ###
###################

### Sourcing the environment:
source /etc/environment
# DONT PRINT ENV TO SCREEN, AS IT CONTAINS PASSWORD!
# TODO RUN THE DUMP WITHOUT PASSWORD IN CLI!
#cat /etc/environment  >> /var/log/cron.log 2>&1
#echo "That was the env." >> /var/log/cron.log 2>&1

######################
### File locations ###
######################

### Where to store dump and logs:
# FILEPATH is constant, as we will mount the proper directory into it!
export DUMP_PATH="/srv/mysql/backup"

### Construct file names:
DAY=`date +%a_%Hh%M`
dumpfile="${DUMP_PATH}/dashboard_database_dump_${DAY}.sql"
logfile="${DUMP_PATH}/dashboard_database_dump_${DAY}.log"
errfile="${DUMP_PATH}/dashboard_database_dump_${DAY}.err"
echo "$(date): backup to files: $dumpfile (logs: $logfile, $errfile)" >> /var/log/cron.log 2>&1
echo "$(date): Dump will be written to: $dumpfile"  >> $logfile 2>> $errfile

### Checking whether stdout goes to the logfile: It does!
#echo "This should go to stdout log."  >> $logfile 2>> $errfile

### Checking whether stderr goes to the errfile: It does!!
#echo "Now checking where err goes:"  >> $logfile 2>> $errfile
#cd idonotexist >> $logfile 2>> $errfile


############################
### Mandatory variables: ###
### Database access info ###
############################

echo "$(date): Now checking presence of vars:"  >> $logfile 2>> $errfile

MISSING_VARS=0

if [ -z ${MYSQL_USER+x} ]; then
        echo "$(date): FATAL: The variable MYSQL_USER is not set!"  >> /var/log/cron.log 2>&1
        echo "$(date): FATAL: The variable MYSQL_USER is not set!"  >> $logfile 2>> $errfile
        MISSING_VARS=1
else
        echo "$(date): The variable MYSQL_USER is set to '$MYSQL_USER'"  >> $logfile 2>> $errfile
fi


if [ -z ${MYSQL_DATABASE+x} ]; then
        echo "$(date): FATAL: The variable MYSQL_DATABASE is not set!"  >> /var/log/cron.log 2>&1
        echo "$(date): FATAL: The variable MYSQL_DATABASE is not set!"  >> $logfile 2>> $errfile
        MISSING_VARS=1
else
        echo "$(date): The variable MYSQL_DATABASE is set to '$MYSQL_DATABASE'"  >> $logfile 2>> $errfile
fi


if [ -z ${MYSQL_PASSWORD+x} ]; then
        echo "$(date): FATAL: The variable MYSQL_PASSWORD is not set!"  >> /var/log/cron.log 2>&1
        echo "$(date): FATAL: The variable MYSQL_PASSWORD is not set!"  >> $logfile 2>> $errfile
        MISSING_VARS=1
else
        echo "$(date): The variable MYSQL_PASSWORD is set to xxxxxx"  >> $logfile 2>> $errfile
fi


if [ $MISSING_VARS -eq 1 ]; then
        #>&2 echo "$(date): FATAL: Missing variables. Did not run the mysqldump command."
        echo "$(date): FATAL: Missing variables. Did not run the mysqldump command." >> $errfile 2>> $errfile
        echo "$(date): Missing variables! Exiting..."  >> /var/log/cron.log 2>&1
        echo "$(date): Missing variables! Exiting..."  >> $logfile 2>> $errfile
        echo "MISSING_VARS" > $healthfile
        exit 1
fi

##########################
### Optional variables ###
##########################

if [ -z ${MYSQL_PORT+x} ]; then
        echo "$(date): The variable MYSQL_PORT is not set. Using default: 3306"  >> /var/log/cron.log 2>&1
        echo "$(date): The variable MYSQL_PORT is not set. Using default: 3306"  >> $logfile 2>> $errfile
        MYSQL_PORT=3306
else
        echo "$(date): The variable MYSQL_PORT is set to '$MYSQL_PORT'"  >> $logfile 2>> $errfile
fi

if [ -z ${MYSQL_HOST+x} ]; then
        echo "$(date): The variable MYSQL_HOST is not set. Using default: 'db'"  >> /var/log/cron.log 2>&1
        echo "$(date): The variable MYSQL_HOST is not set. Using default: 'db'"  >> $logfile 2>> $errfile
        MYSQL_HOST="db"
else
        echo "$(date): The variable MYSQL_HOST is set to '$MYSQL_HOST'"  >> $logfile 2>> $errfile
fi



#####################
### ACTUAL BACKUP ###
#####################

echo "$(date): Running the mysql dump..."  >> $logfile 2>> $errfile
#mysqldump --user "$MYSQL_USER" --password="$MYSQL_PASSWORD" --host "$MYSQL_HOST" --port $MYSQL_PORT --result-file="$dumpfile" "$MYSQL_DATABASE" >> "$logfile" 2>> "$errfile" 
mysqldump --user "$MYSQL_USER" --host "$MYSQL_HOST" --port $MYSQL_PORT --result-file="$dumpfile" "$MYSQL_DATABASE" >> "$logfile" 2>> "$errfile"
CODE=$?
echo "$(date): mysql dump exit code: $CODE"  >> /var/log/cron.log 2>&1
echo "$(date): Finished running the mysql dump (exit code $CODE)..."  >> $logfile 2>> $errfile


# Fill the health check files:
seconds_epoch=`date +%s`
echo "$seconds_epoch" > $lastrunfile
echo "OK_$CODE" > $healthfile


# Done!
echo "$(date): executing mysql backup cronjob... done." >> /var/log/cron.log 2>&1
echo "$(date): DONE." >> /var/log/cron.log 2>&1

