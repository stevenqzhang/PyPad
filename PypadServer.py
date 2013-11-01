"""
PypadServer.py

INTRODUCTION
Contains the Server, PypadData, and 
PypadServer class (isa Server and PypadData object).

PYPADDATA CLASS
The PypadData class contains all data-related attributes. All of these attributes 
are non-Remote Object attributes.

SERVER CLASS
The Server class contains attributes associated with client registration, 
notification, and tracking. All of these attributes are remote object related 
attributes, so Server is a subclass of the RemoteObject class (a Pyro-wrapper).

PYPADSERVER CLASS
PypadServer is a subclass of the Server and PypadData classes.

A PypadServer instance stores the text and drawing data. 
It keeps track of all of its client objects.
Every time a client's state changes, it receives a notification from the client 
of that change. 

The PypadServer instance then notifies other clients of these changes.

DESIGN PATTERNS USED
The Server class is the subject in the subject-observer design pattern.
The PypadData class is the model in the model-view-controller design pattern.

AUTHOR
Steven Zhang

OTHER AUTHORS
Jason Poon worked on the PypadData with regards to history
Reyner Crosby contributed to data storage of drawings

CREDITS
Pyro package taken from pyro.sourceforge.net
RemoteObjects Library: Allen Downey
Subject-Observer template: Mark Sheldon

CHANGELOG
11/26/2010
Cleaned up code and comments. 
Added verbose output which hides detailed certain status updates.
-Steven

4/28/2010
Integrated drawing updates with PypadServer's methods by abstracting 
setState and getState to both text and drawings 
-Steven

4/27/2010
Integrate drawing into the PypadData object using getters and setters for
drawing object
-Jason & Reyner

4/27/2010
Added revision history data object and methods to PypadData
-Jason

4/24/2010
In order to address the bug of server freezing when people type at the same time
A thread was added for each client notification. This makes it slower, 
but avoids any bugs
-Steven

4/23/2010
Reworked PypadServer class using subject-observer design pattern. 
Added server-side notification of clients.
Switched from using the Pyro remote objects library to the RemoteObject Pyro 
wrapper library.
-Steven

4/17/2010 
Got PypadServer to work over the network: 
the nameserver host must be connected via ethernet
-Steven

4/9/2010 
Created basic PypadServer class, using client-side updating of text
Got PypadServer to work on localhost
-Steven

4/6/2010
Added basic structure of PypadData class
-Jason, Reyner, Steven
"""



from RemoteObject import *
import sys
from copy import *
import random
from threading import Thread
from time import sleep

class Server(RemoteObject):
    """
    A server is an object that keeps track of the clients
    watching it.  When the state of a server changes, it
    notifies each client on the list.
    
    It inherits RemoteObject to communicate using the Pyro protocol
    
    The registration and basic notification methods are 
    from subject-observer template from the software design website: 
    http://ece.olin.edu/sd/current/code/Subject.py
    
    Steven wrote the multithreading code in the notification methods
    """

    def __init__(self, name):
        """
        Constructor for Server class
        
        Args:
            name: a string that becomes the name root on all Pypad windows.
        
        """
    
        RemoteObject.__init__(self, name)
        self.clients = []
        
        # prevents name clashes if multiple PypadServer instances are running
        # on same name server
        self.clientAccumulator = random.randint(0, 1000);   
    def notifyClientThread(self, clientName, type):
        """
        Thread called by notifyClients method. Each of these threads notifies one 
        client of change in data.         
        
        Args:
            clientName: string; name of the client to notify
            type: string; type of data to update 
                value can be either 'drawing' or 'text'
        
        History
            Added 4/24/10 by Steven
        """
        try:
            print 'Notifying', clientName
            
            ns = NameServer()
            proxy = ns.get_proxy(clientName)
            proxy.notify(type)
            print 'Finished notifying'
        #=======================================================================
        # # Steven commented these lines because they caught NamingErrors
        # # which the next except block should do.
        # # except Exception, x:
        #   # this clause should catch errors that occur
        #   # in the client code.
        #   # print 'Error with Client' + str(client)
        #   # print ''.join(Pyro.util.getPyroTraceback(x))
        #=======================================================================
        except:
            # this clause should catch Pyro NamingErrors,
            # which occur when an client dies.
            self.unregister(clientName)
            
    def notifyClients(self, sendingClient, type):
        """
        Notify all registered clients when the state of
        the Server changes, except sendingClient (otherwise infinite loop
        occurs)
        
        Args:
            sendingClient: string; name of client whose state changed
            type: 'drawing' or 'text'
            
        History
            This method was from Subject.py template
            
            4/24/10 
            Modified heavily by Steven.
            Split into two methods for multithreading purposes
        """
        t = list()      #lists of notification threads
        
        if (self.VERBOSE):
            print "------------"
            print "list of clients:" + str(self.clients)
        
        i = 0   #thread number
        for clientName in copy(self.clients): # copy to permit mods to clients
            if clientName != sendingClient:
                if (self.VERBOSE): print "notifying using thread " + str(i)
                t.append(Thread(target = self.notifyClientThread,
                                args = [clientName, type]))
                if (self.VERBOSE): print "Created thread"
                t[i].start()
                if (self.VERBOSE): print "Started thread" + str(i)
                i += 1

    # the following methods are intended to be invoked remotely
    def register(self):
        """
        Register a new client to server (invoked by the client)
        
        History
            This method was part of Subject.py template
            
            4/24/10
            Steven modified the clientName generator so that clients didn't have 
            entirely random ids. The first id is random, the the rest are 
            sequential
        """
        id = self.clientAccumulator
        self.clientAccumulator += 1
        clientName = self.name + '_client_' + str(id)
        self.clients.append(clientName)
         
        print "----------------"
        print 'Registered ' + clientName
        if (self.VERBOSE): print 'List of all clients:' + str(self.clients)
            
        return clientName, id
    
    def unregister(self, clientName):
        """
        Steven added this method to unregister clients when they disconnect.
        """
        self.clients.remove(clientName)
        print 'Unregistered ' + clientName

