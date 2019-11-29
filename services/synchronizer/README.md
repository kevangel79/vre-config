# Synchronization via rsync, as a Flask server

## For installation:


### On remote host (where data should be synced from/to)

* Create user account as which the rsync should log in. It must have a home directory.
* Make sure the user has a password (needed for login to copy the public key to this host)
* Make sure the user can login via ssh (/etc/security/..., add "+ : vre : ALL", but before last line to NOT LOCK YOURSELF OUT!)
* Make sure rsync and ssh exist.
* Add the public key created on the other machine to the known keys of this user - this is better done from the other machine.


```
sudo groupadd vre
sudo useradd -m vre -g vre
sudo passwd vre
sudo vi /etc/security/access.conf # allow ssh for user vre
rsync --version # exists?
ssh --version   # exists?
```

### On local host (where service runs):

* In Dockerfile, add the name of the remote host(s) for adding the server key to known hosts. (TODO: This must be improved urgently!)
* Build docker image
* Make dir on local host that contains the data to be synced, and is readable by 999. Inside this, the directories of the users must already exist. For security reasons, we will not create them by the services. The names of the user directories must be the username that is passed to the services.
* Bind-mount that to : "/path/to/userdirs/:/srv/syncer/test/jupyterdirs/:rw"
* Create a key pair for ssh
* Copy the public key to the remote server(s)
* Bind-mount the private key into the container as: "/path/to/priv.key:/srv/syncer/test/KEYS/pubkey:ro"


```
# create image:
vi Dockerfile # add remote host name!
docker build -t syncer:20190822 .

# make user dirs:
mkdir /path/to/userdirs/
sudo chown -R 999 /path/to/userdirs/

mkdir KEYS
cd KEYS/
ssh-keygen -t rsa -b 2048 -f vre-rsync-key
ssh-copy-id -i ./vre-rsync-key vre@bluewhale.dkrz.de # prompts for password
sudo chown 999 ./vre-rsync-key

# check if the key copy worked:
ssh -i ./vre-rsync-key vre@bluewhale.dkrz.de # prompts for password
# if it did, exit back to the other server:
exit

# ready to go:
cd ..
# vi docker-compose.yml # adapt the paths to the dirs!
docker-compose up
# listens on port 5000, just plain http for now! # TODO make https, make flask productive by adding nginx, ...

```

## Images / branches

Please note that several images/branches exist:

* **devel-as33**: In this version, the synchronizer runs as user `www-data` with the uid `33`. This is suitable for installations where NextCloud runs as `www-data` with `33` (its default), and where no other service that runs as another user needs to read/write the data.
* In future, we might need to use other uids (e.g. `1000`, as DIVA runs as this one). This might be achieved by either assigning a different uid to `www-data`, or by creating a fresh user using `useradd`. Then, this service could run alongside other services that are running using different uids. For this, NextCloud also has to switch to the new uid.
* **devel-orca**: Here, the synchronizer runs as `root`, and the NextCloud data is writeable by all (`ugo+w`). This one should not be used. It was used on one machine, on which other services running as different uids had to access and write the data too.



## Testing

We will setup a test instance and test it, for local and remote synchronisation.

Test values we use (some of them are likely to be different in your test setup):

* Server running the synchronizer: `orca`
* Location of test directory on this server: `/home/alice/sync_tmp`
* Port to run synchronizer one: `5000`
* Remote server: `bluewhale`
* Domain of remote server: `grnet.gr`
* Location of test directory (target) on the remote server: `/foo/test/november/sync_target/`
* User on the remote server: `vre` (uid `501`)
* Directory on remote server: `xyz`
* Uid of the synchronizer (this is defined by the image you use, which you should select based on the user that runs NextCloud): `33`


### Setting up the server

Run these steps **on orca**:

```
# on orca:

# Create docker test network:
docker network create blub_tmp

# Make a directory for these tests:
TMPHOME="/home/alice/sync_tmp"
mkdir $TMPHOME
cd $TMPHOME

# Get config:
wget https://raw.githubusercontent.com/SeaDataCloud/vre-config/master/services/synchronizer/remotehosts.json

# Get docker-compose:
wget https://raw.githubusercontent.com/SeaDataCloud/vre-config/master/services/synchronizer/docker-compose.yml
```

Now adapt config:

