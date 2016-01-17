import abc

class IEnvironment():
  """An interface for environment type classes.

  In general you should derive (directly or indirectly) your environment type
  class from the Environment class because it provides a lot of useful defaults
  (especially implements the whole IEnvironment iterface).
  Anyway, if you really want to write your environment type class from scratch, 
  it will be sufficient if your class implements the IEnvironment interface.
  """
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def __init__(self, conf, owner): 
    """Environment constructor

    If you derive your class from other, please remember to call a parent 
    constructor!

    Args:
      conf (dict): Dictionary with a configuration to process
      owner (boolean): Indicates if you have rights to access environment files.
        If you don't, you shouldn't check e.g. for the existence of paths in 
        the host (because such checks will always fail).
    """
    pass
  
  @abc.abstractmethod
  def check(self, duplDomains, duplPorts, duplNames, names): 
    """Cheks environment for conflicts and reports them.

    For (at least) 99% of cases class Environment provides a right
    implementation for this method, so please just derive 

    For (at least) 99% of cases class Environment provides a right 
    implementation of this method, so please just derive (directly or 
    indirectly) your class from the Environment one.

    If you really want to implement it on yourself, please remember to set the
    ``ready`` object property to ``False`` if the check will fail.

    Args:
      duplDomains (list): List of duplicated domains.
      duplPorts (list): List of duplicated host ports.
      duplNames (list): List of duplicated environment names.
      names (list): List of all defined environment names. 
        Useful to check e.g. if all links point to existing environments.
    """
    pass
  
  @abc.abstractmethod
  def buildImage(self, verbose): 
    """Runs 'docker build'
    
    For (at least) 99% of cases class Environment provides a right 
    implementation of this method, so please just derive (directly or 
    indirectly) your class from the Environment one.

    Args:
      verbose (boolean): If method should produce a verbose output.
    """
    pass
  
  @abc.abstractmethod
  def runContainer(self, verbose): 
    """Runs 'docker run'

    For (at least) 99% of cases class Environment provides a right 
    implementation of this method, so please just derive (directly or 
    indirectly) your class from the Environment one.
    Implementation profided in the Environment class relies on the
    ``getDockerOpts()`` method to obtain all parameters to be passed to 
    "docker run", so if you need to adjust these parameters, override
    ``getDockerOpts()`` rather the ``runContainer()``.

    If you really want to implement it yourself, please remember to:
    - check, if the ``ready`` property is set to ``True`` before spawning 
      the container;
    - remove a previous instance of a container (with its volumes);
    - run ``docker-mount-volumes containerName`` after container creation.

    Args:
      verbose (boolean): If method should produce a verbose output.
    """
    pass
  
  @abc.abstractmethod
  def runHooks(self, verbose):
    """Adjusts container after it was created.

    A docker image provides all the stuff which is common for every instance
    of an environment type but typically there are also many things which
    should be "personalized" for every instance (user and group to run
    application in guest, ServerName in Apache config in guest, etc.).
    This method provides a way to do that. 
    It is always invoked just after ``runContainer()``

    If you derive your class form other, please check carefully which actions
    are taken in parent clasees ``runHooks()`` methods before adding new acions
    on your own.

    Args:
      verbose (boolean): If method should produce a verbose output.
    """ 
    pass
