from . import *
import os

class EnvironmentWSGI3(EnvironmentApache, IEnvironment):
  PythonPath      = None
  WSGIScriptAlias = None
  LogDirMount = '/var/log/apache2'

  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'http_wsgi3'
    super(EnvironmentWSGI3, self).__init__(conf, owner)

    self.processLogDir(conf, False)

    if 'PythonPath' in conf :
      self.processPythonPath(conf['PythonPath'])
    else:
      self.PythonPath = [self.DocumentRoot]
    
    if (
      not 'WSGIScriptAlias' in conf 
      or self.owner and (
        not Param.isValidRelPath(conf['WSGIScriptAlias']) 
        or not Param.isValidFile(self.BaseDir + '/' + self.DocumentRoot + '/' + conf['WSGIScriptAlias']) 
      )
    ) :
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
      if self.owner and (not Param.isValidRelPath(path) or not (Param.isValidDir(fullPath) or Param.isValidFile(fullPath))) :
        raise Exception('PythonPath element is invalid')
    self.PythonPath = conf

  def apacheConfigure(self):
    tmpFile = '/tmp/' + self.Name
    with open(tmpFile, 'w') as vhFile:
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
    self.runProcess(['docker', 'cp', tmpFile, self.Name + ':/etc/apache2/sites-enabled/000-default.conf'], False, '', 'Apache config update in guest failed')
    os.remove(tmpFile)

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
  WSGIPassAuthorization On

  <Directory {DocumentRootMount}>
    Require all granted
    AllowOverride {AllowOverride}
    Options {Options}
  </Directory>

  {Aliases}
</VirtualHost>
"""