class PypadData():
    """
    PypadData contains all the attributes (along with setters and getters)
    that correspond to the data being stored.
    
    Authorship:
        Text methods/attributes added by Steven
        Drawing methods/attributes added by Reyner
        History methods/attributes added by Jason
    """
    def __init__(self, string='hello'):
        """
        Constructor for PypadData
        
        Args:
            string: initial text to be stored in the PypadServer object
        """
        self.history = list()   #history is a list of all past text strings
        self.history.append(string)
        
        # self.drawing is the remote attribute that stores the drawings
        self.drawing = []
        
    # The following methods should be invoked remotely by client or the update
    # loops in PypadClient.py
    def getText(self):
        """
        Getter for the text data
        """
        return self.history[len(self.history)-1]        
    def changeText(self,string):
        """
        Setter for the text data on the PypadServer object
        
        Args:
            string: text data to be set
        """
        self.history.append(string)
    def getHistory(self, num):
        """
        Returns the revision that is num revisions before the
        current revision
        
        Args: 
            num: int;
        
        History
            Added by Steven 4/17/2010
            Revised by Jason 4/23/2010
        """
        lenHist = len(self.history)
        
        if num <= lenHist:
            return self.history[num-1]
        else:
            print "You're trying to reach a revision that doesn't exist!"
            return self.history[lenHist]
            
    def getDrawing(self):
        """
        Getter for drawing data. Unlike text, drawing does not store history 
        (otherwise program would be too slow).
        """
        return self.drawing    
        
    def changeDrawing(self, newDrawing):
        """
        Setter for drawing data. 
        """
        self.drawing = newDrawing
            
    def getRevNum(self):
        """
        Returns the number of the most current revision
        """
        return len(self.history)

class PypadServer(Server, PypadData):    
    """
    PypadServer is the final object class, that contains necessary Server and
    PypadData attributes to communicate with the clients
    
    Its only methods are getters/setter wrappers for the data.
    Its parent class, Server, does all the notifications.
    """
    def __init__(self,  name, string='hello'):
        """
        Constructor for PypadServer object
        
        Args:
            string: string; initial text data to be set
            name: a string that becomes the name root on all Pypad windows.
        
        """
        Server.__init__(self, name)
        PypadData.__init__(self, string)
        
    def setState(self, sendingClient, newText=[], newDrawing =[], type = 'text'):
        """
        Setter for changing the state of the server
        
        Args:
            type: 'drawing' or 'text'; type of state change
            sendingClient: string; name of client  whose state changed, initiating the 
                PypadServer state
            newText: string; the new text contained in the sendingClient's text
                editor window
            newDrawing: 
        
        Written by Steven
        """
        if type == 'text':
            print '----------'
            print 'Changing the text of the server'
            self.changeText(newText)
            self.notifyClients(sendingClient, 'text')
        elif type == 'drawing':
            print 'Changing the drawing of the server'
            self.changeDrawing(newDrawing)
            self.notifyClients(sendingClient, 'drawing')  
        
    def getState(self, type):
        """
        Getter for changing the state of the server
        Whether state change is drawing or text specified by type
        
        Written by Steven
        """
        if type == 'text':
            if(self.VERBOSE): print "giving server text to client"
            return self.getText()
        elif type == 'drawing':
            if(self.VERBOSE): print "giving server drawing  to client"
            return self.getDrawing()
        else:
            print 'Error: text or drawing type?'
        
def main(script, *args):
    print "*** Pypad Server ***"
    server = PypadServer('Pypad_dot_com')
    server.VERBOSE = False
    
    for arg in args:
        if args == "-v":
            server.VERBOSE = True;
            
    
    server.requestLoop()    #starts the server

if __name__ == '__main__':
    main(*sys.argv)