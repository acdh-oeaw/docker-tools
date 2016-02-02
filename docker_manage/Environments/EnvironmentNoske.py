from . import *

class EnvironmentNoSkE(EnvironmentHTTP, IEnvironment):
  DataDirMount       = '/var/lib/manatee/data'
  DataDir            = None
  RegistryDirMount   = '/var/lib/manatee/registry'
  RegistryDir        = None
  OptionsDirMount    = '/var/lib/bonito/options'
  OptionsDir         = None
  LogDirMount        = '/var/log/lighttpd'
  LogDir             = None
  BonitoDirMount     = '/usr/lib/python2.7/dist-packages/bonito'
  BonitoDir          = None
  Corplist           = []

  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'noske'
# Not supported right now
#    self.UserName = "www-data"
    self.runAsUser = True
    super(EnvironmentNoSkE, self).__init__(conf, owner)

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
    if (
        not 'RegistryDir' in conf
        or self.owner and (
          not Param.isValidRelPath(conf['RegistryDir'])
          or not Param.isValidDir(self.BaseDir + '/' + conf['RegistryDir'])
        )
      ) :
        raise Exception('RegistryDir is missing or invalid')
    self.RegistryDir = conf['RegistryDir']
    if (
        not 'OptionsDir' in conf
        or self.owner and (
          not Param.isValidRelPath(conf['OptionsDir'])
          or not Param.isValidDir(self.BaseDir + '/' + conf['OptionsDir'])
        )
      ) :
        raise Exception('OptionsDir is missing or invalid')
    self.OptionsDir = conf['OptionsDir']
    if 'BonitoDir' in conf:
      if (self.owner and (
            not Param.isValidRelPath(conf['BonitoDir'])
            or not Param.isValidDir(self.BaseDir + '/' + conf['BonitoDir'])
          )
        ) :
          raise Exception('BonitoDir is missing or invalid')
      self.BonitoDir = conf['BonitoDir']

    if 'Corplist' in conf :
      if not isinstance(conf['Corplist'], list) :
        if not isinstance(conf['Corplist'], basestring) :
          raise Exception('Corplist is not a string nor list')
        conf['Corplist'] = [conf['Corplist']]
      for corpora in conf['Corplist'] :
        if self.owner and (not Param.isValidDir(self.BaseDir + '/' + self.DataDir + '/' + corpora)) :
          raise Exception(corpora + ' corpora subdir is missing in the DataDir')
        if self.owner and (not Param.isValidFile(self.BaseDir + '/' + self.RegistryDir + '/' + corpora)) :
          raise Exception(corpora + ' corpora configuration file is missing in the RegistryDir')
        self.Corplist.append(corpora)
    if len(self.Corplist) == 0 :
      print '    Corplist is empty - bonito will not work.\n    Create a corpora, fill in the Corplist configuration property and rerun environment to make bonito work.'
    self.Mounts.append({ "Host" : self.DataDir, "Guest" : self.DataDirMount, "Rights" : "rw" })
    self.Mounts.append({ "Host" : self.LogDir, "Guest" : self.LogDirMount, "Rights" : "rw" })
    self.Mounts.append({ "Host" : self.RegistryDir, "Guest" : self.RegistryDirMount, "Rights" : "rw" })
    self.Mounts.append({ "Host" : self.OptionsDir, "Guest" : self.OptionsDirMount, "Rights" : "rw" })
    if (self.BonitoDir is not None): self.Mounts.append({ "Host" : self.BonitoDir, "Guest" : self.BonitoDirMount, "Rights" : "rw" })

  def runHooks(self, verbose):
    super(EnvironmentNoSkE, self).runHooks(verbose)

    if verbose :
      print '    Reconfiguring /var/www/bonito/run.cgi'
    replace1 = "s/^ *corplist = .*$/    corplist = [u'" + "', u'".join(self.Corplist) + "']/"
    replace2 = "s/^ *corpname = .*$/    corpname = u'" + (self.Corplist[0] if len(self.Corplist) > 0 else '') + "'/"
    self.runProcess(['docker', 'exec', '-u', 'root', self.Name, 'sed', '-i', '-e', replace1, '-e', replace2, '/var/www/bonito/run.cgi'], False, '', '/var/www/bonito/run.cgi update failed')
  #   subprocess.call(['docker', 'exec', self.Name, 'chown', 'user:user', '-R', '/usr/lib/python2.7/dist-packages/bonito'])
  #   distutils.dir_util.copy_tree(self.BaseDir + '/' + self.BonitoPath, self.DockerMntBase + '/' + self.Name + '/usr-lib-python2.7-dist-packages-bonito')
  #   subprocess.call(['docker', 'exec', self.Name, 'chown', 'user:user', '-R', '/usr/lib/python2.7/dist-packages/bonito'])
  #   subprocess.call(['docker', 'exec', self.Name, 'chmod', '+rX', '-R', '/usr/lib/python2.7/dist-packages/bonito'])
  #   subprocess.call(['docker', 'exec', self.Name, 'python', '-m', 'compileall', '/usr/lib/python2.7/dist-packages/bonito'])
  #
  #   subprocess.call(['docker', 'exec', self.Name, 'chown', 'user:user', '-R', '/var/lib/manatee/registry/'])
  #   distutils.dir_util.copy_tree(self.BaseDir + '/' + self.RegistryPath, self.DockerMntBase + '/' + self.Name + '/var-lib-manatee-registry/')
  #   subprocess.call(['docker', 'exec', self.Name, 'chown', 'user:user', '-R', '/var/lib/manatee/registry/'])
  #   subprocess.call(['docker', 'exec', self.Name, 'chmod', '+rX', '-R', '/var/lib/manatee/registry/'])

class EnvironmentNoSkE_patched(EnvironmentNoSkE, IEnvironment):
  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'noske_patched'
    self.runAsUser = True
    super(EnvironmentNoSkE_patched, self).__init__(conf, owner)