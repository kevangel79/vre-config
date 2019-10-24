FROM ubuntu:latest

###https://github.com/cheyer/docker-cron

# Install cron
RUN apt-get update
RUN apt-get install cron

# Install mysql-client
RUN apt-get install -y mysql-client

# Add crontab file in the cron directory
ADD crontab /etc/cron.d/simple-cron

# Add shell script and grant execution rights
ADD script.sh /script.sh
RUN chmod +x /script.sh

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/simple-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Install vim (remove again!)
RUN apt-get install -y vim

# Add healthcheck script:
ADD healthcheck.sh /healthcheck.sh
RUN chmod +x /healthcheck.sh
RUN echo "0" > /lastrunmoment.txt && echo "NOT_STARTED" > /status.txt

# Add default cron job schedule (every hour at 0)
ENV CRON_SCHEDULE '0 * * * *'

# Add default maximum number of seconds after which healthcheck will be unhappy
#ENV MAX_SECONDS_SINCE_LAST=$((24 * 60 * 60 + 1))
ENV MAX_SECONDS_SINCE_LAST 86401

# Create password file for mysqldump:
# NOTE: Has to be in home of the user who runs the dump!
ADD my.cnf /root/.my.cnf

# Forward request and error logs to docker log collector
# https://serverfault.com/questions/599103/make-a-docker-application-write-to-stdout
# DOES NOT WORK! TEST BETTER!
#RUN ln -sf /dev/stdout /var/log/cron.log

# Run the command on container startup
#CMD cron && tail -f /var/log/cron.log
# Use entrypoint to first store the environment to /etc/environment:
ADD entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# docker build -t mysql-cron:20191024 .
# docker tag mysql-cron:20191024 registry-sdc.argo.grnet.gr/mysql-cron:20191024
# docker push registry-sdc.argo.grnet.gr/mysql-cron:20191024
#
