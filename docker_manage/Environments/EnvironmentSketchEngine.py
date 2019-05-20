from . import *

class EnvironmentSketchEngine(EnvironmentSkeBase, IEnvironment):
  UserName          = 'apache'
  DataDirMount      = '/corpora/data'
  BonitoDirMount    = '/var/lib/ske'
  RegistryDirMount  = '/corpora/registry'
  BonitoLibDirMount = '/usr/lib/python2.7/site-packages/bonito'

  def __init__(self, conf, owner):
    if not 'DockerfileDir' in conf :
      conf['DockerfileDir'] = 'sketch-engine'
    super(EnvironmentSketchEngine, self).__init__(conf, owner)

    try:
      self.getHTTPPort()
    except:
      self.Ports.append({ "Host" : HTTPReverseProxy.getPort(), "Guest" : 80 , "Type" : "HTTP", "ws" : False, "wss" : False, "Alias" : ""})

    self.Mounts.append({ "Host" : self.RegistryDir, "Guest" : "/var/lib/ske/registry", "Rights" : "rw"})

