#!/bin/python

# An application for automatic managment of docker images

import json
import os
import re
import stat
import subprocess
import collections

class HTTPReverseProxy(object):
  portNumber = 8000

  @staticmethod
  def getPort():
    HTTPReverseProxy.portNumber += 1
    return HTTPReverseProxy.portNumber

class Param(object):
  @staticmethod
  def isValidAbsPath(p):
    return not re.search('/../', p) and re.search('^/[-_.a-zA-Z0-9]+$', p)

  @staticmethod
  def isValidRelPath(p):
    return (not (re.search('^/', p) or re.search('^../', p) or re.search('/../', p))) and re.search('^[-/_.a-zA-Z0-9]+$', p)

  @staticmethod
  def isValidFile(p):
    return os.path.isfile(p)

  @staticmethod
  def isValidDir(p):
    return os.path.isdir(p)

  @staticmethod
  def isValidName(p):
    return re.search('^[-_.a-zA-Z0-9]+$', p)

  @staticmethod
  def isValidNumber(p):
    return re.search('^[0-9]+$', str(p))

  @staticmethod
  def isValidDomain(p):
    return re.search('^((([a-z0-9][-a-z0-9]*[a-z0-9])|([a-z0-9]+))[.]?)+$', str(p))

  @staticmethod
  def isValidAlias(p):
    return re.search('^/[-_.a-zA-Z0-9/]+$', str(p))

class Configuration:
  accounts = None

  def __init__(self):
    self.accounts = []

    for accName in os.listdir('/home'):
      account = Account(accName)
      account.readConfig()
      self.accounts.append(account)

  def check(self):
    domains = []
    ports = []
    names = []
    for account in self.accounts:
      domains += account.getDomains()
      ports += account.getPorts()
      names += account.getNames()

    duplDomains = [domain for domain, count in collections.Counter(domains).iteritems() if count > 1]
    duplPorts = [port for port, count in collections.Counter(ports).iteritems() if count > 1]
    duplNames = [name for name, count in collections.Counter(names).iteritems() if count > 1]

    for account in self.accounts:
      errors = account.check(duplDomains, duplPorts, duplNames, names)
      if len(errors) > 0 :
        print account.name, ': ', errors

  def apply(self):
    for account in self.accounts:
      account.apply()

class Account:
  base         = '/home'
  name         = ''
  path         = ''
  uid          = -1
  gid          = -1
  environments = None

  def __init__(self, name):
    self.environments = []

    if not Param.isValidName(name) :
      raise Exception('account name contains forbidden characters')
    self.name = name
    path = self.base + '/' + self.name
    if not Param.isValidDir(path) :
      raise Exception('account does not exist')
    self.uid = os.stat(path).st_uid
    self.gid = os.stat(path).st_gid
  
  def readConfig(self):
    print self.name
    confFileName = self.base + '/' + self.name + '/config2.json'
    if os.path.isfile(confFileName):
      print self.path
      self.processConfig(json.load(open(confFileName, 'r')))

  def processConfig(self, conf):
    if not isinstance(conf, list) :
      raise Exception('configuration is not a list')

    self.environments = []
    for envConf in conf:
      try:
        envConf['BaseDir'] = self.base + '/' + self.name
        envConf['UID']     = self.uid
        envConf['GID']     = self.gid
        envConf['Account'] = self.name
        if 'Type' in envConf :
          if   envConf['Type'] == 'HTTP' :
            env = EnvironmentHTTP(envConf)
          elif envConf['Type'] == 'Apache' :
            env = EnvironmentApache(envConf)
          elif envConf['Type'] == 'PHP' :
            env = EnvironmentPHP(envConf)
          elif envConf['Type'] == 'WSGI' :
            env = EnvironmentWSGI(envConf)
          elif envConf['Type'] == 'Drupal6' :
            env = EnvironmentDrupal6(envConf)
          elif envConf['Type'] == 'Generic' :
            env = Environment(envConf)
          else :
            raise Exception('environment is of unsupported type (' + envConf['Type'] + ')')
        else :
          raise Exception('environment has no type')
        self.environments.append(env)
      except Exception as e:
        print '  Error in ', (1 + len(self.environments)), ' environment: ', e

  def check(self, duplDomains, duplPorts, duplNames, names):
    errors = {}
    for env in self.environments:
      tmp = env.check(duplDomains, duplPorts, duplNames, names)
      if len(tmp) > 0 :
        errors[env.Name] = tmp
    return errors

  def apply(self):
    for env in self.environments:
      if env.ready :
        env.apply()

  def getDomains(self):
    domains = []
    for env in self.environments:
      domains += env.getDomains()
    return domains

  def getPorts(self):
    ports = []
    for env in self.environments:
      ports += env.getPorts()
    return ports

  def getNames(self):
    names = []
    for env in self.environments:
      names.append(env.Name)
    return names

