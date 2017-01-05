from . import *

class EnvironmentNoSkE(EnvironmentSkeBase, IEnvironment):
  DockerfileDir     = 'noske'
  UserName          = 'www-data'
  LogDir            = ''
  LogDirMount       = '/var/log/lighttpd'
  DataDirMount      = '/var/lib/manatee/data'
  BonitoDirMount    = '/var/lib/bonito'
  RegistryDirMount  = '/var/lib/manatee/registry'
  BonitoLibDirMount = '/usr/lib/python2.7/dist-packages/bonito'
  runAsUser         = True

  def __init__(self, conf, owner):
    if not 'DockerfileDir' in conf :
      conf['DockerfileDir'] = 'noske'
    super(EnvironmentNoSkE, self).__init__(conf, owner)

    if (
      not 'LogDir' in conf
      or self.owner and (
          not Param.isValidRelPath(conf['LogDir'])
          or not Param.isValidDir(self.BaseDir + '/' + conf['LogDir'])
        )
      ) :
        raise Exception('LogDir is missing or invalid')
    self.LogDir = conf['LogDir']
    self.Mounts.append({ "Host" : self.LogDir,     "Guest" : self.LogDirMount,     "Rights" : "rw" })

    try:
      self.getHTTPPort()
    except:
      self.Ports.append({ "Host" : HTTPReverseProxy.getPort(), "Guest" : 8080 , "Type" : "HTTP", "ws" : [], "Alias" : ""})

class EnvironmentNoSkE_patched(EnvironmentNoSkE, IEnvironment):
  def __init__(self, conf, owner):
    if not 'DockerfileDir' in conf :
      conf['DockerfileDir'] = 'noske_patched'
    super(EnvironmentNoSkE_patched, self).__init__(conf, owner)
