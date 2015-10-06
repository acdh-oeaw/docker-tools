#!/bin/python

# An application for automatic managment of docker images

import json
import os
import re
import stat
import subprocess

class Param(object):
  @staticmethod
  def isValidPath(p, msg = None):
    result = (not (re.search('^/', p) or re.search('^../', p) or re.search('/../', p))) and re.search('^[-_.a-zA-Z0-9]+$', p)
    if result == False and not msg is None :
      raise Exception(msg)
    return result

  @staticmethod
  def isValidFile(p, msg = None):
    result = os.path.isfile(p)
    if result == False and not msg is None :
      raise Exception(msg)
    return result

  @staticmethod
  def isValidDir(p, msg = None):
    result = os.path.isdir(p)
    if result == False and not msg is None :
      raise Exception(msg)
    return result

  @staticmethod
  def isValidName(p, msg = None):
    result = re.search('^[_.a-zA-Z0-9]+$', p)
    if result == False and not msg is None :
      raise Exception(msg)
    return result

  @staticmethod
  def isValidNumber(p, msg = None):
    result = re.search('^[0-9]+$', str(p))
    if result == False and not msg is None :
      raise Exception(msg)
    return result

  @staticmethod
  def isValidDomain(p, msg = None):
    result = re.search('^((([a-z0-9][-a-z0-9]*[a-z0-9])|([a-z0-9]+))[.]?)+$', str(p))
    if result == False and not msg is None :
      raise Exception(msg)
    return result

  @staticmethod
  def isValidAlias(p, msg = None):
    result = re.search('^/[-_.a-zA-Z0-9/]+$', str(p))
    if result == False and not msg is None :
      raise Exception(msg)
    return result

class Account:
  path = ''
  uid = -1
  gid = -1
  environments = []

  def __init__(self, name):
    Param.isValidName(name, 'account name contains forbidden characters')
    self.path = '/home/' + name
    Param.isValidDir(self.path, 'account does not exist')
    self.uid = os.stat(self.path).st_uid
    self.gid = os.stat(self.path).st_gid
  
  def readConfig(self):
    confFileName = self.path + '/config2.json'
    if os.path.isfile(confFileName):
      self.processConfig(json.load(open(confFileName, 'r')))

  def processConfig(self, conf):
    if not isinstance(conf, list) :
      raise Exception('configuration is of a wrong type')

    print self.path

    self.environments = []
    for envConf in conf:
      envConf['BaseDir'] = self.path
      envConf['UID']     = self.uid
      envConf['GID']     = self.gid
      if 'Type' in envConf :
        if   envConf['Type'] == 'PHP' :
          env = EnvironmentPHP(envConf)
        elif envConf and envConf['Type'] == 'WSGI' :
          env = EnvironmentWSGI(envConf)
        elif envConf['Type'] == 'Drupal6' :
          env = EnvironmentDrupal6(envConf)
        elif envConf['Type'] == 'Docker' :
          env = EnvironmentDocker(envConf)
        else :
          raise Exception('environment is of unsupported type (' + envConf['Type'] + ')')
      else :
        raise Exception('environment has no type')
      self.environments.append(env)

  def getServerNames(self):
    names = []
    for env in self.environments:
      names.append(env.ServerName)
    return names

class Environment(object):
  
  DockerName  = None
  UID         = None
  GID         = None
  BaseDir     = None
  ServerName  = None
  ServerAlias = []

  def __init__(self, conf):
    if not isinstance(conf, dict) :
      raise Exception('configuration is of a wrong type')

    if not 'DockerName' in conf or not Param.isValidName(conf['DockerName']) :
      raise Exception('DockerName is missing or wrong')
    self.DockerName = conf['DockerName']

    if not 'BaseDir' in conf or not Param.isValidDir(conf['BaseDir']) :
      raise Exception('Base dir is missing or wrong')
    self.BaseDir = conf['BaseDir']

    if not 'UID' in conf or not Param.isValidNumber(conf['UID']) :
      raise Exception('UID is missing or wrong')
    self.UID = conf['UID']

    if not 'GID' in conf or not Param.isValidNumber(conf['GID']) :
      raise Exception('GID is missing or wrong')
    self.GID = conf['GID']

    if 'ServerName' in conf and Param.isValidDomain(conf['ServerName']) :
      self.ServerName = conf['ServerName']

    if 'ServerAlias' in conf:
      self.processServerAlias(conf['ServerAlias'])

  def processServerAlias(self, conf):
    if not isinstance(conf, list):
      if not isinstance(conf, basestring):
        raise Exception('ServerAlias is not a string nor list')
      conf = [conf]

    for alias in conf:
      Param.isValidDomain(alias, alias + ' is not a valid domain')
    self.ServerAlias = conf

  proxyVHTemplate = """
<VirtualHost *:80>
  ServerName {ServerName}
  {ServerAlias}

  ProxyPreserveHost On
  ProxyPass        / http://127.0.0.1:{Port}/
  ProxyPassReverse / http://127.0.0.1:{Port}/
</VirtualHost>
"""

