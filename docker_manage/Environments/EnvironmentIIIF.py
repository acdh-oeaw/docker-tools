from . import *

class EnvironmentIIIF(EnvironmentHTTP, IEnvironment):
  DropzoneDirMount = '/dropzone/'
  DropzoneDir      = None
  DataDirMount     = '/data/'
  DataDir          = None
  LogDirMount      = '/var/log'
  LogDir           = None

  def __init__(self, conf, owner):
    self.runAsUser = True
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'iiif'
    super(EnvironmentIIIF, self).__init__(conf, owner)
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
    self.DataDir = conf['LogDir']
    self.Mounts.append({ "Host" : self.DropzoneDir, "Guest" : self.DropzoneDirMount, "Rights" : "rw" })
    self.Mounts.append({ "Host" : self.DataDir, "Guest" : self.DataDirMount, "Rights" : "rw" })
    self.Mounts.append({ "Host" : self.LogDir, "Guest" : self.LogDirMount, "Rights" : "rw" })