class Environment(object):
  DockerImgBase = '/var/lib/docker/images'
  DockerMntBase = '/srv/docker'

  ready         = False
  Name          = None
  UID           = None
  GID           = None
  BaseDir       = None
  DockerfileDir = None
  Mounts        = None
  Links         = None
  Ports         = None

  def __init__(self, conf):
    self.Mounts      = []
    self.Links       = []
    self.Ports       = []

    if not isinstance(conf, dict) :
      raise Exception('configuration is of a wrong type')

    if not 'Account' in conf or not Param.isValidName(conf['Account']) :
      raise Exception('Account name is missing or invalid')
    if not 'Name' in conf or not Param.isValidName(conf['Name']) :
      raise Exception('Name is missing or invalid')
    self.Name = conf['Account'] + '-' + conf['Name']

    if not 'BaseDir' in conf or not Param.isValidDir(conf['BaseDir']) :
      raise Exception('Base dir is missing or invalid')
    self.BaseDir = conf['BaseDir']

    if not 'UID' in conf or not Param.isValidNumber(conf['UID']) :
      raise Exception('UID is missing or invalid')
    self.UID = conf['UID']

    if not 'GID' in conf or not Param.isValidNumber(conf['GID']) :
      raise Exception('GID is missing or invalid')
    self.GID = conf['GID']

    if (
      not 'DockerfileDir' in conf
      or not isinstance(conf['DockerfileDir'], basestring) 
      or not Param.isValidRelPath(conf['DockerfileDir'])
      or not (
        Param.isValidFile(self.BaseDir + '/' + conf['DockerfileDir'] + '/Dockerfile') 
        or Param.isValidFile(self.DockerImgBase + '/' + conf['DockerfileDir'] + '/Dockerfile')
      )
    ) :
      raise Exception('DockerfileDir is missing or invalid')
    self.DockerfileDir = conf['DockerfileDir']

    if 'Mounts' in conf :
      self.processMounts(conf['Mounts'])

    if 'Links' in conf :
      self.processLinks(conf['Links'])

    if 'Ports' in conf :
      self.processPorts(conf['Ports'])

  def processMounts(self, conf):
    if not isinstance(conf, list):
      conf = [conf]

    for mount in conf:
      if not isinstance(mount, dict) :
        raise Exception(str(len(self.mounts) + 1) + ' mount point description is not a dictionary')
      if (
        not 'Host' in mount  
        or not (Param.isValidRelPath(mount['Host']) or Param.isValidAbsPath(mount['Host'])) 
        or not (Param.isValidDir(self.BaseDir + '/' + mount['Host']) or Param.isValidFile(self.BaseDir + '/' + mount['Host']))
      ) :
        raise Exception(str(len(self.Mounts) + 1) + ' mount point host mount point is missing or invalid')
      if not 'Guest' in mount :
        raise Exception(str(len(self.Mounts) + 1) + ' mount point guest mount point is missing')
      if not 'Rights' in mount or (mount['Rights'] != 'ro' and mount['Rights'] != 'rw') :
        raise Exception(str(len(self.Mounts) + 1) + ' mount point access rights are missing or invalid')
      self.Mounts.append(mount)

  def processLinks(self, conf):
    if not isinstance(conf, list) :
      conf = [conf]

    for link in conf :
      if not isinstance(link, dict) :
        raise Exception(str(len(self.Links) + 1) + ' link definition is not a dictionary')
      if not 'Name' in link or not isinstance(link['Name'], basestring) :
        raise Exception(str(len(self.Links) + 1) + ' link container name is missing or invalid')
      if not 'Alias' in link or not isinstance(link['Alias'], basestring) :
        raise Exception(str(len(self.Links) + 1) + ' link alias is missing or invalid')
      self.Links.append(link)

  def processPorts(self, conf):
    if not isinstance(conf, list) :
      conf = [conf]

    for port in conf:
      if not isinstance(port, dict) :
        raise Exception(str(len(self.Ports) + 1) + ' port forwarding description is not a dictionary')
      if not 'Type' in port or not port['Type'] in ['HTTP', 'tunnel'] :
        raise Exception(str(len(self.Ports) + 1) + ' port forwarding type is missing or invalid')
      if not 'Host' in port or not Param.isValidNumber(port['Host']) or int(port['Host']) < 1000 or int(port['Host']) > 65535 :
        if 'Host' in port and port['Type'] == 'HTTP' and int(port['Host']) == 0 :
          port['Host'] = HTTPReverseProxy.getPort()
        else :
          raise Exception (str(len(self.Ports) + 1) + ' port forwarding host port is missing or invalid')
      if not 'Guest' in port or not Param.isValidNumber(port['Guest']) or int(port['Guest']) < 1 or int(port['Guest']) > 65535 :
        raise Exception(str(len(self.Ports) + 1) + ' port forwarding guest port is missing or invalid')
      self.Ports.append(port)

  def check(self, duplDomains, duplPorts, duplNames, names):
    errors = []
    if self.Name in duplNames :
      errors.append('Duplicated name: ' + self.Name)
    if self.ServerName in duplDomains :
      errors.append('Domain ' + self.serverName + ' is duplicated')
    for alias in self.ServerAlias:
      if alias in duplDomains :
        errors.append('ServerAlias ' + alias + ' is duplicated')
    for port in self.Ports:
      if port['Host'] in duplPorts :
        errors.append('Port ' + str(port) + ' is duplicated')
    for link in self.Links:
      if not link['Name'] in names :
        errors.append('Alias container ' + link['Name'] + ' does not exist')
    if len(errors) == 0 :
      self.ready = True
    return errors

  def apply(self):
    if not self.ready :
      raise Exception('Environment is not ready - it was not checked or there were errord during check')
    dockerOpts = self.getDockerOpts()
    if Param.isValidFile(self.BaseDir + '/' + self.DockerfileDir + '/Dockerfile') :
      dockerfileDir = self.BaseDir + '/' + self.DockerfileDir
    elif Param.isValidFile(self.DockerImgBase + '/' + self.DockerfileDir + '/Dockerfile') : 
      dockerfileDir = self.DockerImgBase + '/' + self.DockerfileDir
    else :
      raise Exception('There is no Dockerfile ' + self.DockerfileDir + ' ' + self.BaseDir)
    print ['docker-install-container', self.Name, dockerfileDir, dockerOpts]
    subprocess.call(['docker-install-container', self.Name, dockerfileDir, dockerOpts])

  def getPorts(self):
    ports = []
    for port in self.Ports:
      ports.append(port['Host'])
    return ports

  def getDomains(self):
    domains = []
    if not self.ServerName is None :
      domains.append(self.ServerName)
    domains += self.ServerAlias
    return domains

  def getDockerOpts(self):
    dockerOpts = ' -d'
    for mount in self.Mounts:
      dockerOpts += ' -v ' + self.BaseDir + '/' + mount['Host'] + ':' + mount['Guest'] + ':' + mount['Rights']
    for port in self.Ports:
      dockerOpts += ' -p ' + str(port['Host']) + ':' + str(port['Guest'])
    for link in self.Links:
      dockerOpts += ' --link ' + link['Name'] + ':' + link['Alias']
    return dockerOpts

