import os
import traitlets
import tornado
import jupyterhub.auth

import logging
LOGGER = logging.getLogger(__name__)
root = logging.getLogger()
root.setLevel(logging.DEBUG)

# User id and group id for the user's directory. Must match those used in the
# spawned container. Default is 1000:100. In the container they can be changed,
# and are set to the env vars 'NB_UID', 'NB_GID', but those are only available
# inside the container, so we cannot use them here.
# See:
# https://github.com/jupyter/docker-stacks/blob/7a3e968dd21268c4b7a6746458ac34e5c3fc17b9/base-notebook/Dockerfile#L10
USERDIR_OWNER_ID_DEFAULT = 1000
USERDIR_GROUP_ID_DEFAULT = 100


class VRETestAuthenticator(jupyterhub.auth.Authenticator):

    # The following attributes can be set in the hub's
    # jupyterhub_config.py:

    # Custom HTML Login form
    custom_html = traitlets.Unicode(
        "",
        config = True)

    # Allow a password to be configured, so we can login without a valid
    # WebDAV account or access to a WebDAV server:
    test_pw = traitlets.Unicode(
        None, allow_none = True,
        config = True)

    # Only if JupyterHub runs in a container:
    # Where the userdirectory location will be mounted-to.
    # This dir needs to be used inside the docker-compose file of the hub!!!
    basedir_in_hub_docker = traitlets.Unicode(
        '/usr/share/userdirectories/',
        config = True)

    @tornado.gen.coroutine
    def authenticate(self, handler, data):
        logging.debug("Calling authenticate()...")

        # Get variables from the login form:
        username = data.get('username', None)
        password = data.get('password', None)
        vre_displayname = data.get('vre_displayname', '')

        webdav_mount_username = data.get('webdav_mount_username', '')
        webdav_mount_password = data.get('webdav_mount_password', '')
        webdav_mount_url = data.get('webdav_mount_url', '')
        fileselection_path = data.get('fileselection_path', '')

        if username is None:
            LOGGER.debug('Missing username...')
            return None

        if password is None:
            LOGGER.debug('Missing password...')
            return None

        if not password == self.test_pw:
            LOGGER.debug('Wrong password...')
            return None

        else:
            LOGGER.debug('Authentication successful!')

        # Return dict for use by spawner
        # See https://jupyterhub.readthedocs.io/en/stable/reference/authenticators.html#using-auth-state
        auth_state = {
                "name": username,
                "auth_state": {
                    "vre_username": username,
                    "vre_displayname": vre_displayname,
                    "webdav_mount_password": webdav_mount_password,
                    "webdav_mount_username": webdav_mount_username,
                    "webdav_mount_url": webdav_mount_url,
                    "fileselection_path": fileselection_path,
                }}
        LOGGER.debug("return auth_state: %s" % auth_state)
        return auth_state



    def get_user_dir_path(self, spawner):

        userdir = None

        # Get bind-mount into spawned container
        userdir_on_host = None
        try:
            # the host directories (as dict) which are bind-mounted, e.g.
            # {'/path/on/host': {'bind': '/path/in/spawned/container', 'mode': 'rw'}}
            LOGGER.debug("On host:  spawner.volume_binds: %s", spawner.volume_binds)

            # list of container directories which are bind-mounted, e.g.
            # ['/path/in/spawned/container']
            LOGGER.debug("In cont.: spawner.volume_mount_points: %s", spawner.volume_mount_points)

            userdir_on_host = list(spawner.volume_binds.keys())[0]

        # Stop if no mount:
        except IndexError as e:
            LOGGER.error('Did not find volume on host: %s' % e)
            LOGGER.error('************* No volumes mounted into the container.')
            LOGGER.warning('There is no point in using the user directory ' +
                        'if it is not mounted into the spawned container.')
            return None

        LOGGER.debug("All mount points in the spawned container: %s",
            spawner.volume_mount_points)
        userdir_in_spawned = spawner.volume_mount_points[0]

        # Get dir name (how it's named on the host):
        userdirname = os.path.basename(userdir_on_host.rstrip('/'))

        # As JupyterHub runs inside a container, use the dir where it's mounted:
        if not os.path.isdir(self.basedir_in_hub_docker):
            LOGGER.error('The directory does not exist: %s (for security reasons, we will not create it here. Make sure it is mounted!' % self.basedir_in_hub_docker)
            return None

        userdir_in_hub = os.path.join(self.basedir_in_hub_docker, userdirname)

        # All my logging, I will send to you...
        LOGGER.info('User directory will be: %s (bind-mounted from %s).',
            userdir_in_hub, userdir_on_host)
        LOGGER.info('User directory will be availabe in the spawned container as: %s',
            userdir_in_spawned)

        # Return:
        return userdir_in_hub

 


    '''
    Create the user's directory before the user's container is
    spawned. If intermediate directories don't exist, they are not created,
    for security reasons.

    The directory will then be mounted into the user's container. IMPORTANT:
    This has to configured in jupyterhub_config.py, e.g.:
    c.DockerSpawner.volumes = { '/path/on/host/juser-{username}': '/home/jovyan/work' }

    :param userdir: Full path of the directory.
    '''
    def create_user_directory(self, userdir):

        LOGGER.info("Preparing user's directory (on host or in hub's container): %s", userdir)

        # Create if not exist:
        if os.path.isdir(userdir):
            LOGGER.debug('User directory exists already (owned by %s)!' % os.stat(userdir).st_uid)

        else:
            try:
                LOGGER.debug("Creating dir, as it does not exist.")
                os.mkdir(userdir)
                LOGGER.debug('User directory was created now (owned by %s)!' % os.stat(userdir).st_uid)

            except FileNotFoundError as e:
                LOGGER.error('Could not create user directory (%s): %s', userdir, e)
                LOGGER.debug('Make sure it can be created in the context where JupyterHub is running.')
                superdir = os.path.join(userdir, os.path.pardir)
                LOGGER.debug('Super directory is owned by %s!' % os.stat(superdir).st_uid)               
                raise e # InternalServerError

        return userdir

    '''
    Chown the user's directory before the user's container is
    spawned.

    :param userdir: Full path of the directory.
    :param userdir_owner_id: UID of the directory to be created.
    :param userdir_group_id: GID of the directory to be created.
    '''
    def chown_user_directory(self, userdir, userdir_owner_id, userdir_group_id):

        # Note that in theory, the directory should already be owned by the correct user,
        # as NextCloud or the synchronization process should run as the same UID and have
        # created it.
        #
        # If the directory does not exist yet, it is created by whatever user runs JupyterHub
        # - likely root - so we may have to chown it!
        #
        # In other situations, chowning might be harmful, because whichever process that
        # created it, cannot read/write it anymore. You might want to switch this off!
        # 

        LOGGER.debug("stat before: %s",os.stat(userdir))

        # Check:
        if not os.stat(userdir).st_uid == userdir_owner_id:
            LOGGER.warn("The userdirectory is owned by %s (required: %s), chowning now!" % (os.stat(userdir).st_uid, userdir_owner_id))

        # Execute:
        try:
            LOGGER.debug("chown...")
            os.chown(userdir, userdir_owner_id, userdir_group_id)
        except PermissionError as e:
            LOGGER.error('Chowning not allowed, are you running as the right user?')
            raise e # InternalServerError

        LOGGER.debug("stat after:  %s",os.stat(userdir))
        return userdir

    '''
    Does a few things before a new Container (e.g. Notebook server) is spawned
    by the DockerSpawner:

    * Prepare the directory (to-be-bind-mounted into the container) on the host
    * Mount WebDAV-resource if requested

    This runs in the JupyterHub's container. If JupyterHub does not run inside
    a container, it runs directly on the host. If JupyterHub runs inside a container,
    certain things such as WebDAV mounts do not make sense, because they will not
    be visible on the host, as thus, in the spawned containers!

    Only works if auth_state dict is passed by the Authenticator.
    '''
    @tornado.gen.coroutine
    def pre_spawn_start(self, user, spawner):
        LOGGER.info('Preparing spawn of container for %s...' % user.name)

        # Get userdir name:
        userdir = self.get_user_dir_path(spawner)

        # Set userdir owner id:
        USERDIR_OWNER_ID = os.environ.get('RUN_AS_USER') or USERDIR_OWNER_ID_DEFAULT
        USERDIR_GROUP_ID = os.environ.get('RUN_AS_GROUP') or USERDIR_GROUP_ID_DEFAULT
        USERDIR_OWNER_ID = int(USERDIR_OWNER_ID)
        USERDIR_GROUP_ID = int(USERDIR_GROUP_ID)
        LOGGER.info('Will chown to : "%s:%s" (%s, %s)' % (USERDIR_OWNER_ID, USERDIR_GROUP_ID, type(USERDIR_OWNER_ID), type(USERDIR_GROUP_ID)))
        # See c.JupyterHub.base_url in JupyterHub URL Scheme docs
        # https://test-jupyterhub.readthedocs.io/en/latest/reference/urls.html
        BASE_URL = os.environ.get('BASE_URL', '')
            
        # Prepare user directory:
        # This is the directory where the docker spawner will mount the <username>_sync directory!
        # But we create it beforehand so that docker does not create it as root:root
        if userdir is not None:
            LOGGER.info('Preparing user directory...')
            self.create_user_directory(userdir)
            self.chown_user_directory(userdir, USERDIR_OWNER_ID, USERDIR_GROUP_ID)

        # Retrieve variables:
        auth_state = yield user.get_auth_state()

        # Create environment vars for the container to-be-spawned:
        # CONTAINER ENVIRONMENT DEFINED HERE:
        spawner.environment['VRE_USERNAME'] = auth_state['vre_username']
        spawner.environment['VRE_DISPLAYNAME'] = auth_state['vre_displayname']
        spawner.environment['WEBDAV_USERNAME'] = auth_state['webdav_mount_username']
        spawner.environment['WEBDAV_PASSWORD'] = auth_state['webdav_mount_password']
        spawner.environment['WEBDAV_URL'] = auth_state['webdav_mount_url']
        spawner.environment['FILESELECTION_PATH'] = auth_state['fileselection_path']
        spawner.environment['BASE_URL'] = BASE_URL

        # Done!
        LOGGER.debug("Finished pre_spawn_start()...")

