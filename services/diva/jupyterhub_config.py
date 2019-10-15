import os

# RUN AS DIFFERENT USER FROM 1000 (not needed in most cases!)
# https://groups.google.com/forum/#!topic/jupyter/-VJXHy5hnfM
#c.DockerSpawner.extra_create_kwargs = {'user' : '0'}
#c.DockerSpawner.environment = {'NB_UID' : 'xxx'}

# Use this
# https://jupyterhub.readthedocs.io/en/stable/api/app.html#jupyterhub.app.JupyterHub.base_url
#  base_url c.JupyterHub.base_url = URLPrefix('/')
#     The base URL of the entire application.
#   Add this to the beginning of all JupyterHub URLs. Use base_url to run JupyterHub within an existing website.
###c.JupyterHub.base_url = '/diva/' # TODO!!

## Path to SSL certificate and key file for the public facing interface of the proxy
c.JupyterHub.ssl_cert = '/srv/jupyterhub/ssl/certs/myhost_cert_and_chain.crt'
c.JupyterHub.ssl_key = '/srv/jupyterhub/ssl/private/myhost.key'

## Authentication module
c.JupyterHub.authenticator_class = 'webdavauthenticator.WebDAVAuthenticator'
c.WebDAVAuthenticator.hub_is_dockerized = True
c.WebDAVAuthenticator.admin_pw = 'XXXXXXX'
# For testing:
#c.JupyterHub.authenticator_class = 'dummyauthenticator.DummyAuthenticator'
#c.DummyAuthenticator.password = 'XXXXXXX'

## Whitelist for WebDAV Servers
c.WebDAVAuthenticator.allowed_webdav_servers = [
    "https://orca.dkrz.de:8001/remote.php/webdav",
    "http://workspace/remote.php/webdav",
    "http://workspace/remote.php/webdav/",
    "https://dashboard.argo.grnet.gr:8001/remote.php/webdav/",
    "https://dashboard.argo.grnet.gr:8001/remote.php/webdav",
    "https://b2drop.eudat.eu/remote.php/webdav",
    "https://dox.ulg.ac.be/remote.php/webdav",
    "https://dox.uliege.be/remote.php/webdav",
    "https://dummy"
]


## To spawn Notebooks as containers:
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
c.DockerSpawner.image = os.environ['DOCKER_JUPYTER_IMAGE']
c.Authenticator.enable_auth_state = True # Important, otherwise cannot pass dict to spawner!

## Mount the directory that will contain the synced NextCloud data!!!
notebook_dir = os.environ.get('DOCKER_NOTEBOOK_DIR') or '/home/jovyan/work'
c.DockerSpawner.notebook_dir = notebook_dir
c.DockerSpawner.volumes = {
    '/path/to/sync_target/{username}_sync': notebook_dir+'/sync',
}

## Connect containers to this Docker network
network_name = os.environ['DOCKER_NETWORK_NAME']
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = network_name
# Pass the network name as argument to spawned containers
c.DockerSpawner.extra_host_config = { 'network_mode': network_name }
# User containers will access hub by container name on the Docker network
c.JupyterHub.hub_ip = os.environ['HUB_IP']

## Timeout (in seconds) before giving up on a spawned HTTP server
#  Once a server has successfully been spawned, this is the amount of time we
#  wait before assuming that the server is unable to accept connections.
c.Spawner.http_timeout = 60

## Log level
c.DockerSpawner.debug = True
c.JupyterHub.log_level = 'DEBUG'

# https://github.com/jupyterhub/jupyterhub/issues/379
# TODO: Correct place?? Correct url?
c.NotebookApp.tornado_settings = {
    'headers': {
        'Content-Security-Policy': "frame-ancestors xxx.xxx.xx:8000; "
    }
}

c.JupyterHub.tornado_settings = {
    'headers': {
        'Content-Security-Policy': "frame-ancestors *; ",
    }
}

# Custom login form
#                                                      

c.WebDAVAuthenticator.custom_html = """<form action="/hub/login?next=" method="post" role="form">
  <div class="auth-form-header">
    Alternative Login
  </div>
  <div class='auth-form-body'>
    <h3>SeaDataCloud Virtual Research Environment</h3>
    <p>This is the Jupyterhub for DIVAnd. Please use your NextCloud credentials, not your <em>Marine-ID</em>.</p>
    <!--p>The NextCloud credentials are normally hidden from you, because this instance of JupyterHub is intended for use with the <em>SeaDataCloud Virtual Research Environment</em> and with <em>Marine-ID</em> only.</p>
    <p>Please contact the administrators to find out about alternative login.</p-->
    <p>If you see this and you did log in via Marine-Id, there has been an error on the server, and we would be extremely grateful if you could notify us (when it happened, what is your Marine-Id, ...)!</p>
    <div id="form_elements" style="display: none" >
        <label for="username_input">WebDAV username:</label>
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
        <label for='password_input'>WebDAV password:</label>
        <input
          type="password"
          class="form-control"
          name="password"
          id="password_input"
          tabindex="2"
        />
        <input
          type="text"
          class="form-control"
          name="token"
          id="token_input"
          style="display: none"
        />
        <label for='webdav_url_input'>WebDAV URL:</label>
        <input
          type="text"
          class="form-control"
          name="webdav_url"
          id="webdav_url_input"
          xstyle="display: none"
          value = "https://dummy"
        />
        <input
          type="submit"
          id="login_submit"
          class='btn btn-jupyter'
          value='Sign In'
          tabindex="3"
        />
    </div>
  </div>
</form>
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
   document.getElementById("webdav_url_input").value  = qs.webdav_url;
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

