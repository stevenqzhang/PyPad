"""
PypadClient.py

INTRODUCTION
Contains the PypadClient class.
The PypadClient class is the controller in the model view controller design 
pattern of Pypad. It interfaces between the server and gui objects

AUTHORS 
Steven Zhang, Jason Poon, Reyner Crosby

CREDITS
Pyro author and package: http://pyro.sourceforge.net
Remoteobjects Library: Allen Downey
Subject-Observer-Modifier template: Mark Sheldon

CHANGELOG
11/26/2010
Cleaned up code and comments. 
Made the drawing canvas work a little more smoothly.
Made all loops into PypadClient class methods
-Steven

4/29/10
Cleaned up code and added comments
-Steven

4/28/10
Added collaboration abilities for the drawing canvas
- Steven

4/27/10
Added improved version of revision history.
- Jason

4/23/10
Switched to the Remote Object Library
Encapsulated methods by adding a client class for listening to server
Use server side pushing (notified as in obeserver-subject-modifer) for changes: 
all changes now instantaneous
-Steven

4/23/10
Added revision history capabilities
-Jason

4/9/10 
Created initial frame work
-Jason, Steven, Reyner
"""


from RemoteObject import *
from threading import Thread
from PypadGui import *
from time import sleep
from RemoteObject import *
import sys

DEBUG = False

