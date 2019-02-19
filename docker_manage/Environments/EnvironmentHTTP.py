import subprocess
import os.path

from . import *

class EnvironmentHTTP(Environment, IEnvironment):
  MandatoryAccessForIPAddress = '193.170.85.88'

  ServerName   = None
  ServerAlias  = None
  HTTPS        = "true"
  Auth         = None
  AllowEncodedSlashes = "On"
  ProxyOptions = ""

  def __init__(self, conf, owner):
    self.ServerAlias = []
    self.Auth        = []
    super(EnvironmentHTTP, self).__init__(conf, owner)

    if 'ServerName' in conf and Param.isValidDomain(conf['ServerName']) :
      self.ServerName = conf['ServerName']

    if 'ServerAlias' in conf:
      self.processServerAlias(conf['ServerAlias'])

    if 'HTTPS' in conf :
      if not isinstance(conf['HTTPS'], basestring) or not ['true', 'false', 'both'].count(conf['HTTPS']) > 0 :
        raise Exception('HTTPS is not a string or has value other then true/false/both')
      self.HTTPS = conf['HTTPS']

    if 'Auth' in conf and self.owner:
      self.processAuth(conf['Auth'])

  def processAuth(self, conf):
    if not isinstance(conf, list) :
      conf = [conf]
    n = 1
    htpasswdFiles = []
    for loc in conf:
      if not isinstance(loc, dict) :
        raise Exception('Auth %d is not a dictionary' % n)
      if 'PathRe' not in loc :
        loc['PathRe'] = ''
      if not Param.isValidRe(loc['PathRe']) :
        raise Exception('Auth %d PathRe is not a valid regular expression' % n)
      require = htpasswd = ''
      if 'IPs' in loc :
        ips = loc['IPs']
        if not isinstance(ips, list) :
          ips = [ips]
        m = 1
        for ip in ips:
          if not Param.isValidRequireIP(ip) :
            raise Exception('Auth %d IP %d is not a valid Require IP' % (n, m))
          m += 1
        if self.MandatoryAccessForIPAddress is not None :
          ips.append(self.MandatoryAccessForIPAddress)
        require = 'Require ip ' + ' '.join(ips)
      if 'htpasswdFile' in loc :
        htFile = os.path.join(self.BaseDir, loc['htpasswdFile'])
        if not Param.isValidFile(htFile) :
          raise Exception('Auth %d htpasswdFile is invalid' % n)
        if Param.getSecurityContext(htFile) != 'httpd_config_t' :
          raise Exception('Auth %d htpasswdFile has wrong security context - execute "chcon -t httpd_config_t %s"' % (n, htFile))
        htpasswd = """
  AuthType basic
  AuthName "%s"
  AuthUserFile %s
  Require valid-user
""" % (self.Name, htFile)
      if not 'htpasswdFile' in loc and not 'IPs' in loc :
        raise Exception('Auth %d IPs or htpasswdFile has to be specified' % n)
      
      auth = """
<ProxyMatch "%s">
  %s
</ProxyMatch>
""" % (loc['PathRe'], require + htpasswd)
      self.Auth.append(auth)

      n += 1

  def processServerAlias(self, conf):
    if not isinstance(conf, list):
      if not isinstance(conf, basestring):
        raise Exception('ServerAlias is not a string nor list')
      conf = [conf]

    for alias in conf:
      if alias == self.ServerName:
        continue
      if not Param.isValidDomain(alias) :
        raise Exception(alias + ' is not a valid domain')
    self.ServerAlias = conf

  def check(self, duplDomains, duplPorts, duplNames, names):
    errors = super(EnvironmentHTTP, self).check(duplDomains, duplPorts, duplNames, names)
    if self.ServerName in duplDomains :
      errors.append('Domain ' + self.ServerName + ' is duplicated')
    for alias in self.ServerAlias:
      if alias == self.ServerName:
        continue
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
    HTTPPort = self.getHTTPPort()
    websockets = ''
    proto = 'ws' if self.HTTPS == 'false' else 'wss'
    for ws in HTTPPort['ws']:
      websockets += 'ProxyPass        ' + ws + ' ' + proto + '://127.0.0.1:' + str(HTTPPort['Host']) + ws + '\n'
      websockets += 'ProxyPassReverse ' + ws + ' ' + proto + '://127.0.0.1:' + str(HTTPPort['Host']) + ws + '\n'
    cmd = [
      'sudo', '-u', 'root', 'docker-register-proxy',
      self.Name,
      self.ServerName,
      self.getServerAlias(),
      str(HTTPPort['Host']),
      websockets + ''.join(self.Auth),
      self.HTTPS,
      HTTPPort['Alias'],
      self.AllowEncodedSlashes,
      self.ProxyOptions
    ]
    if verbose :
      print('    Setting up reverse proxy')
      print(' '.join(cmd))

    proc = subprocess.Popen(cmd)
    out, err = proc.communicate()

  def getDockerOpts(self):
    dockerOpts = super(EnvironmentHTTP, self).getDockerOpts()
    return dockerOpts

  def getDomains(self):
    domains = []
    if not self.ServerName is None and self.ServerName not in self.ServerAlias:
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


