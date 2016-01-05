class Param(object):
  @staticmethod
  def isValidAbsPath(p):
    return not re.search('/[.][.]/', p) and re.search('^/[-_.a-zA-Z0-9]+$', p)

  @staticmethod
  def isValidRelPath(p):
    return (not (re.search('^/', p) or re.search('^[.][.]/', p) or re.search('/[.][.]/', p))) and re.search('^[-/_.a-zA-Z0-9]+$', p)

  @staticmethod
  def isValidFile(p):
    return os.path.isfile(p)

  @staticmethod
  def isValidDir(p):
    return os.path.isdir(p)

  @staticmethod
  def isValidName(p):
    return re.search('^[-_.a-zA-Z0-9]+$', p)

  @staticmethod
  def isValidNumber(p):
    return re.search('^[0-9]+$', str(p))

  @staticmethod
  def isValidDomain(p):
    return re.search('^((([a-z0-9][-a-z0-9]*[a-z0-9])|([a-z0-9]+))[.]?)+$', str(p))

  @staticmethod
  def isValidAlias(p):
    return re.search('^/[-_.a-zA-Z0-9/]+$', str(p))

  @staticmethod
  def isValidHostName(p):
    return re.search('^([-a-zA-Z0-9][.]?)+$', p)

  @staticmethod
  def isValidIP(p):
    return re.search('^[0-9]?[0-9]?[0-9][.][0-9]?[0-9]?[0-9][.][0-9]?[0-9]?[0-9][.][0-9]?[0-9]?[0-9]$', str(p))

  @staticmethod
  def isValidRequireIP(p):
    return (
      re.search('^[0-9]?[0-9]?[0-9]([.][0-9]?[0-9]?[0-9])?([.][0-9]?[0-9]?[0-9])?([.][0-9]?[0-9]?[0-9])?$', str(p))
      or re.search('^[0-9]?[0-9]?[0-9][.][0-9]?[0-9]?[0-9][.][0-9]?[0-9]?[0-9][.][0-9]?[0-9]?[0-9]/(3[0-2]|[12][0-9]|[0-9])$', str(p))
    )

  @staticmethod
  def isValidParamsList(p):
    if not isinstance(p, list) :
      return False
    for i in p:
      if not isinstance(i, basestring) :
        return False
    return True

  @staticmethod
  def isValidVarName(p):
    return re.search('^[_a-zA-Z][_a-zA-Z0-9]*$', str(p))