class EnvironmentHTTP(Environment):
  ServerName    = None
  ServerAlias   = None
  Websockets    = None

  def __init__(self, conf):
    self.ServerAlias = []
    self.Websockets  = []
    super(EnvironmentHTTP, self).__init__(conf)

    if 'ServerName' in conf and Param.isValidDomain(conf['ServerName']) :
      self.ServerName = conf['ServerName']

    if 'ServerAlias' in conf:
      self.processServerAlias(conf['ServerAlias'])

    if 'Websockets' in conf :
      self.processWebsockets(conf['Websockets'])

  def processWebsockets(self, conf):
    if not isinstance(conf, list) :
      raise Exception('Websockets descriptions is not a list')
    for ws in conf:
      if not isinstance(ws, basestring) or not Param.isValidAlias(ws) :
        raise Exception(ws + ' is an invalid websocket path')
    self.Websockets = conf

  def processServerAlias(self, conf):
    if not isinstance(conf, list):
      if not isinstance(conf, basestring):
        raise Exception('ServerAlias is not a string nor list')
      conf = [conf]

    for alias in conf:
      if not Param.isValidDomain(alias) :
        raise Exception(alias + ' is not a valid domain')
    self.ServerAlias = conf

  def apply(self):
    super(EnvironmentHTTP, self).apply()
    self.configureProxy()

  def configureProxy(self):
    vhFileName = '/etc/httpd/conf.d/sites-enabled/' + self.Name + '.conf'
    vhFile = open(vhFileName, 'w')
    vhFile.write(self.ReverseProxyTemplate.format(
      ServerName = self.ServerName,
      ServerAlias = self.getServerAlias(),
      Port = str(self.getHTTPPort())
    ))
    vhFile.close()
    subprocess.call(['systemctl', 'reload', 'httpd'])

  def getDockerOpts(self):
    dockerOpts = super(EnvironmentHTTP, self).getDockerOpts()
    return dockerOpts

  def getServerAlias(self):
    serverAlias = self.ServerName
    for alias in self.ServerAlias:
      serverAlias += ' ' + alias
    return serverAlias

  def getHTTPPort(self):
    for port in self.Ports:
      if port['Type'] == 'HTTP' :
        return port['Host'] 

  ReverseProxyTemplate = """
<VirtualHost *:80>
  ServerName {ServerName}
  ServerAlias {ServerAlias}

  ProxyPreserveHost On
  ProxyPass        / http://127.0.0.1:{Port}/
  ProxyPassReverse / http://127.0.0.1:{Port}/
  <Proxy *>
    Require all granted
  </Proxy>
</VirtualHost>
"""