class PypadClient(RemoteObject):
    """
    A PypadClient (herein called client) 
    is an object that watches its PypadGui and the PypadServer.
    
    Whenever the gui changes, the client sends that update to the server.
    
    The server immediately responds by notifying all the other clients currently
    running to update their guis. 
    
    That way, all the changes are (almost) instantaneous
    
    Some code is modified from:
    http://ece.olin.edu/sd/current/web/notes/25_subject_observer/subject_observer.html
    """

    def __init__(self, serverName):
        """
        Constructor for PypadClient object
        
        Args:
            serverName: string; the name of the PypadServer object to connect to
                this name must match the defined in the instantiation of said 
                object
        
        """
        
        # setting these flags to be true allows the initial gui to 
        # display the current data
        self.textNeedsUpdating = True       
        self.drawingNeedsUpdating = True
        ns = NameServer()
        # register with the server
        self.serverName = serverName
        self.server = ns.get_proxy(self.serverName)
        self.clientName, self.id = self.server.register()
        print "I just registered with server."

        # connect to the name server
        
        RemoteObject.__init__(self, self.clientName)
        print "I just registered with Name Server."
        # modifying attributes
    
    
    # Getters
    def getClientName(self):
        """Getter for client name. added 4/24 Steven"""
        return self.clientName
    def getId(self):
        """Getter for id. added 11/26 Steven"""
        return self.id

    # the following methods are added by Steven
    # following modification from Mark Sheldon's Subject, Modifier, Observer
    # examples in the link above
    def notify(self, type):
        """
        This method is invoked remotely
        
        When the PypadServer is modified, it invokes notify;
        then the client sets off flags (corresponding to whether text or drawing
        has changed), which allows the client to be updated in the loops below
        
        Args:
            type: 'text' or 'drawing'
        """
        if(DEBUG): print 'Notified', type
        if type == 'text':
            if(DEBUG): print 'self.textNeedsUpdating = True'
            self.textNeedsUpdating = True
        elif type == 'drawing':
            self.drawingNeedsUpdating = True

    def modify(self, text=[], drawing=[], type = 'text'):
        """
        Changed the state of the server data. 
        
        Args:
            type: 'text' or 'drawing'. 
                Specifies whether text or drawing should be updated
        """
        self.server.setState(self.name, newText = text, newDrawing = drawing, type = type)
        if DEBUG: print 'Setting state to ' + str(self.server.getState())
        
    def cleanup(self):
        """
        Inherited RemoteObject method to stop itself
        Unregisters self from PypadServer
        
        Added by Steven Zhang 4/24
        """
        print 'Disconnecting from server'
        self.server.remove(self.clientName)
        RemoteObject.cleanup(self)
    
    def updateTextLoop(self, gui):
        """
        This loop is the event loop that handles requests between client and gui
        text. 
        
        The client checks to see if gui has changed. If so, it notifies the server
        
        It also checks to see if server has flagged the client to update the gui.
        If so, it updates the gui.
            
        Args: 
            gui: the corresponding PypadGui object
            
        Steven wrote most of this loop.
        """
        if(DEBUG): print "in updateTextLoop"
        while True:
            # Check to see if gui has changed due to user input
            if gui.t.hasTextChanged() == True:
                if(DEBUG): print "Gui just changed"
                gui.t.setTextAsUpdated()
                self.modify(text = gui.t.getText(), type = 'text')
                if(DEBUG): print "state=" + str(gui.t.getText())
                
            # Checks to see client's textNeedsUpdating flag has been raised by 
            # server
            if self.textNeedsUpdating == True:
                if(DEBUG): print "client.textNeedsUpdating == True"
                if(DEBUG): print self.server.getState('text')
                self.textNeedsUpdating = False
                gui.t.setText(self.server.getState('text'))
                
            # This part which checks to see if the a person has inputed
            # a request for new revision. Since we want to check this as much as
            # possible, this request is contained in this loop, which does not pause
            # like the updateRevLoop does.
            # This is the only time gui's attributes are accessed directly
            # We can easily implement getters and setters with more time
            if gui.t.getRevUpdateFlag() == True:
                newRev = int(gui.t.getRevNumReq())
                
                #update to requested rev, but only if requested rev < current rev
                if newRev < self.server.getRevNum():
                    self.modify(text = self.server.getHistory(newRev), type = 'text')
                gui.t.setText(self.server.getState('text'))
                gui.t.setRevUpdateFlag(False)
            
    def updateRevLoop(self, gui):
        """
        This loop is the event loop that handles requests between client and 
        the gui's revision box.
        
        Jason wrote this loop.
        """
        if(DEBUG): print "in updateRevLoop"
        
        while True:
            if(DEBUG): print gui.t.revInput
            sleep(5)    
            # we pause so that the user can input something in the rev box before 
            # it gets overwritten by the automated revision updater
            if gui.t.revInput == False:
                # Continually update the revision number on each GUI.
                gui.t.nameTextCtrl.SetValue(str(self.server.getRevNum()))

    def updateDrawingLoop(self, gui):
        """
        This loop is the event loop that handles requests between client and gui
        drawing. Works in principle just like the updateTextLoop.
        
        Jason wrote the initial loop
        Steven refactored it to make methods similar named to the updateTextLoop
        """
        if(DEBUG): print "in update Drawing Loop"  
        while(True):
            sleep(1)    
            # drawing objects are full of data, so we don't want to update too often
            # due to latency
            if gui.d.hasDrawingChanged() == True:
                print "Drawing just changed"
                gui.d.setDrawingAsUpdated()
                self.modify(drawing = gui.d.getDrawing(),type = 'drawing')
            if self.drawingNeedsUpdating == True:
                print "self.drawingNeedsUpdating == True"
                self.drawingNeedsUpdating = False
                gui.d.setDrawing(self.server.getState('drawing'))
                
    def clientLoops(self, gui):
        """
        Initializes the loops for text, rev, request, and drawing update loops
        
        Added 11/16/10 by Steven
        """
        
        
        t1 = Thread(target = self.updateTextLoop, args =[gui])
        t1.start()
        
        # in essence, the client request loop handles interfacing between the server
        # and client. The other update loops handle interfacing between client and 
        # gui
        t2 =  Thread(target = self.requestLoop)   
        t2.start()
        
        t3 = Thread(target = self.updateRevLoop, args =[gui])
        t3.start()
        
        t4 = Thread(target = self.updateDrawingLoop, args =[gui])
        t4.start()
        
            
def main(script, *args):
    """
    Starts the gui, client object and various loops
    The client loop and the three loops for updating drawing, text, revisions
    are in separate threads.
    
    The gui loop runs on the initial/base thread
    
    Written mostly by Steven
    """
    serverName = 'Pypad_dot_com'
    ns = NameServer()
    serverData = ns.get_proxy(serverName)
    
    client = PypadClient(serverName)
    app = wx.App(False)
    gui = PypadGui()
    gui.t.SetTitle("Pypad client, connected to " + client.serverName
                               + ':' + str(client.getId()) + '.')
    client.clientLoops(gui)
    
    
    app.MainLoop()      #gui loop
    print "in GUI Loop"

if __name__ == '__main__':
    main(*sys.argv)