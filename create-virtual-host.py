#!/bin/bash

# An application for automatic managment of docker images

import os
import re

class Account:
  path = ''
  uid = -1
  gid = -1
  environments = []

  def __init__(self, name):
    if not re.search('[-_.a-zA-Z0-9]', name) :
      raise Exception('account name contains forbidden characters')
    self.path = '/home/' + name
    if not os.path.isdir(self.path) :
      raise Exception('account does not exist')
    self.uid = os.stat(self.path).st_uid
    self.gid = os.stat(self.path).st_gid
  
  def readConfig(self):
    confFileName = self.path + '/config.json'
    if os.path.isfile(confFileName):
      self.processConfig(json.load(open(confFileName, 'r')))

  def processConfig(self, conf):
    if not isinstance(conf, dict) :
      raise Exception('configuration is of a wrong type')
    self.environments = []
    for envConf in conf:
      conf.baseDir = self.path
      conf.uid     = self.uid
      conf.gid     = self.gid
      if   'type' in envConf and envConf['type'] == 'PHP' :
        env = EnvironmentPHP(envConf)
      elif 'type' in envConf and envConf['type'] == 'WSGI' :
        env = EnvironmentWSGI(envConf)
      elif 'type' in envConf and envConf['type'] == 'Drupal6' :
        env = EnvironmentDrupal6(envConf)
      elif 'type' in envConf and envConf['type'] == 'Docker' :
        env = EnvironmentDocker(envConf)
      else :
        raise Exception('environment has no type or is of unsupported type')
      self.environments.append(env)

  def getServerNames(self):
    names = []
    for env in self.environments:
      names.append(env.ServerName)
    return names

class Environment:
  conf = {}

  def __init__(self, conf):
    self.conf = conf
    if not isinstance(self.conf, dict) :
      raise Exception('configuration is of a wrong type')
    if not 'DockerName' in self.conf :
      raise Exception('DockerName is missing')
    

  def isComplete(self):
    return False

  proxyVHTemplate = """
<VirtualHost *:80>
  ServerName {ServerName}
  {ServerAlias}

  ProxyPreserveHost On
  ProxyPass        / http://127.0.0.1:{Port}/
  ProxyPassReverse / http://127.0.0.1:{Port}/
</VirtualHost>
"""

class EnvironmentPHP(Environment):
  def __init__(self, conf):
    super(EnvironmentPHP, self).__init__(conf)

  guestVHTemplate = """
<VirtualHost *:80>
  ServerName {ServerName}
  DocumentRoot {DocumentRoot}
  {ServerAlias}
  AssignUserID {UID}

  <Directory {DocumentRoot}>
    Require all granted
    AllowOverride {AllowOverride}
    {Options}
  </Directory>

  {Aliases}
</VirtualHost>    
"""

class EnvironmentWSGI(Environment):
  def __init__(self, conf):
    super(EnvironmentWSGI, self).__init__(conf)

  guestVHTemplate = """
<VirtualHost *:80>
  ServerName {ServerName}
  {ServerAlias}

  WSGIDaemonProcess {ServerName} user={UID} python-path={PythonPath}
  WSGIProcessGroup {ServerName}
  WSGIScriptAlias / {WSGIPath}

  <Directory {DocumentRoot}>
    Require all granted
  </Directory>

  {Aliases}
</VirtualHost>
"""

class EnvironmentDrupal6(EnvironmentPHP):
  def __init__(self, conf):
    super(EnvironmentDrupal6, self).__init__(conf)

class EnvironmentDocker(Environment):
  def __init__(self, conf):
    super(EnvironmentDocker, self).__init__(conf)

