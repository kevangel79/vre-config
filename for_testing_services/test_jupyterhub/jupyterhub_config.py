# Configuration file for Jupyter Hub
import os
c = get_config()


###
### Get all env variables
###

##
## Have to be set:
DOCKER_JUPYTER_IMAGE = os.environ['DOCKER_JUPYTER_IMAGE']
DOCKER_NETWORK_NAME = os.environ['DOCKER_NETWORK_NAME']
TEST_PW = os.environ.get('TEST_PW')
HOST_LOCATION_USERDIRS = os.environ['HOST_LOCATION_USERDIRS'] # without trailing slash!
USE_SSL = os.environ['USE_SSL']


if USE_SSL.lower() == 'false':
  USE_SSL = False
else:
  USE_SSL = True

##
## Optional, have defaults:
RUN_AS_USER = os.environ.get('RUN_AS_USER', None)
RUN_AS_GROUP = os.environ.get('RUN_AS_GROUP', None)
MEMORY_LIMIT = os.environ.get('MEMORY_LIMIT', '2G')
HUB_IP = os.environ.get('HUB_IP', 'hub')
HTTP_TIMEOUT = os.environ.get('HTTP_TIMEOUT', '60')
USERDIR_INSIDE_CONTAINER = os.environ.get('USERDIR_INSIDE_CONTAINER', None)



# Fix
CONTAINER_PREFIX = 'vretest'

##
## Memory limits
## https://github.com/jupyterhub/dockerspawner#memory-limits
c.Spawner.mem_limit = MEMORY_LIMIT

##
## spawn with Docker
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'

##
## Notebook Directory
## https://github.com/jupyterhub/dockerspawner#data-persistence-and-dockerspawner
## Please no trailing slash!
##
## Explicitly set notebook directory because we'll be mounting a host volume to
## it.  Most jupyter/docker-stacks *-notebook images run the Notebook server as
## user `jovyan`, and set the notebook directory to `/home/jovyan/work`.
## We follow the same convention.
NOTEBOOK_DIR = '/home/jovyan/work'
c.DockerSpawner.notebook_dir = NOTEBOOK_DIR

##
## Mount the user directory
## We mount the <username>_sync directory, which is the synchronizer target directory!
## We mount it to a subdirectory of the Notebook directory (so that the sync dir does not get
## crowded with weird Jupyter stuff...
## The {username} comes from dockerspawner's volumenamingstrategy.py, and from JupyterHub's
## base handler which constructs a User object from the result of the authenticate() method,
## where we return a username (so we control that!)
if USERDIR_INSIDE_CONTAINER is None:
  USERDIR_INSIDE_CONTAINER = NOTEBOOK_DIR

c.DockerSpawner.volumes = {
    HOST_LOCATION_USERDIRS+'/{username}/': USERDIR_INSIDE_CONTAINER+'/nextcloud',
}

##
## Which docker image to be spawned
c.DockerSpawner.image = DOCKER_JUPYTER_IMAGE

##
## Prefix for the container's names:
c.DockerSpawner.prefix = CONTAINER_PREFIX

##
## Which authenticator to use
c.JupyterHub.authenticator_class = 'vretestauthenticator.VRETestAuthenticator'

##
## Set the log level by value or name.
c.JupyterHub.log_level = 'DEBUG'
c.DockerSpawner.debug = True

##
## Timeout (in seconds) before giving up on a spawned HTTP server
## Once a server has successfully been spawned, this is the amount of time we
## wait before assuming that the server is unable to accept connections.
c.Spawner.http_timeout = int(HTTP_TIMEOUT)

##
## Enable passing env variables to containers from the 
## authenticate-method (which has the login form...)
c.Authenticator.enable_auth_state = True

##
## Logo file
c.JupyterHub.logo_file = "/usr/local/share/jupyter/hub/static/images/logo.png"

##
## Set admin password
c.VRETestAuthenticator.test_pw = TEST_PW


###########################
## Run as different user ##
###########################

## Default is 1000:100
## See:
## https://groups.google.com/forum/#!topic/jupyter/-VJXHy5hnfM
## Two steps are needed:
## (1/2): Tell it to spawn as root:
c.DockerSpawner.extra_create_kwargs = {'user' : '0'}

## (2/2): Tell it to run as NB_UID:NB_GID:
## Note: We will also chown the directory to this user, in "pre_spawn_start"
container_env = {}

