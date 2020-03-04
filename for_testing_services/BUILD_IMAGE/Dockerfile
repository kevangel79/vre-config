FROM jupyterhub/jupyterhub:1.0.0
# this is the  most recent on 20190521
#RUN which python     # /opt/conda/bin/python
#RUN python --version # Python 3.6.7

# Add useful tools
RUN apt-get update && apt-get install -y vim

# Install spawner
RUN pip install dockerspawner==0.11.1 # most recent on 20190521, on pypi

# FOR LOCAL TESTING:
COPY ./auth_package jupyterhub-vretestauthenticator/
RUN cd ./jupyterhub-vretestauthenticator && ls -lpah && python setup.py install && cd ..

# This is only to check if it built correctly:
RUN python -c "import vretestauthenticator"

# docker build -t jupyterhub_vretest:20200304 .
# docker build -t registry-sdc.argo.grnet.gr/jupyterhub_vretest:20200304
# docker push registry-sdc.argo.grnet.gr/jupyterhub_vretest:20200304