class EnvironmentHTTP(Environment):

  BaseDirMount = '/var/www/html'
  DocumentRoot = None
  AllowOverride = 'All'
  Options = 'None'
  Aliases = {}

  def __init__(self, conf):
    super(EnvironmentHTTP, self).__init__(conf)

    if not Param.isValidDomain(self.ServerName) :
      raise Exception('ServerName is missing or wrong')

    if not 'DocumentRoot' in conf or not Param.isValidPath(conf['DocumentRoot']) or not Param.isValidDir(self.BaseDir + '/' + conf['DocumentRoot']) :
      raise Exception('DocumentRoot is missing or wrong')
    self.DocumentRoot = conf['DocumentRoot']

    if 'AllowOverride' in conf :
      self.processAllowOverride(conf['AllowOverride'])

    if 'Options' in conf :
      self.processOptions(conf['Options'])

    if 'Aliases' in conf :
      self.processAliases(conf['Aliases'])

  def processAllowOverride(self, conf):
    dictionary = ['All', 'AuthConfig', 'FileInfo', 'Indexes', 'Limit', 'Options']
    
    if not isinstance(conf, list):
      if not isinstance(conf, basestring):
        raise Exception('AllowOverride is not a string nor list')
      conf = [conf]

    self.AllowOverride = ''
    for opt in conf:
      dictionary.index(opt)
      self.AllowOverride += ' ' + opt

  def processOptions(self, conf):
    dictionary = ['All', 'ExecCGI', 'FollowSymLinks', 'Includes', 'MultiViews', 'SymLinksIfOwnerMatch']
    
    if not isinstance(conf, list):
      if not isinstance(conf, basestring):
        raise Exception('Options is not a string nor list')
      conf = [conf]

    self.Options = ''
    for opt in conf:
      dictionary.index(opt)
      self.Options += ' ' + opt

  def processAliases(self, conf):
    if not isinstance(conf, dict) :
      raise Exception('Aliases is not a dictionary')

    for alias, path in conf.iteritems():
      Param.isValidAlias(alias, 'Wrong Alias name')
      Param.isValidPath(path, 'Wrong Alias path')
      Param.isValidDir(self.BaseDir + '/' + path, 'Wrong Alias path')
    self.Aliases = conf

class EnvironmentPHP(EnvironmentHTTP):
  def __init__(self, conf):
    super(EnvironmentPHP, self).__init__(conf)
    print 'Environment PHP'

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

class EnvironmentWSGI(EnvironmentHTTP):

  PythonPath = None
  WSGIPath   = None

  def __init__(self, conf):
    super(EnvironmentWSGI, self).__init__(conf)
    print 'Environment WSGI'

    if 'PythonPath' in conf :
      self.processPythonPath(conf['PythonPath'])
    else:
      self.PythonPath = self.DocumentRoot
    
    if 'WSGIPath' in conf and Param.isValidPath(conf['WSGIPath']) and Param.isValidFile(self.BaseDir + '/' + self.DocumentRoot + '/' + conf['WSGIPath']) :
      self.WSGIPath = conf['WSGIPath']
    else:
      self.WSGIPath = 'wsgi.py'

  def processPythonPath(self, conf):
    if not isinstance(conf, list):
      if not isinstance(conf, basestring):
        raise Exception('PythonPath is not a string nor list')
      conf = [conf]

    for path in conf:
      fullPath = self.BaseDir + '/' + self.DocumentRoot + '/' + path
      if not Param.isValidPath(path) or not (Param.isValidDir(fullPath) or Param.isValidFile(fullPath)) :
        raise Exception('PythonPath is wrong')
    self.PythonPath = conf

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
    print 'Environment Drupal6'

class EnvironmentDocker(Environment):
  def __init__(self, conf):
    super(EnvironmentDocker, self).__init__(conf)
    print 'Environment Docker'

    if 'ServerName' in conf and Param.isValidDomain(conf['ServerName']) :
      self.ServerName = conf['ServerName']

for accName in os.listdir('/home'):
  account = Account(accName)
  account.readConfig()

