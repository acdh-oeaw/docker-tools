import subprocess

from . import *

class EnvironmentHTTP(Environment, IEnvironment):
  MandatoryAccessForIPAddress = '193.170.85.88'

  ServerName    = None
  ServerAlias   = None
  HTTPS         = "true"
  Require       = "all granted"
  RequireForPaths = ""

  def __init__(self, conf, owner):
    self.ServerAlias = []
    super(EnvironmentHTTP, self).__init__(conf, owner)

    if 'ServerName' in conf and Param.isValidDomain(conf['ServerName']) :
      self.ServerName = conf['ServerName']

    if 'ServerAlias' in conf:
      self.processServerAlias(conf['ServerAlias'])

    if 'HTTPS' in conf :
      if not isinstance(conf['HTTPS'], basestring) or not ['true', 'false'].count(conf['HTTPS']) > 0 :
        raise Exception('HTTPS is not a string or has value other then true/false')
      self.HTTPS = conf['HTTPS'] == 'true'

    if 'Require' in conf :
      self.processRequire(conf['Require'])

    if 'RequireForPaths' in conf:
      if not isinstance(conf['RequireForPaths'], dict) :
        raise Exception('RequireForPaths is not a dictionary')
      self.processRequireForPaths(conf['RequireForPaths'])

  def processRequire(self, conf):
    if not isinstance(conf, list):
      if not isinstance(conf, basestring):
        raise Exception('Require is not a string nor list')
      conf = [conf]

    for ip in conf:
      if not Param.isValidRequireIP(ip) :
        raise Exception(ip + ' is not a valid Require entry')

    if self.MandatoryAccessForIPAddress is not None:
      conf.append(self.MandatoryAccessForIPAddress)
    self.Require = 'ip ' + ' '.join(conf)

  def processRequireForPaths(self, conf):
    if not isinstance(conf, list):
      conf = [conf]
    idx = 1
    for require in conf:
      pathre = require['PathRe']
      if not Param.isValidRe(pathre):
        raise Exception('RequireForPath ' + idx + ' is no valid RegExp')
      ipconf = require['IPs']
      if not isinstance(ipconf, list):
        if not isinstance(ipconf, basestring):
          raise Exception('RequireForPath ' + idx + ' is not a string nor list')
        ipconf = [ipconf]
      ips = []
      for ip in ipconf:
        if not Param.isValidRequireIP(ip):
          raise Exception('RequireForPath ' + str(idx) +
                          '/IP ' + str(len(ips) + 1) + ' is not a valid Require entry')
        ips.append(ip)
      if self.MandatoryAccessForIPAddress is not None:
        ips.append(self.MandatoryAccessForIPAddress)
      self.RequireForPaths = self.RequireForPaths + """
<ProxyMatch "%(pathre)s">
  Require %(requirestmt)s
</ProxyMatch>
""" % {"pathre": pathre, "requirestmt": 'ip ' + ' '.join(ips)}
      idx += 1


  def processServerAlias(self, conf):
    if not isinstance(conf, list):
      if not isinstance(conf, basestring):
        raise Exception('ServerAlias is not a string nor list')
      conf = [conf]

    for alias in conf:
      if not Param.isValidDomain(alias) :
        raise Exception(alias + ' is not a valid domain')
    self.ServerAlias = conf

  def check(self, duplDomains, duplPorts, duplNames, names):
    errors = super(EnvironmentHTTP, self).check(duplDomains, duplPorts, duplNames, names)
    if self.ServerName in duplDomains :
      errors.append('Domain ' + self.serverName + ' is duplicated')
    for alias in self.ServerAlias:
      if alias in duplDomains :
        errors.append('ServerAlias ' + alias + ' is duplicated')
    if len(errors) == 0 :
      self.ready = True
    else :
      self.ready = False
    return errors

  def runHooks(self, verbose):
    super(EnvironmentHTTP, self).runHooks(verbose)
    self.configureProxy(verbose)

  def configureProxy(self, verbose):
    if verbose :
      print '    Setting up reverse proxy'

    HTTPPort = self.getHTTPPort()
    websockets = ''
    for ws in HTTPPort['ws']:
      websockets += 'ProxyPass        ' + ws + ' ws://127.0.0.1:' + str(HTTPPort['Host']) + ws + '\n'
      websockets += 'ProxyPassReverse ' + ws + ' ws://127.0.0.1:' + str(HTTPPort['Host']) + ws + '\n'
    if self.Require == "all granted" and self.RequireForPaths != "":
      self.Require = ""
    proc = subprocess.Popen([
      'sudo', '-u', 'root', 'docker-register-proxy', 
      self.Name, 
      self.ServerName, 
      self.getServerAlias(), 
      str(HTTPPort['Host']), 
      websockets + self.RequireForPaths,
      self.HTTPS, 
      self.Require, 
      HTTPPort['Alias']
    ])
    out, err = proc.communicate()

  def getDockerOpts(self):
    dockerOpts = super(EnvironmentHTTP, self).getDockerOpts()
    return dockerOpts

  def getDomains(self):
    domains = []
    if not self.ServerName is None :
      domains.append(self.ServerName)
    domains += self.ServerAlias
    return domains

  def getServerAlias(self):
    serverAlias = self.ServerName
    for alias in self.ServerAlias:
      serverAlias += ' ' + alias
    return serverAlias

  def getHTTPPort(self):
    for port in self.Ports:
      if port['Type'] == 'HTTP' :
        return port
    raise Exception('No HTTP port')

