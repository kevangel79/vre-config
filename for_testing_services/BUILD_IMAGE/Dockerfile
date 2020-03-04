FROM jupyterhub/jupyterhub:1.2
# this is the  most recent on 20200304
# RUN which python     # /usr/bin/python
# RUN python --version # Python 2.7.17
# RUN which python3     # /usr/bin/python3
# RUN python3 --version # Python 3.6.9

# Before:
#FROM jupyterhub/jupyterhub:1.0.0
#RUN which python     # /opt/conda/bin/python
#RUN python --version # Python 3.6.7

# Add useful tools
RUN apt-get update && apt-get install -y vim

# Install spawner
RUN pip install --upgrade pip
RUN pip install dockerspawner==0.11.1 # most recent on 20200304, on pypi

# FOR LOCAL TESTING:
COPY ./auth_package jupyterhub-vretestauthenticator/
RUN cd ./jupyterhub-vretestauthenticator && ls -lpah && python3 setup.py install && cd ..

# This is only to check if it built correctly:
RUN python3 -c "import vretestauthenticator"

# docker build -t jupyterhub_vretest:20200304-2 .
# docker build -t registry-sdc.argo.grnet.gr/jupyterhub_vretest:20200304-2 .
# docker push registry-sdc.argo.grnet.gr/jupyterhub_vretest:20200304-2