if RUN_AS_USER is not None:
  container_env['NB_UID'] = RUN_AS_USER

if RUN_AS_GROUP is not None:
  container_env['NB_GID'] = RUN_AS_GROUP

c.DockerSpawner.environment = container_env


##################
## SSL settings ##
##################

## If hub runs inside a container, do not change these, but mount
## the cert and key to the correct location.
## Both must be set!

if USE_SSL:

  ## Path to SSL certificate file for the public facing interface of the proxy 
  c.JupyterHub.ssl_cert = '/srv/jupyterhub/ssl/certs/myhost_cert_and_chain.crt'

  ## Path to SSL key file for the public facing interface of the proxy
  c.JupyterHub.ssl_key = '/srv/jupyterhub/ssl/private/myhost.key'


#######################
## Docker networking ##
#######################

##
## Pass the IP where the instances can access the JupyterHub instance
## The docker instances need access to the Hub, so the default loopback port doesn't work:
##from jupyter_client.localinterfaces import public_ips
##c.JupyterHub.hub_ip = public_ips()[0]
## Instead, containers will access hub by container name on the Docker network
c.JupyterHub.hub_ip = HUB_IP

##
## Connect containers to this Docker network
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = DOCKER_NETWORK_NAME

##
## Pass the network name as argument to spawned containers
## TODO: What for? Seems to work fine without it!
c.DockerSpawner.extra_host_config = { 'network_mode': DOCKER_NETWORK_NAME }

################
## Login form ##
################

##
## Custom login form
c.VRETestAuthenticator.custom_html = """<form action="/hub/login?next=" method="post" role="form">
  <div class="auth-form-header">
    Alternative Login
  </div>
  <div class='auth-form-body'>
    <h3>SeaDataCloud Virtual Research Environment</h3>
    
    <p>This is a JupyterHub for the SeaDataCloud VRE. This is a test login, you can <em>not</em> use your <em>Marine-ID</em>.</p>
    <div id="form_elements" style="display: none" >

        <label for="username_input">VRE username:</label>
        <input
          id="username_input"
          type="text"
          autocapitalize="off"
          autocorrect="off"
          class="form-control"
          name="username"
          value=""
          tabindex="1"
          autofocus="autofocus"
        />

        <label for='password_input'>VRE password:</label>
        <input
          type="password"
          class="form-control"
          name="password"
          id="password_input"
          tabindex="2"
        /> 
        <label for='vre_displayname_input'>Display name:</label>
        <input
          type="text"
          class="form-control"
          name="vre_displayname"
          id="vre_displayname_input"
          value = "Grace Hopper"
        />
        <label for='fileselection_path_input'>File selection (path):</label>
        <input
          type="text"
          class="form-control"
          name="fileselection_path"
          id="fileselection_path_input"
          value = "/Photos/Hummingbird.jpg"
        />

        <input
          type="submit"
          id="login_submit"
          class='btn btn-jupyter'
          value='Sign In'
          tabindex="3"
    </div>
  </div>
</form>
<script>
function parse_query_string(query) {
  var vars = query.split("&");
  var query_string = {};
  for (var i = 0; i < vars.length; i++) {
    var pair = vars[i].split("=");
    // If first entry with this name
    if (typeof query_string[pair[0]] === "undefined") {
      query_string[pair[0]] = decodeURIComponent(pair[1]);
      // If second entry with this name
    } else if (typeof query_string[pair[0]] === "string") {
      var arr = [query_string[pair[0]], decodeURIComponent(pair[1])];
      query_string[pair[0]] = arr;
      // If third or later entry with this name
    } else {
      query_string[pair[0]].push(decodeURIComponent(pair[1]));
    }
  }
  return query_string;
}
// substitute username and token from query string if provided
// and submit form for login.
var query = window.location.search.substring(1);
var qs = parse_query_string(query);
if (qs.username) {
  document.getElementById("username_input").value  = qs.username;
}
if (qs.password) {
   document.getElementById("password_input").value  = qs.password;
}
if (qs.webdav_url) {
   document.getElementById("auth_url_input").value  = qs.auth_url;
}
if (qs.token) {
   document.getElementById("token_input").value  = qs.token;
   document.getElementsByTagName("form")[0].submit();
}
else {
  document.getElementById("form_elements").style.display = "block"
}
</script>

"""


