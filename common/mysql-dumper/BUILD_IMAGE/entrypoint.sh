#!/bin/bash

# Write the environment into a file for cron to be able to access it:
#https://stackoverflow.com/questions/27771781/how-can-i-access-docker-set-environment-variables-from-a-cron-job
#echo "This is the environment:"
#printenv

echo "Writing the environment to /etc/environment."
printenv | grep -v "no_proxy" >> /etc/environment

# Replace the cron pattern
echo "Cron schedule: ${CRON_SCHEDULE}"
sed -i -e "s/XYZ/${CRON_SCHEDULE}/g" /etc/cron.d/simple-cron
#echo "Cron schedule: "
#head -1 /etc/cron.d/simple-cron

# Add the start of this script, for the health check, which
# checks the number of seconds since the last backup...
NOW=`date +%s`
echo $NOW > /lastrunmoment.txt
echo "Starting at: $NOW"

# Add the password to the password file
# so it does not turn up in the cli logs
# but it is still in the env, which is not ideal!!
sed -i -e "s/XYZ/${MYSQL_PASSWORD}/g" /root/.my.cnf

# Run cron in foreground to keep the docker running:
# https://stackoverflow.com/questions/27771781/how-can-i-access-docker-set-environment-variables-from-a-cron-job
#echo "Running cron in foreground..."
#cron -f
# Problem: Then we cannot send the cron.log to stdout...


# Run cron, then taill -f to keep the docker running
# First echo something into the log, otherwise it does not work
# Maybe because the log does not exist yet.
echo "Start of cron-log" >> /var/log/cron.log
cron && tail -f /var/log/cron.log

