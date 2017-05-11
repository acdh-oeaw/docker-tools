from . import *

class EnvironmentKontext(EnvironmentWSGI3, IEnvironment):
  PythonPath      = ''
  WSGIScriptAlias = 'public/app.py'
  DataDirMount      = '/var/lib/manatee/data'
  RegistryDirMount  = '/var/lib/manatee/registry'
  LogDirMount = '/var/log/apache2'
  Corplist          = None

  def __init__(self, conf, owner):
    self.Corplist = []
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'kontext'
    super(EnvironmentWSGI3, self).__init__(conf, owner)

    if (
      not 'LogDir' in conf
      or self.owner and (
          not Param.isValidRelPath(conf['LogDir'])
          or not Param.isValidDir(self.BaseDir + '/' + conf['LogDir'])
        )
      ) :
        raise Exception('LogDir is missing or invalid')
    self.LogDir = conf['LogDir']

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
      not 'RegistryDir' in conf
      or self.owner and (
        not Param.isValidRelPath(conf['RegistryDir'])
        or not Param.isValidDir(self.BaseDir + '/' + conf['RegistryDir'])
      )
    ) :
      raise Exception('RegistryDir is missing or invalid')
    self.RegistryDir = conf['RegistryDir']

    if 'Corplist' in conf :
      if not isinstance(conf['Corplist'], list) :
        if not isinstance(conf['Corplist'], basestring) :
          raise Exception('Corplist is not a string nor list')
        conf['Corplist'] = [conf['Corplist']]
      for corpora in conf['Corplist'] :
        if self.owner and (not Param.isValidFile(self.BaseDir + '/' + self.RegistryDir + '/' + corpora)) :
          raise Exception(corpora + ' corpora configuration file is missing in the RegistryDir')
        self.Corplist.append(corpora)
    if len(self.Corplist) == 0 :
      print '    Corplist is empty - bonito will not work.\n    Create a corpus, fill in the Corplist configuration property and rerun environment to make bonito work.'

    self.Mounts.append({ "Host" : self.LogDir,     "Guest" : self.LogDirMount,     "Rights" : "rw" })
    self.Mounts.append({ "Host" : self.DataDir,     "Guest" : self.DataDirMount,     "Rights" : "rw" })
    self.Mounts.append({ "Host" : self.RegistryDir, "Guest" : self.RegistryDirMount, "Rights" : "rw" })

  def runHooks(self, verbose):
    super(EnvironmentKontext, self).runHooks(verbose)

    print "TODO: Register corpora -> corplist.xml?"

    if verbose :
      print '    Adjusting files ownership'
    self.runProcess(['docker', 'exec', '-u', 'root', self.Name, 'chown', '-R', self.UserName+":"+self.UserName, self.DocumentRootMount], False, '', 'ownership adjustment failed')

  guestVHTemplate = """
<VirtualHost *:80>
  ServerName {ServerName}
  ServerAlias {ServerAlias}
  DocumentRoot {DocumentRootMount}

  WSGIDaemonProcess {ServerName} user={UID} group={GID}
  WSGIProcessGroup {ServerName}
  WSGIApplicationGroup %{{GLOBAL}}
  Alias "/files" "/var/www/html/public/files"
  WSGIScriptAlias / {WSGIScriptAlias}
  WSGIPassAuthorization On

  <Directory {DocumentRootMount}>
    Require all granted
    AllowOverride {AllowOverride}
    Options {Options}
  </Directory>
  
  <Directory "/var/www/html/public">
    Options -Indexes -FollowSymLinks
    AllowOverride All
    Order allow,deny
    Allow from all
  </Directory>

  {Aliases}
</VirtualHost>
"""