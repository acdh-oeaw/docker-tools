# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "centos/7"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  config.vm.provider "virtualbox" do |vb|
     # Display the VirtualBox GUI when booting the machine
     vb.gui = true
  
     # Customize the amount of memory on the VM:
     vb.memory = "2048"
     # Customize video memory
     vb.customize ["modifyvm", :id, "--vram", "32"]
     vb.customize ["modifyvm", :id, "--accelerate3d", "on"]
     vb.customize ["modifyvm", :id, "--clipboard", "bidirectional"]
     vb.customize ["modifyvm", :id, "--draganddrop", "bidirectional"]
  end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Define a Vagrant Push strategy for pushing to Atlas. Other push strategies
  # such as FTP and Heroku are also available. See the documentation at
  # https://docs.vagrantup.com/v2/push/atlas.html for more information.
  # config.push.define "atlas" do |push|
  #   push.app = "YOUR_ATLAS_USERNAME/YOUR_APPLICATION_NAME"
  # end

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "shell", inline: <<-SHELL
     sudo yum update -y
     sudo yum install -y epel-release
     sudo yum groups install -y "MATE Desktop"
     sudo yum groups install -y "X Window System"
     sudo systemctl set-default graphical.target
     sudo yum install -y dnsmasq java-1.7.0-openjdk wget git patch httpd docker docker-python
     sudo usermod -a -G docker vagrant
     # vagrant itself needs sudo to not requiretty so this default is already reverted 
     (cat | sudo tee /etc/NetworkManager/dnsmasq.d/localdomain-wildcard.conf) > /dev/null <<"EOF"
# Add local-only domains here, queries in these domains are answered
# from /etc/hosts or DHCP only.
local=/localdomain/
# Add domains which you want to force to an IP address here.
address=/.localdomain/127.0.0.1
address=/.localdomain/::1
EOF
     sudo sed -i -e '/.main./ a\
dns=dnsmasq' /etc/NetworkManager/NetworkManager.conf     
     sudo sed -i -e 's/dockerroot/docker/' /etc/group
     # to enable volumes access for normal users
     sudo chmod +x /var/lib/docker
     # SELinux context to allow docker access external mounts
     sudo semanage fcontext -a -t svirt_sandbox_file_t "/home(/.*)?"
     sudo restorecon -RvF /home
     (cat | sudo tee /etc/sudoers.d/docker-admin) > /dev/null <<"EOF"
%users  ALL=(:docker) NOPASSWD: /usr/sbin/docker-manage-admin
%docker ALL=(root)    NOPASSWD: /usr/sbin/docker-mount-volumes
%docker ALL=(root)    NOPASSWD: /usr/sbin/docker-register-systemd
%docker ALL=(root)    NOPASSWD: /usr/sbin/docker-register-proxy
%docker ALL=(root)    NOPASSWD: /usr/sbin/docker-clean
EOF
     sudo mkdir /etc/httpd/conf.d/sites-enabled
     sudo mkdir /etc/httpd/conf.d/sites-available
     sudo mkdir /etc/httpd/conf.d/shared
     sudo chmod g+w /etc/httpd/conf.d/sites-enabled/
     sudo chgrp wheel /etc/httpd/conf.d/sites-enabled/
     (cat | sudo tee /etc/httpd/conf.d/zzz-sites.conf) > /dev/null <<"EOF"
# ServerName localhost.localdomain
Include /etc/httpd/conf.d/sites-enabled/*.conf
EOF
     (cat | sudo tee /etc/httpd/conf.d/shared/ssl.conf) > /dev/null <<"EOF"
# For description look into /etc/httpd/conf.d/ssl.conf
SSLEngine on
SSLProtocol all -SSLv2
SSLCertificateFile /etc/pki/tls/certs/localhost.crt
SSLCertificateKeyFile /etc/pki/tls/private/localhost.key
# SSLCertificateChainFile /etc/pki/tls/certs/DigiCertCA.crt
SSLCipherSuite HIGH:MEDIUM:!aNULL:!MD5
<Files ~ "\.(cgi|shtml|phtml|php3?)$">
    SSLOptions +StdEnvVars
</Files>
<Directory "/var/www/cgi-bin">
    SSLOptions +StdEnvVars
</Directory>
BrowserMatch "MSIE [2-5]" \
         nokeepalive ssl-unclean-shutdown \
         downgrade-1.0 force-response-1.0
EOF
     # As apache is the reverse proxy it has to be able to connect
     # via network
     sudo setsebool -P httpd_can_network_connect true
     sudo patch /etc/pki/tls/openssl.cnf <<"EOF" 
--- /etc/pki/tls/openssl.cnf	2016-01-17 18:19:25.312532499 -0500
+++ etc-pki-tls-openssl.cnf	2016-01-17 18:19:38.040532499 -0500
@@ -123,7 +123,7 @@
 # WARNING: ancient versions of Netscape crash on BMPStrings or UTF8Strings.
 string_mask = utf8only
 
-# req_extensions = v3_req # The extensions to add to a certificate request
+req_extensions = v3_req # The extensions to add to a certificate request
 
 [ req_distinguished_name ]
 countryName			= Country Name (2 letter code)
@@ -149,6 +149,7 @@
 
 commonName			= Common Name (eg, your name or your server\'s hostname)
 commonName_max			= 64
+commonName_default		= *.localdomain
 
 emailAddress			= Email Address
 emailAddress_max		= 64
@@ -222,6 +223,10 @@
 
 basicConstraints = CA:FALSE
 keyUsage = nonRepudiation, digitalSignature, keyEncipherment
+subjectAltName = @alt_names
+
+[alt_names]
+DNS.1 = localhost
 
 [ v3_ca ]
 
EOF
     openssl genrsa -out localhost.key 2048
     openssl req -nodes -newkey rsa:2048 -key localhost.key -out localhost.csr -subj "/C=XX/ST=local/L=local/O=localdomain/OU=localhost/CN=*.localdomnain"
     openssl x509 -req -days 365 -in localhost.csr -signkey localhost.key -out localhost.crt
     sudo cp localhost.crt /etc/pki/tls/certs/localhost.crt
     sudo cp localhost.key /etc/pki/tls/private/localhost.key
     sudo cp localhost.csr /etc/pki/tls/private/localhost.csr
     sudo restorecon -RvF /etc/pki     
     wget https://download.jetbrains.com/python/pycharm-community-5.0.3.tar.gz
     tar -xzf pycharm-community-5.0.3.tar.gz
     mkdir -p .local/share/applications
     cat > .local/share/applications/jetbrains-pycharm-ce.desktop <<"EOF"      
[Desktop Entry]
Version=1.0
Type=Application
Name=PyCharm Community Edition
Icon=/home/vagrant/pycharm-community-5.0.3/bin/pycharm.png
Exec="/home/vagrant/pycharm-community-5.0.3/bin/pycharm.sh" %f
Comment=Develop with pleasure!
Categories=Development;IDE;
Terminal=false
StartupWMClass=jetbrains-pycharm-ce
EOF
  SHELL
end
