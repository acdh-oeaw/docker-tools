import os
from . import *

class EnvironmentSkeBase(EnvironmentHTTP, IEnvironment):
  """Base class for all SketchEngine/noske and maybe also Kontext environment
  types providing common stuff used in all of them.
  """

  DataDir           = ''
  RegistryDir       = ''
  BonitoDir         = ''
  BonitoLibDir      = None
  DataDirMount      = None
  BonitoDirMount    = None
  RegistryDirMount  = None
  BonitoLibDirMount = None
  Corplist          = None

  def __init__(self, conf, owner):
    self.Corplist = []
    super(EnvironmentSkeBase, self).__init__(conf, owner)

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
      'BonitoDir' not in conf
      or self.owner and (
           not isinstance(conf['BonitoDir'], basestring) 
        or not Param.isValidRelPath(conf['BonitoDir']) 
        or not Param.isValidDir(self.BaseDir + '/' + conf['BonitoDir']) 
      )
    ) :
      raise Exception('BonitoDir is missing or invalid')
    self.BonitoDir = conf['BonitoDir']

    if (
      not 'RegistryDir' in conf
      or self.owner and (
        not Param.isValidRelPath(conf['RegistryDir'])
        or not Param.isValidDir(self.BaseDir + '/' + conf['RegistryDir'])
      )
    ) :
      raise Exception('RegistryDir is missing or invalid')
    self.RegistryDir = conf['RegistryDir']

    if 'BonitoLibDir' in conf:
      if (
        self.owner and (
          not Param.isValidRelPath(conf['BonitoLibDir'])
          or not Param.isValidDir(self.BaseDir + '/' + conf['BonitoLibDir'])
        )
      ) :
        raise Exception('BonitoLibDir is invalid')
      self.BonitoLibDir = conf['BonitoLibDir']

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

    self.Mounts.append({ "Host" : self.DataDir,     "Guest" : self.DataDirMount,     "Rights" : "rw" })
    self.Mounts.append({ "Host" : self.BonitoDir,   "Guest" : self.BonitoDirMount,   "Rights" : "rw" })
    self.Mounts.append({ "Host" : self.RegistryDir, "Guest" : self.RegistryDirMount, "Rights" : "rw" })
    if (self.BonitoLibDir is not None): 
      self.Mounts.append({ "Host" : self.BonitoLibDir, "Guest" : self.BonitoLibDirMount, "Rights" : "rw" })

  def runHooks(self, verbose):
    super(EnvironmentSkeBase, self).runHooks(verbose)

    if verbose :
      print '    Reconfiguring /var/www/bonito/run.cgi'
    replace1 = "s/^ *corplist = .*$/    corplist = [u'" + "', u'".join(self.Corplist) + "']/"
    replace2 = "s/^ *corpname = .*$/    corpname = u'" + (self.Corplist[0] if len(self.Corplist) > 0 else '') + "'/"
    self.runProcess(['docker', 'exec', '-u', 'root', self.Name, 'sed', '-i', '-e', replace1, '-e', replace2, '/var/www/bonito/run.cgi'], False, '', '/var/www/bonito/run.cgi update failed')

    if verbose :
      print '    Preparing BonitoDir'
    for directory in ['cache', 'jobs', 'options', 'subcorp']:
      if not os.path.isdir(self.BaseDir + '/' + self.BonitoDir + '/' + directory) :
        os.mkdir(self.BaseDir + '/' + self.BonitoDir + '/' + directory)
    if not os.path.isfile(self.BaseDir + '/' + self.BonitoDir + '/htpasswd') :
      os.mknod(self.BaseDir + '/' + self.BonitoDir + '/htpasswd')

    # we are using system's apache/www-user account with adjusted UID, thus we must also adjust files ownership because here and now they are owned by an orphaned UID
    if verbose :
      print '    Adjusting files ownership'
    self.runProcess(['docker', 'exec', '-u', 'root', self.Name, 'chown', '-R', self.UserName, self.BonitoDirMount, self.BonitoLibDirMount], False, '', 'ownership adjustment failed')