* `<remoteserver>` must be `bluewhale`
* `<myusername>` must be `vre`
* `/path/to/sync_target/` must be `TODO` 
* `foo.bar.fr` must be your domain `grnet.gr` (servername and this toghether must be your remote server's FQDN)


Now adapt docker-compose:

* The network must be `blub_tmp`, not `vre` (two occurrences!)
* `HOST: 'manatee'` must be `HOST: 'orca'`
* `/path/to/nextcloud_data/` must be `./local_source/nextcloud_all/`
* `/path/to/localsync/nextcloud_data/` must be `./local_target/`
* WHITELIST_SERVERS must contain `bluewhale.grnet.gr`
* Image: TODO! Currently: `registry-sdc.argo.grnet.gr/syncer:20190930-orca`


Now create the test source and target directories and add content for test user "fritz". For the source directory, we imitate ownership and permission written by NextCloud (this was taken from GRNET server, so it is the ownership and permission that are created by the current VRE Nextcloud instance, 20191128).

```
# on orca:
mkdir local_target
sudo chown -R 33:33 local_target
mkdir -p local_source/nextcloud_all/fritz/files/Work/
echo "bla" > local_source/nextcloud_all/fritz/files/Work/test1.txt
sudo chown -R 33:33 local_source/nextcloud_all/fritz/
sudo chmod u+rwx local_source/nextcloud_all/fritz/
sudo chmod go+rx  local_source/nextcloud_all/fritz/
sudo chmod go-w   local_source/nextcloud_all/fritz/
```

Now start the synchronizer. THen you are already good to go to test the local synchronisation. But we will continue setting up the remote synchronisation.

Start:

```
# on orca:
docker-compose up
```


### Preparing the remote server

Run these steps **on bluewhale:**

On this server, we need the user `vre` to be created, with the uid `501:501`, and the user must be ssh-enabled.

If this has not been done yet, follow these steps:

```
# on bluewhale
sudo groupadd -g 100 vre
sudo useradd -u 1000 -m vre -g vre
sudo passwd vre # prompts for new password for this user
# possibly:
vi /etc/security/access.conf # enable vre for ssh access
```

Now create the test environment:

```
# on bluewhale:
TMPTARGET="/foo/test/november/sync_target"
sudo mkdir -p $TMPTARGET
sudo chown 501:501 $TMPTARGET
```

Run these steps **on orca:**

```
# on orca:
cd $TMPHOME
mkdir KEYS
cd KEYS/
ssh-keygen -t rsa -b 2048 -f vre-rsync-key # no passphrase!
ssh-copy-id -i ./vre-rsync-key vre@bluewhale.dkrz.de # prompts for password
sudo chown 33 ./vre-rsync-key # otherwise, permission error!
cd ..

# Test login
ssh -i ./KEYS/vre-rsync-key vre@bluewhale.dkrz.de # prompts for password
exit
```


### Test local synchronisation


Check the target **on orca** before:

```
# on orca:
cd $TMPHOME
ls -lpah local_target
# should be empty and owned by yourself with drwxr-xr-x

```

Now run the test using curl:

```
# on orca:
curl http://localhost:5001/sync/bidirectional/dkrz/orca/fritz/execute
```

Check the result:

* Check for error messages from this command (on orca)
* Check the output of the synchronizer (on orca)
* Check the content of the local target (on orca):

```
# on orca:
ls -lpah $TMPHOME/local_target/fritz_sync/
# Dir itself:           33:33   "rwxrwxrwx"
# Contains test1.txt:   33:33   "rw-rw-rw-"

# TODO: Why so open? Why is write added?

# Comparison with source:
ls -lpah local_source/nextcloud_all/fritz/files/Work/
# Dir itself:           33:33   "rwxr-xr-x"
# Contains test1.txt    33:33   "rw-r--r--"
```

### Test remote synchronisation


Check the target **on bluewhale** before the test:

```
# on bluewhale:
sudo ls -lpah $TMPTARGET/sync_target
# Dir itself: vre:vre   "rwxr-xr-x"
# Contains: Empty!
```


Now run the test **on orca** (adapt the server name and site in the command):

```
# on orca:
curl http://localhost:5001/sync/bidirectional/dkrz/bluewhale/fritz/execute
```
Check the result:

* Check for error messages from this command (on orca)
* Check the output of the synchronizer (on orca)
* Check the content of the remote target (on bluewhale):


```
on bluewhale:
sudo ls -lpah $TMPTARGET/sync_target/fritz_sync/
# Dir itself:               vre:vre     "rwxr-xr-x"
# Should contain test1.txt: vre:vre     "rw-r--r--"
```

Next, run those curl commands from another server, not via localhost, to check the firewall settings.



### Re-test

To recreate a clean test environment after a failed test:

```
# on orca:
cd $TMPHOME
docker-compose down

sudo rm -rf local_target
sudo rm -rf local_source
mkdir local_target
sudo chown -R 33:33 local_target
mkdir -p local_source/nextcloud_all/fritz/files/Work/
echo "bla" > local_source/nextcloud_all/fritz/files/Work/test1.txt
sudo chown -R 33:33 local_source/nextcloud_all/fritz/
sudo chmod u+rwx local_source/nextcloud_all/fritz/
sudo chmod go+rx  local_source/nextcloud_all/fritz/
sudo chmod go-w   local_source/nextcloud_all/fritz/
```

```
# on bluewhale:
sudo rm -rf $TMPTARGET
sudo mkdir -p $TMPTARGET
sudo chown 501:501 $TMPTARGET
```

```
# on orca:
cd $TMPHOME
docker-compose up
```

### Clean up

Final clean up after all tests:

```
# on orca:
cd $TMPHOME
docker-compose down
docker network remove blub_tmp
cd ..
rm -rf $TMPHOME

```

```
# on bluewhale:
sudo rm -rf $TMPTARGET

# remove user and group if you want
# uninstall unison if you want
```


### Debug ideas

In case of ssh login problems, first check the permissions of your private key - are you sure that the application can run it?

```
# on orca:
docker exec -it sync_tmp_syncer_1 /bin/bash
ls -lpah /srv/syncer/KEYS/
```

Then try Unison directly, also from inside the docker image:

```
# on orca:
docker exec -it sync_tmp_syncer_1 /bin/bash
unison -batch -times -sshargs="-p 22 -i /srv/syncer/KEYS/privkey" /srv/syncer/source/fritz/files/Work/ ssh://vre@bluewhale.dkrz.de///$TMPTARGET/fritz_sync
```

(This is the command also shown in the logs, but you need to add double quotes around the sshargs (after `sshargs=` and after `privkey`))

