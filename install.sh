#!/bin/bash

cd dirname $0

###################
# Install docker-tools
###################
python setup.py build && sudo python setup.py install
mkdir -p /var/lib/docker/images
cp -r images/* /var/lib/docker/images/
cp -r system_files/* /

###################
# Install system packages
###################
yum makecache fast
yum install -y yum-plugin-fastestmirror deltarpm epel-release
yum update -y
yum install -y docker docker-selinux httpd net-tools python-docker git xfsprogs

###################
# Configure Apache
###################
mkdir /etc/httpd/conf.d/sites-enabled
mkdir /etc/httpd/conf.d/shared
systemctl enable httpd
systemctl start httpd

###################
# Set permissions
###################
sed -i -e 's/dockerroot/docker/' /etc/group
sed -i -e 's/home +xfs +defaults /home +xfs +defaults,pquota /' /etc/fstab

# to enable volumes access for normal users
chmod +x /var/lib/docker
chmod 777 /var/lib/docker/images/tmp

# SELinux context to allow docker access external mounts
semanage fcontext -a -t svirt_sandbox_file_t "/home(/[^.].*)?"
restorecon -RvF /home

# As apache is the reverse proxy it has to be able to connect
# via network
setsebool -P httpd_can_network_connect true

###################
# Configure Docker and prepare images
###################
systemctl enable docker
systemctl start docker
