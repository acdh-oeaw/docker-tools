from . import *

class EnvironmentBaseX(EnvironmentHTTP, IEnvironment):
  DataDirMount       = '/data'
  DataDir            = None
  BaseXDirMount       = '/opt/basex'
  BaseXDir            = None
  TmpDirMount        = '/tmp'
  TmpDir             = None

  def __init__(self, conf, owner):
    self.runAsUser = True
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'basex'
    super(EnvironmentBaseX, self).__init__(conf, owner)
    if (
        not 'BaseXDir' in conf
        or self.owner and (
          not Param.isValidRelPath(conf['BaseXDir'])
          or not Param.isValidDir(self.BaseDir + '/' + conf['BaseXDir'])
        )
      ) :
        raise Exception('BaseXDir is missing or invalid')
    self.BaseXDir = conf['BaseXDir']
    if (
        not 'TmpDir' in conf
        or self.owner and (
          not Param.isValidRelPath(conf['TmpDir'])
          or not Param.isValidDir(self.BaseDir + '/' + conf['TmpDir'])
        )
      ) :
        raise Exception('TmpDir is missing or invalid')
    self.TmpDir = conf['TmpDir']
    self.Mounts.append({ "Host" : self.BaseXDir, "Guest" : self.BaseXDirMount, "Rights" : "rw" })
    self.Mounts.append({ "Host" : self.TmpDir, "Guest" : self.TmpDirMount, "Rights" : "rw" })

class EnvironmentRHELBaseX(EnvironmentBaseX, IEnvironment):

  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = self.DistrPrefix + 'rhel_basex'
    super(EnvironmentRHELBaseX, self).__init__(conf, owner)
