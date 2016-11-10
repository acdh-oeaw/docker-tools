#!/bin/bash

DIR=`dirname $0`
cd $DIR

###################
# Install system packages
###################
yum makecache fast
yum install -y yum-plugin-fastestmirror deltarpm epel-release
yum update -y
yum install -y docker docker-selinux httpd net-tools python-docker python-setuptools git xfsprogs mod_ssl vim links

###################
# Install docker-tools
###################
python setup.py build && sudo python setup.py install

cd /var/lib/docker
git clone https://github.com/acdh-oeaw/docker-tools-environments.git
mv docker-tools-environments images
git clone https://redmine.acdh.oeaw.ac.at/docker-tools-environments-priv.git
mv docker-tools-environments-priv/* images/
rm -fR docker-tools-environments
cd $DIR

cp -r system_files/* /

###################
# Configure Apache
###################
systemctl enable httpd
systemctl start httpd

###################
# Set permissions
###################
sed -i -e 's/dockerroot/docker/' /etc/group
sed -i -e 's/home +xfs +defaults /home +xfs +defaults,pquota /' /etc/fstab

# to enable volumes access for normal users
chmod +x /var/lib/docker
mkdir -p /var/lib/docker/images/tmp
chmod 777 /var/lib/docker/images/tmp

# SELinux context to allow docker access external mounts
semanage fcontext -a -t svirt_sandbox_file_t "/home(/.*)?"
restorecon -RF /home
chcon -R -t ssh_home_t /home/*/.ssh

# As apache is the reverse proxy it has to be able to connect
# via network
setsebool -P httpd_can_network_connect true

# in the default CentOs vagrant image the vagrant user does not belong to the users group
if [ "`grep vagrant /etc/group`" != "" ]; then
  sed -i -e 's/users:x:100:/users:x:100:vagrant/' /etc/group
fi

###################
# Configure Docker and prepare images
###################
systemctl enable docker-storage-setup
systemctl start docker-storage-setup
systemctl enable docker
systemctl start docker

echo 'To build images run'
echo '  docker-build-images -v /var/lib/docker/images/ --skip envToSkip1 envToSkip2'
