from . import *

class Environmentelasticsearch(EnvironmentHTTP, IEnvironment):
  DataDirMount       = '/usr/share/elasticsearch/data'
  DataDir            = None
  LogDirMount        = '/usr/share/elasticsearch/log'
  LogDir             = None
  ConfDirMount       = '/usr/share/elasticsearch/config'
  ConfDir            = None

  def __init__(self, conf, owner):
    self.runAsUser = True
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'elasticsearch'
    super(Environmentelasticsearch, self).__init__(conf, owner)
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
    if 'ConfDir' in conf:
      if (self.owner and (
            not Param.isValidRelPath(conf['ConfigDir'])
            or not Param.isValidDir(self.BaseDir + '/' + conf['ConfigDir'])
          )
        ) :
          raise Exception('ConfigDir is missing or invalid')
    self.ConfDir = conf['ConfigDir']
    self.Mounts.append({ "Host" : self.DataDir, "Guest" : self.DataDirMount, "Rights" : "rw" })
    self.Mounts.append({ "Host" : self.LogDir, "Guest" : self.LogDirMount, "Rights" : "rw" })
    self.Mounts.append({ "Host" : self.ConfDir, "Guest" : self.ConfDirMount, "Rights" : "rw" })

    try:
      self.getHTTPPort()
    except:
      self.Ports.append({ "Host" : HTTPReverseProxy.getPort(), "Guest" : 9200 , "Type" : "HTTP", "ws" : [], "Alias" : ""})