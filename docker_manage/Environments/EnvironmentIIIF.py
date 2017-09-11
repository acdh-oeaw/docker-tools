from . import *

class EnvironmentIIIF(EnvironmentApache, IEnvironment):
  skipDocumentRoot   = True 
  DocumentRootMount  = '/usr/share/cgi-bin'
  DocumentRoot       = None
  DockerfileDir = 'iiif'
  DropzoneDirMount = '/dropzone/'
  DropzoneDir      = None
  DataDirMount     = '/data/'
  DataDir          = None
  LogDirMount      = '/opt/iiifserver/logs'
  LogDir           = None

  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'iiif'
    super(EnvironmentIIIF, self).__init__(conf, owner)
    try:
      self.getHTTPPort()
    except:
      self.Ports.append({ "Host" : HTTPReverseProxy.getPort(), "Guest" : 80 , "Type" : "HTTP", "ws" : [], "Alias" : ""})

    if (
        not 'DropzoneDir' in conf
        or self.owner and (
          not Param.isValidRelPath(conf['DropzoneDir'])
          or not Param.isValidDir(self.BaseDir + '/' + conf['DropzoneDir'])
        )
      ) :
        raise Exception('DropzoneDir is missing or invalid')
    self.DropzoneDir = conf['DropzoneDir']
    if (
        not 'DataDir' in conf
        or self.owner and (
          not Param.isValidRelPath(conf['DataDir'])
          or not Param.isValidDir(self.BaseDir + '/' + conf['DataDir'])
        )
      ) :
        raise Exception('DataDir is missing or invalid')
    self.DataDir = conf['DataDir']
    if (
        not 'LogDir' in conf
        or self.owner and (
          not Param.isValidRelPath(conf['LogDir'])
          or not Param.isValidDir(self.BaseDir + '/' + conf['LogDir'])
        )
      ) :
        raise Exception('LogDir is missing or invalid')
    self.LogDir = conf['LogDir']
    
    self.Mounts.append({ "Host" : self.DropzoneDir, "Guest" : self.DropzoneDirMount, "Rights" : "rw" })
    self.Mounts.append({ "Host" : self.DataDir, "Guest" : self.DataDirMount, "Rights" : "rw" })
    self.Mounts.append({ "Host" : self.LogDir, "Guest" : self.LogDirMount, "Rights" : "rw" })

  def apacheConfigure(self):
    tmpFile = '/tmp/' + self.Name
    with open(tmpFile, 'w') as vhFile:
      vhFile.write(self.guestVHTemplate.format(
        ServerName = self.ServerName,
        ServerAlias = self.getServerAlias(),
        UID = '#' + str(self.UID),
        GID = '#' + str(self.GID),
        DocumentRootMount = self.DocumentRootMount,
        AllowOverride = self.AllowOverride,
        Options = self.Options,
        Aliases = self.getAliases(),
        FastCgiExternalServer = self.FastCgiExternalServer(),
        ImitateHTTPS = self.imitateHTTPSTemplate if self.ImitateHTTPS == 'true' else ''
      ))
    self.runProcess(['docker', 'cp', tmpFile, self.Name + ':/etc/apache2/sites-enabled/000-default.conf'], False, '', 'Apache config update in guest failed')
    os.remove(tmpFile)

  def apacheRestart(self, verbose):
    self.runProcess(['docker', 'exec', self.Name, 'apachectl', 'graceful'], verbose, '', 'Apache graceful restart failed')
    self.runProcess(['docker', 'exec', self.Name, 'supervisorctl', 'restart', 'apache2'], verbose, '', 'Apache restart failed')

  def getDockerOpts(self):
    dockerOpts = super(EnvironmentApache, self).getDockerOpts()
    dockerOpts += ['--cap-add=SYS_NICE', '--cap-add=DAC_READ_SEARCH']
    return dockerOpts

  def getAddHandler(self):
    return 'fastcgi-script fcg fcgi fpl'  

  def getAliases(self):
    aliases = ''
    for alias in self.Aliases:
      aliases += 'Alias ' + alias['Alias'] + ' ' + self.DocumentRootMount + '/' + alias['Path'] + '\n'
    return aliases

  def getFastCgiExternalServer(self):
    return '/usr/share/cgi-bin/iiifserver.fcgi -host 127.0.0.1:9000 -idle-timeout 3600'  

  def getGuestHomeDir(self):
    return '/var/www/html'

  imitateHTTPSTemplate = """
  SetEnv HTTPS on
  SetEnv REQUEST_SCHEME https
  SetEnv protossl s
"""

  guestVHTemplate = """
<VirtualHost *:80>
  ServerName {ServerName}
  DocumentRoot {DocumentRootMount}
  ServerAlias {ServerAlias}
  AssignUserID {UID} {GID}
  FastCgiExternalServer {FastCgiExternalServer}

  <Directory {DocumentRootMount}>
    Require all granted
    AllowOverride {AllowOverride}
    Options {Options}
  </Directory>
   
  {AddHandler} 
  {Aliases}
  {ImitateHTTPS}
</VirtualHost>   
"""  


