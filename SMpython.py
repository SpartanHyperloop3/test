

class GenericSM(object):
    """ Generic blueprint for state machine.
    Use as-is or subclass and redefine for more specific state machine.
    """
    
    def __init__(self, state):
        """ Initialize state machine with first state.
            
        Args:
            state (GenericState): hold state object to start machine
        """
        
        self.state = state
        self.info = {}

    def run(self):
        """ Run current state until next state is defined.
        Next state is held in self.state.nextState.
        """
        try:
            while(self.state.nextState is None):
                self.state.run(self.info)
            self.transition()
        except FatalException as e:
            # Emergency stop
            pass
        except SoftException as e:
            # Handle Exception and log info
            pass


    def getNextState(self):
        """ Return next state object. """
        return self.state.nextState

    def transition(self):
        """ Transition between states.
        Exit state, change state, enter state.
        """
        
        self.state.exit()
        self.state = self.getNextState()
        self.state.enter()


class GenericState(object):
    """ Generic blueprint for state in State Machine.
    Subclass this object and redefine methods for use in state machine.
    """
    
    def __init__(self, localInfo={}):
        """ Initialize new state.
        
        Note:
            Argument localInfo not required, default will be assignment of empty dict.
        
        Args:
            localInfo (dict): hold information specific to this instance of this state.
        """
        
        self.localInfo = localInfo
    
    def enter(self):
        """ Method called during transition TO this state. """
        pass
    
    def run(self, globalInfo):
        """ Method run while state machine is in specific state.
        
        Args:
            globalInfo (dict): holds persistent information that travels between states.
        
        Note:
            Assignment of self.nextState specifies next state for state machine.
        """
        pass

    def exit(self):
        """ Method called during transition FROM this state. """
        pass
		
class FatalException(Exception):
    """ Fatal Exception requires emergency stop.
        Subclass this exception for any errors that cannot be safetly handled. """
    pass

class SoftException(Exception):
    """ Soft Exception is logged and handled allowing continued operation.
        Subclass this exception for any errors that can be handled without halting operation. """
    pass
		