class EnvironmentApache(EnvironmentHTTP):
  DocumentRootMount  = '/var/www/html'
  DocumentRoot       = None
  AllowOverride      = 'All'
  Options            = 'None'
  Aliases            = None

  def __init__(self, conf):
    self.Aliases = []
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'http'
    super(EnvironmentApache, self).__init__(conf)
    self.Ports = [{ "Host" : HTTPReverseProxy.getPort(), "Guest" : 80 , "Type" : "HTTP"}]

    if not Param.isValidDomain(self.ServerName) :
      raise Exception('ServerName is missing or invalid')

    if not 'DocumentRoot' in conf or not Param.isValidRelPath(conf['DocumentRoot']) or not Param.isValidDir(self.BaseDir + '/' + conf['DocumentRoot']) :
      raise Exception('DocumentRoot is missing or invalid')
    self.DocumentRoot = conf['DocumentRoot']
    self.Mounts.append({ "Host" : self.DocumentRoot, "Guest" : self.DocumentRootMount, "Rights" : "rw" })

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
    if not isinstance(conf, list) :
      conf = [conf]

    for alias in conf:
      if not isinstance(alias, dict) :
        raise Exception('Alias definition is not a dictionary')
      if not 'Alias' in alias or not Param.isValidAlias(alias['Alias']) :
        raise Exception('Alias name is missing or invalid')
      if (
        not 'Path' in alias 
        or not (
          Param.isValidAbsPath(alias['Path']) 
          or Param.isValidRelPath(alias['Path']) and (
            Param.isValidDir(self.BaseDir + '/' + self.DocumentRoot + '/' + alias['Path']) 
            or Param.isValidFile(self.BaseDir + '/' + self.DocumentRoot + '/' + alias['Path'])
          )
        )
      ) :
        raise Exception('Alias path is missing or invalid')
    self.Aliases = conf

  def apply(self):
    super(EnvironmentApache, self).apply()
    self.apacheConfigure()
    self.apacheRestart()

  def apacheConfigure(self):
    vhFile = self.getApacheVHConfFile()
    vhFile.write(self.guestVHTemplate.format(
      ServerName = self.ServerName,
      ServerAlias = self.getServerAlias(),
      UID = '#' + str(self.UID) + ' #' + str(self.GID),
      DocumentRootMount = self.DocumentRootMount,
      AllowOverride = self.AllowOverride,
      Options = self.Options,
      Aliases = self.getAliases()
    ))
    vhFile.close()

  def apacheRestart(self):
    subprocess.call(['docker', 'exec', self.Name, 'supervisorctl', 'restart', 'apache2'])

  def getDockerOpts(self):
    dockerOpts = super(EnvironmentApache, self).getDockerOpts()
    dockerOpts += ' --cap-add=SYS_NICE --cap-add=DAC_READ_SEARCH'
    return dockerOpts

  def getApacheVHConfFile(self):
    vhFileName = self.DockerMntBase + '/' + self.Name + '/etc/apache2/sites-enabled/000-default.conf'
    vhFile = open(vhFileName, 'w')
    return vhFile

  def getAliases(self):
    aliases = ''
    for alias in self.Aliases:
      aliases += 'Alias ' + alias['Alias'] + ' ' + self.DocumentRootMount + '/' + alias['Path'] + '\n'
    return aliases

  guestVHTemplate = """
<VirtualHost *:80>
  ServerName {ServerName}
  DocumentRoot {DocumentRootMount}
  ServerAlias {ServerAlias}
  AssignUserID {UID}

  <Directory {DocumentRootMount}>
    Require all granted
    AllowOverride {AllowOverride}
    Options {Options}
  </Directory>

  {Aliases}
</VirtualHost>   
"""

