# docker-tools

Set of tools to make Docker administration easier

## Installation

### Installation on already running CentOs7 machine

* If you want to store Docker images on a separate partition (if you are installing it on the server, the answer is always YES), then:
    * Install docker
      `sudo yum install -y docker`
    * Adjust `/etc/sysconfig/docker-storage-setup`, e.g.
      ```
      STORAGE_DRIVER=devicemapper
      VG=centos00
      DATA_SIZE=50G
      GROWPART=false
      ```
    * Run
      ```
      systemctl enable docker-storage-setup
      systemctl start docker-storage-setup
      ```
    * Check created `/etc/sysconfig/docker-storage`
      You may consider adding `--storage-opt dm.min_free_space=5%` to it (the default is 10%)
* Clone this repo and enter its directory
* Consider adjusting configuration files in the `system_files` directory, especially:
    * `system_files/etc/httpd/conf.d/shared/ssl.conf` - path to your servers SSL key and cert files
    * `system_files/etc/cron.daily/docker` backup paths, etc.
* Run `./install.sh`

### Virtual Box VM creation and deployment on it

* Install VirtualBox and Vagrant
* Clone this repo, open console and go into the repo directory
* Run `vagrant up`
* You can log in 

### Installation instructions from Omar

Omar's installation creates a Virtual Box VM with the windows manager, Python IDE, etc.
You do not need all this stuff if you only want to test your services in ACDH server environment.

* Make sure docker docker-python httpd mod_ssl are already installed
* Create these non-standard directories if they don't exist:
** /etc/httpd/conf.d/sites-enabled
** /etc/httpd/conf.d/shared
* Install netstat
* Copy Apache config:
  cp etc-httpd-conf.d-shared-ssl_without_certs.conf /etc/httpd/conf.d/shared/
  cp etc-httpd-conf.d-zzz-sites.conf /etc/httpd/conf.d/
* Copy environment types Dockerfiles to /var/lib/docker/images:
  cp -pR images /var/lib/docker
  mkdir /var/lib/docker/images/tmp
* Set up system permissions:
  ./permissions
* Adjust docker-add-project to meet your requirements
** In particular see if you have a separate /home for xfs_quota else / will most probably be the right path
* Install admin scripts
  python setup.py build && sudo python setup.py install
* Register clean-up scripts in cron:
  cp etc-cron.daily-docker /etc/cron.daily/docker
* There is a slightly modified replacement for /etc/pki/tls/openssl.cnf in etc-pki-tls-openssl.cnf
** use it as is on a development machine to generate a self signed certificate for *.localdomain
** openssl genrsa -out localhost.key 2048
   openssl req -new -key localhost.key -out localhost.csr
   openssl x509 -req -days 365 -in localhost.csr -signkey localhost.key -out localhost.crt
   sudo cp localhost.crt /etc/pki/tls/certs/localhost.crt
   sudo cp localhost.key /etc/pki/tls/private/localhost.key
   sudo cp localhost.csr /etc/pki/tls/private/localhost.csr
   sudo restorecon -RvF /etc/pki
** replace *.localdomain and localhost on DNS.1 both with the machines name to create a production machine
   wildcard certificate; use different filenames perhaps; adjust /etc/httpd/conf.d/shared/ssl.conf.
* Enjoy

For Development:
* The CentOS default of requiretty in sudoers may be an obstacle. It can be commented out using sudo visudo
* You need sudo chmod g+w /etc/httpd/conf.d/sites-enabled/; sudo chgrp wheel /etc/httpd/conf.d/sites-enabled/
  so your development user is able to automatically create the apache config files.
* for creating the wildcard behavior in dns dnsmasq is used as a proxy dns. The configuration needs to be copied
  from etc-NetworkManager-dnsmasq.d-localdom-wildcard.conf to /etc/NetworkManager/dnsmasq.d/localdom-wildcard.conf
* In /etc/NetworkManager/NetworkManager.conf add dns=dnsmasq to the [main] section. Restart NetworkManager.service or
  reboot the development machine
* You can now use "ServerName" : "<name>.localdomain" on the development maching to access your environments
* Mozilla shows the usual warning for self signed certificates which you can allow and save permanently

## Usage

Included scripts are:

* `docker-manage-admin`
  Our workhorse for checking configuration, building images, running containers and accessing guest console
* `docker-manage`
  Alias for `docker-manage-admin` for unprivileged users so they do not have to type `sudo -g docker docker-manage`
* `docker-add-project`
  Script which properly adds new system user taking care of setting up quota, files required for ssh access, etc.
  You should use it instead of normal `useradd` or `adduser`
* `docker-clean`, `docker-register-proxy`, `docker-register-systemd`
  Helper scripts run by docker-manage
  There is no need to run them directly but if you are root, you can do it
* `docker-remove-unused-images`, `docker-remove-unused-containers`
  Clean-up scripts removing obsolete containers and images
  They are run by docker-manage and by cron, you can also run them manually
* `docker-check-quota`
  Script for quickly checking if we can safely extend quota limit or maybe we
  should ask ARZ to extend disk space first
* `docker-tools-update`
  Updates this tools by fetching the up to date version from the repository and installing it
