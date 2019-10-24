#!/bin/bash

# We want a backup at least twice per day (every 12 hours)
#MAX_SECONDS_SINCE_LAST=$((24 * 60 * 60 + 1))
# This is defined in the Dockerfile and can be overridden
# by the docker-compose!

# Read healthcheck file which contains success of last
# mysql dump script:
FILE_CONTENT=$(cat status.txt)
# If all went ok, the content is:
# FILE_CONTENT="OK_0"

# Compute when the last run was done:
LAST_RUN=$(cat lastrunmoment.txt)
NOW=`date +%s`
DIFF="$(($NOW - $LAST_RUN))"
#echo "DIFF: $DIFF"
#echo "MAX: $MAX_SECONDS_SINCE_LAST"
#echo "Seconds since last run: $DIFF"


if [ $FILE_CONTENT == "NOT_STARTED" ]; then
        echo "Healthcheck: No backup run yet!"
        echo "Seconds since start: $DIFF"
        exit 0

elif [ $FILE_CONTENT == "OK_0" ] && [ $DIFF -lt $MAX_SECONDS_SINCE_LAST  ]; then
        echo "Healthcheck ok!"
        echo "Seconds since last run: $DIFF"
        echo "Outcome of last run: $FILE_CONTENT"
        exit 0
else
        echo "Last run unsuccessful or too long ago!"
        echo "Seconds since last run: $DIFF"
        echo "Outcome of last run: $FILE_CONTENT"
        exit 1
fi