class EnvironmentPHP(EnvironmentApache):
  def __init__(self, conf):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'http_php'
    super(EnvironmentPHP, self).__init__(conf)

class EnvironmentWSGI(EnvironmentApache):
  PythonPath      = None
  WSGIScriptAlias = None

  def __init__(self, conf):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'http_wsgi'
    super(EnvironmentWSGI, self).__init__(conf)

    if 'PythonPath' in conf :
      self.processPythonPath(conf['PythonPath'])
    else:
      self.PythonPath = [self.DocumentRoot]
    
    if not 'WSGIScriptAlias' in conf or not Param.isValidRelPath(conf['WSGIScriptAlias']) or not Param.isValidFile(self.BaseDir + '/' + self.DocumentRoot + '/' + conf['WSGIScriptAlias']) :
      raise Exception('WSGIScriptAlias is missing or invalid')
    self.WSGIScriptAlias = conf['WSGIScriptAlias']

  def processPythonPath(self, conf):
    if not isinstance(conf, list):
      if not isinstance(conf, basestring):
        raise Exception('PythonPath is not a string nor list')
      conf = [conf]

    for path in conf:
      if not isinstance(path, basestring) :
        raise Exception('PythonPath element is not a string')
      fullPath = self.BaseDir + '/' + self.DocumentRoot + '/' + path
      if not Param.isValidRelPath(path) or not (Param.isValidDir(fullPath) or Param.isValidFile(fullPath)) :
        raise Exception('PythonPath element is invalid')
    self.PythonPath = conf

  def apacheConfigure(self):
    vhFile = self.getApacheVHConfFile()
    vhFile.write(self.guestVHTemplate.format(
      ServerName = self.ServerName,
      ServerAlias = self.getServerAlias(),
      UID = '#' + str(self.UID),
      GID = '#' + str(self.GID),
      DocumentRootMount = self.DocumentRootMount,
      PythonPath = self.getPythonPath(),
      WSGIScriptAlias = self.DocumentRootMount + '/' + self.WSGIScriptAlias,
      AllowOverride = self.AllowOverride,
      Options = self.Options,
      Aliases = self.getAliases()
    ))
    vhFile.close()

    passwdFile = open(self.DockerMntBase + '/' + self.Name + '/etc/passwd', 'a')
    passwdFile.write('wsgi:x:' + str(self.UID) + ':' + str(self.GID) + '::' + self.DocumentRootMount + ':/bin/false')
    passwdFile.close()

    groupFile = open(self.DockerMntBase + '/' + self.Name + '/etc/group', 'a')
    groupFile.write('wsgi:x:' + str(self.GID) + ':')
    groupFile.close()

  def getPythonPath(self):
    pythonPath = ''
    for path in self.PythonPath:
      pythonPath += ':' + self.DocumentRootMount + '/' + path
    return pythonPath[1:]

  guestVHTemplate = """
<VirtualHost *:80>
  ServerName {ServerName}
  ServerAlias {ServerAlias}
  DocumentRoot {DocumentRootMount}

  WSGIDaemonProcess {ServerName} user={UID} group={GID} python-path={PythonPath}
  WSGIProcessGroup {ServerName}
  WSGIScriptAlias / {WSGIScriptAlias}

  <Directory {DocumentRootMount}>
    Require all granted
    AllowOverride {AllowOverride}
    Options {Options}
  </Directory>

  {Aliases}
</VirtualHost>
"""

class EnvironmentDrupal6(EnvironmentPHP):
  def __init__(self, conf):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'http_drupal6'
    super(EnvironmentDrupal6, self).__init__(conf)

#######################################

configuration = Configuration()
configuration.check()
configuration.apply()
