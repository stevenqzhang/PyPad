"""
PypadGui.py

INTRODUCTION
Contains the PypadGui class (hasa PypadGuiText and PypadGuiDrawing object)
The PypadGui class is the view in the model view controller model of Pypad,
displaying the text editor and canvas necessary for collaborative editing

AUTHORS
Steven Zhang, Reyner Crosby, Jason Poon

CREDITS
Text editor inspired by wxpython tutorial 
from http://wiki.wxpython.org/WxHowtoSmallEditor

CHANGELOG
11/26/2010
Cleaned up code and comments. 
Made the drawing canvas work a little more smoothly
-Steven

4/29/10
Cleaned up code and added comments
-Steven

4/28/10
Added collaboration abilities for the drawing canvas. Fixed Pyro pickling error
with the drawing window by removing brush/pen selection palette
-Steven

Made separate windows for drawing and text
"Fixed" drawing refresh where the drawing canvas flickers constantly
-Matt

4/26/10
Created drawing canvas framework, including a brush selection palette
-Reyner

4/24/10
Fixed the cursor jumping in the gui text by storing and then updating the
insertion point (cursor) location whenever text is updated
-Steven

4/22/10 
Added framework for viewing history
-Jason

4/18/10
Tweaked collaboration framework in PypadGuiText.
-Steven

4/12/10
Made all variables in initial text editor framework private. Instead using
getters and setters
-Steven

4/9/2010 
Created initial text framework based on wxpython tutorial 
-Steven, Jason, Reyner

BUGS
Drawing area canvases are not very responsive.
This is because of Python's threading limitations, and the fact
that we are storing drawing lines essentially 
as a vector graphic (although the display is as a bitmap)


"""
import wx
import wx.richtext as rt
import os.path
import sys
from time import sleep

DEBUG = True    # change this flag if you want details on every gui change

class PypadGuiText(wx.Frame):
    """
    The PypadGuiText class creates one text editor frame, with methods for
    communicating with the controller, PypadClient
    """
    def __init__(self, parent=None, id=-1, title='Pypad', position=(50, 50), \
    size=(700, 600)): 
        """
        Constructor for PypadGuiText class.
        For the arguments and what they mean, see 
        http://wiki.wxpython.org/WxHowtoSmallEditor
        
        """
        # Some gui initializers, created by Steven, Jason, Reyner 4/9/2010
        # Refactored and cleaned up by Matt
        wx.Frame.__init__(self, parent, id, title, position, size) 
        self.textpanel = wx.Panel (self)
        self.textpanel.SetBackgroundColour('white')
        self.control = wx.TextCtrl(self, size=(400, 500), style=wx.TE_MULTILINE)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.control.Bind(wx.EVT_TEXT, self.onTextChange)
        self.CreateExteriorWindowComponents()

		# Change Flag notifies controller if this object's text has changed
        self.changeFlag = False; 

        # History Revision, Added 4/12/2010 by Jason
        # Creating the revision user interfaces
        self.nameLabel = wx.StaticText(self, label="Revision:")
        self.nameTextCtrl = wx.TextCtrl(self, value="0")
        self.revButton = wx.Button(self, label="Update to revision")
        
        # Placing the revision user interfaces
        self.nameLabel.SetDimensions(x=500, y=100, width=-1, height=-1)
        self.nameTextCtrl.SetDimensions(x=550, y=100, width=50, height=-1)
        self.revButton.SetDimensions(x=550, y=125, width=100, height=-1)
        
        # Creating the callbacks on the revision user interface
        self.revButton.Bind(wx.EVT_BUTTON, self.requestRevUpdate)
        
        # The following line was originally for the revision history input box
        # it stopped refreshing of the revision text box when user started
        # typing into it. Unfortunately, it didn't work, so we opted for a 
        # timed based method instead.
        self.Bind(wx.EVT_CHAR, self.revUserInput, self.nameTextCtrl)
        
        # Flags
        
        # The revision number user requests thru the gui
        self.revNumReq = 0          
        self.revInput = False       # True when user is typing in revision box
        self.revUpdateFlag = False  # True gui is updating to certain revision
        
        # True when gui text becomes different from server text
        self.textChangeFlag = False 
        
        # Filename related attributes
        self.filename = "pypadtext.txt"
        self.dirname = '.'

# Text  collaboration framework created by Jason, Reyner, Steven 
# Steven made all the getter/setter methods. 
# Steven fixed the bug where the cursor jumps by using the insertionPoint 
# methods
    def onTextChange(self, event):
        """ 
        Updates textChangeFlag when user starts typing in the gui text area 
        
        Args: 
            event: a wxpython event
        """
        self.textChangeFlag = True;
    def getText(self):
        """Getter for string in gui text area """
        return (self.control.GetValue())
    def setText(self, textState):
        """
        Setter for gui text area. Also make sure cursor remains in one place
        thru the insertion point methods
        
        Args:
            textState: string; 
        """
        oldInsertionPoint = self.control.GetInsertionPoint()
        self.control.SetValue(textState)
        self.control.SetInsertionPoint(oldInsertionPoint)   
        self.textChangeFlag = False
    def hasTextChanged(self):
        """
        Returns true whenever the text area has been changed by user typing
        """
        return self.textChangeFlag
    def setTextAsUpdated(self):
        """
        Marks the gui text as updated. Used whenever the client controller
        updates the gui from server data
        """
        self.textChangeFlag = False

# History Revision, Added Apr 22 2010 by Jason
# Updated and improved version, Added Apr 27 2010 by Jason
    def requestRevUpdate(self,event):
        """
        Called whenever the user submits request for past revision. 
        It makes the  
        """
        print('update requested!')
        self.revInput = False
        self.revNumReq = self.nameTextCtrl.GetValue()
        self.revUpdateFlag = True
    def revUserInput(self,event):
        """
        Sets flag for user input whenever someone is typing in the revision
        text box.
        Currently doesn't work for some reason because it's bound incorrectly
        to the method
        """
        print('user typing rev number!')
        self.revInput = True
        
    def getRevUpdateFlag(self):
        """Getter for revUpdateFlag"""
        return self.revUpdateFlag
        
    def setRevUpdateFlag(self, flag):
        """Setter for revUpdateFlag"""
        self.revUpdateFlag = flag
    
    def getRevNumReq(self):
        """Getter for revNumReq"""
        return self.revNumReq
      
# code from tutorial found here: 
# Edited heavily by Matt 4/27
    def CreateExteriorWindowComponents(self):
        """
        Create "exterior" window components, such as menu and status
        bar. 
        """
        self.CreateMenu()
        self.CreateStatusBar()

    def CreateMenu(self):
        """
        Creates menu options. Currently save as doesn't work, but open works.
        """
        fileMenu = wx.Menu()
        for id, label, helpText, handler in \
            [(wx.ID_ABOUT, '&About', 'Information about this program',
                self.OnAbout),
             (wx.ID_OPEN, '&Open', 'Open a .txt file', self.OnOpen),
             (wx.ID_SAVE, '&Save', 'Save the current file', self.OnSave),
             (wx.ID_SAVEAS, 'Save &As', 'Save the file under a different name',
                self.OnSaveAs),
             (None, None, None, None),
             (wx.ID_EXIT, 'E&xit', 'Terminate the program', self.OnExit)]:
            if id == None:
                fileMenu.AppendSeparator()
            else:
                item = fileMenu.Append(id, label, helpText)
                self.Bind(wx.EVT_MENU, handler, item)

        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, '&File') # Add the fileMenu to the MenuBar
        self.SetMenuBar(menuBar)  # Add the menuBar to the Frame

    # Helper methods from tutorial. These methods are used for open/saving files
    def SetTitle(self, title):
        """Sets the title of the text editor window"""
        # PypadGui.SetTitle overrides wx.Frame.SetTitle, so we have to
        # call it using super:
        super(PypadGuiText, self).SetTitle(title)
        
    def defaultFileDialogOptions(self):
        ''' 
        Return a dictionary with file dialog options that can be
        used in both the save file dialog as well as in the open
        file dialog. 
        '''
        return dict(message='Choose a file', defaultDir=self.dirname,
                    wildcard='*.*')

    def askUserForFilename(self, **dialogOptions):
        dialog = wx.FileDialog(self, **dialogOptions)
        if dialog.ShowModal() == wx.ID_OK:
            userProvidedFilename = True
            self.filename = dialog.GetFilename()
            self.dirname = dialog.GetDirectory()
            
            # Update the window title with the new filename
            titleRoot = self.Title[0  :  self.Title.find('.') + 1]
            self.SetTitle(titleRoot + ' Saved to ' + self.filename) 
        else:
            userProvidedFilename = False
        dialog.Destroy()
        return userProvidedFilename

    # Event handlers, edited by Matt
    def OnAbout(self, event):
        """
        Called when user clicks File-> About
        """
        dialog = wx.MessageDialog(self, \
        'A collaborative text and drawing editor in wxPython.', 
            'About Pypad', wx.OK)
        dialog.ShowModal()

    def OnExit(self, event):
        """Called when user clicks File -> Exit """
        self.Close()  # Close the main window.

    def OnSave(self, event):
        """Called when user clicks File -> Save"""
        try:    #this try/except was added by Steven to prevent save errors
            textfile = open(os.path.join(self.dirname, self.filename), 'w')
            textfile.write(self.control.GetValue())
            textfile.close()
        except:
            dialog = wx.MessageDialog(self, 'Please Save As first', 'Error', wx.OK)
            dialog.ShowModal()

    def OnOpen(self, event):
        """Called when user clicks File -> Open"""
        # if self.askUserForFilename(style=wx.OPEN,
        # **self.defaultFileDialogOptions()):
        # textfile = open(os.path.join(self.dirname, self.filename), 'r')
        # self.control.SetValue(textfile.read())
        # textfile.close()
			
       #Code from tutorial
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", \
        "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
           self.filename = dlg.GetFilename()
           self.dirname = dlg.GetDirectory()
           f = open(os.path.join(self.dirname, self.filename), 'r')
           self.control.SetValue(f.read())
           f.close()
        dlg.Destroy()

    def OnSaveAs(self, event):
        """Called when user clicks File -> Open"""
        if self.askUserForFilename(defaultFile=self.filename, \
        style=wx.SAVE, **self.defaultFileDialogOptions()):
            self.OnSave(event)
      
            
			
class PypadGuiDrawing(wx.Frame):
    """
    The PypadGuiDrawing class creates one drawing editor frame, with methods for
    communicating with the controller, PypadClient
    """

    def __init__(self, parent=None, id=-1, title='Pypad Drawing', \
    position=(750, 50), size=(500, 600)): 
        # These methods were originally created by Reyner
        # Matt edited them to make a cleaner window consistent with text editor
        # window
        wx.Frame.__init__(self, parent, id, title, position, size) 
        self.drawpanel = wx.Panel(self)
        self.drawpanel.SetBackgroundColour('white')
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.CreateExteriorWindowComponents()        
        
        # Set up drawing canvas
        self.fromPoint = None
        self.lineList = []  
        # lineList  is data structure that stores the list of lines drawn. 
        # It is used to communicate data to the client to server
        
        # Bind drawing methods to mouse movements
        self.drawpanel.Bind(wx.EVT_PAINT, self.DrawSetup)
        self.drawpanel.Bind(wx.EVT_MOTION, self.DrawDrawing)
        self.drawpanel.Bind(wx.EVT_LEFT_DOWN, self.DrawDrawing)
        self.drawpanel.Bind(wx.EVT_RIGHT_DOWN, self.ReadDrawing)
	
		# drawingChangeFlag notifies controller if drawing should be updated
        # When user edits the drawing
        self.drawingChangeFlag = False; 

# Drawing Stuff here. Original framework by Reyner
# Steven added the getters, setters, etc. for communicating with client/server
    def onDrawingChange(self, event):
        """ 
        Updates drawingChangeFlag when user starts drawing in the gui draw area        
        """
        self.drawingChangeFlag = True;
    def getDrawing(self):
        """Getter for data structure representing drawn lines"""
        return (self.lineList)
    def setDrawing(self, lineList):
        """
        Updates the drawing from external lineList by calling readDrawing method
        Called by client whenever server needs to update this gui
        """
        self.lineList = lineList
        self.ReadDrawing()
        
    def hasDrawingChanged(self):
        """
        Returns true whenever the drawing area has been changed by user
        """
        return self.drawingChangeFlag
    def setDrawingAsUpdated(self):
        """
        Marks the gui drawing as updated. Used whenever the client controller
        updates the gui from server data
        """
        self.drawingChangeFlag = False
    def DrawSetup(self, event):
        """Sets up a PaintDC object in the window for drawing on"""
        self.dc = wx.PaintDC(self.drawpanel)
        self.DrawPanel()
    def DrawPanel(self):
        """Sets up the drawing canvas
        Made by Reyner
        """
        self.dc.Clear()
        self.dc.SetPen(wx.Pen('black'))
        self.dc.SetBrush(wx.Brush('white'))
        panelBoundingRect = wx.Rect(0, 0, 70, 70)
        self.dc.DrawRoundedRectangleRect(panelBoundingRect, 2)
        
        # The following features were disabled for remote sharing by Steven 
        # because of pickling issues with pen/brush size. 
        # Thus the drawing can only be drawn in black.
        # However, if you want color and line thickness control on individual
        # drawing windows, uncomment the block below
        
        #=======================================================================
        # #Set up color control box
        # colors = ['black', 'red', 'yellow', 'green', 'blue', 'purple']
        # for i in range(len(colors)):
        #    rect = wx.Rect(5+10*i, 5, 10, 10)
        #    self.dc.SetBrush(wx.Brush(colors[i]))
        #    self.dc.SetPen(wx.Pen(colors[i]))
        #    self.dc.DrawRoundedRectangleRect(rect, 4)
        # 
        # #set up brush size controls
        # radii = [1, 2, 3, 4, 5]
        # self.dc.SetPen(wx.Pen('black'))
        # for i in range(len(radii)):
        #    self.dc.SetBrush(wx.Brush('black'))
        #    self.dc.DrawCircle(10+10*i, 25, radii[i])
        #
        # self.dc.DrawText('Erase', 5, 35)    
        #=======================================================================
        
        #add "clear" and "erase" controls
        self.dc.DrawText('Clear', 5, 50)       
        
    
    def DrawDrawing(self, event):
        """
        Called when mouse movement happens over the drawing canvas. 
        Draws lines and stores them in lineList
        This was made by Reyner
        """
        if event.LeftIsDown():
            self.onDrawingChange(event)
            
        def IsPointInRect(point, rect):
            """Tells whether or not current line is being drawn in drawing
            rectangle
            """
            rectXMin = rect[0]
            rectXMax = rect[0]+rect[2]
            rectYMin = rect[1]
            rectYMax = rect[1]+rect[3]
            if rectXMin < point[0] < rectXMax \
            and rectYMin < point[1] < rectYMax:
                return True
            else:
                return False
        
        def setParamForPoint(point):
            """Sets colors"""
            if IsPointInRect(point, wx.Rect(5, 5, 65, 10)):
                colorMap = {5: 'black',
                            15: 'red',
                            25: 'yellow',
                            35: 'green',
                            45: 'blue',
                            55: 'purple'}
                for xMin in colorMap:
                    if xMin < point[0] < xMin+10:
                        curPenWidth = self.dc.GetPen().GetWidth()
                        self.dc.SetPen(wx.Pen(colorMap[xMin], curPenWidth))
            #set thickness
            if IsPointInRect(point, wx.Rect(5, 15, 65, 20)):
                radiusMap = {5: 1, 15: 4, 25: 6, 35: 8, 45: 10}
                for xMin in radiusMap:
                    if xMin < point[0] < xMin+10:
                        curPenColor = self.dc.GetPen().GetColour().GetAsString()
                        self.dc.SetPen(wx.Pen(curPenColor, radiusMap[xMin]))
            #erase
            if IsPointInRect(point, wx.Rect(5, 35, 65, 12)):
                self.dc.SetPen(wx.Pen('white', 15))
            #clear
            if IsPointInRect(point, wx.Rect(5, 50, 65, 12)):
                self.lineList = list()
                self.dc.Clear()
                self.DrawPanel()
                self.onDrawingChange(event)
        
        point = event.GetPosition()
        if self.fromPoint == None:
            self.fromPoint = point
        thisLine = []
        if event.LeftIsDown():
            if IsPointInRect(point, wx.Rect(0, 0, 70, 70)):
                setParamForPoint(point)
            else:
                self.dc.DrawLine(self.fromPoint[0], self.fromPoint[1],\
                point[0], point[1])
                thisLine.append(self.fromPoint)
                thisLine.append(point)
                penColor = self.dc.GetPen().GetColour()
                penWidth = self.dc.GetPen().GetWidth()
                #thisLine.append([penColor, penWidth]) #don't care about pen
                thisLine.append([])
        self.fromPoint = point
        
        if thisLine != []:
            if DEBUG: print thisLine
            if DEBUG: print self.lineList
            self.lineList.append(thisLine)
        
    def ReadDrawing(self, event=[]):
        """
        Called whenever drawing canvas is updated by client/server
        notifications. 
        
        It does this by clearing the canvas and redrawing every
        line that the server stores. This is inefficient, but works fairly well
        
        A better method would be to store on the server only recent changes, 
        so that changes accumulate on the gui. This would make it faster, but
        more lines are missed. 
        
        All these problems are in part due to Python's relatively poor threading 
        abilities
        
        Made by Reyner. Updated by Steven/Jason to remove pen/brush selections
        """
        
        self.DrawPanel()

        self.dc.SetBrush(wx.Brush('red'))
        self.dc.SetPen(wx.Pen('black',1))
        
        for segment in self.lineList:
            self.dc.DrawLine(segment[0][0],segment[0][1],\
            segment[1][0],segment[1][1])
        self.setDrawingAsUpdated()
      
# The following code is modified from the text editor tutorial. 
# See corresponding lines in the PypadGuiText class on this file
# edited heavily by Matt. 
    def CreateExteriorWindowComponents(self):
        '''Create "exterior" window components, such as menu and status
            bar. '''
        self.CreateMenu()
        self.CreateStatusBar()

    def CreateMenu(self):
        fileMenu = wx.Menu()
        for id, label, helpText, handler in \
            [(wx.ID_ABOUT, '&About', 'Information about this program',
                self.OnAbout),
             (wx.ID_EXIT, 'E&xit', 'Terminate the program', self.OnExit)]:
            if id == None:
                fileMenu.AppendSeparator()
            else:
                item = fileMenu.Append(id, label, helpText)
                self.Bind(wx.EVT_MENU, handler, item)

        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, '&File') # Add the fileMenu to the MenuBar
        self.SetMenuBar(menuBar)  # Add the menuBar to the Frame

    def SetTitle(self, title = 'Pypad Client Editor'):
        # PypadGui.SetTitle overrides wx.Frame.SetTitle, so we have to
        # call it using super:
        super(PypadGui, self).SetTitle(title)

    # Event handlers:
    def OnAbout(self, event):
        dialog = wx.MessageDialog(self, 'A collaborative text editor in WX' + 
                                  '\n This is the drawing add-on', 
            'About Pypad', wx.OK)
        dialog.ShowModal()
        #dialog.Destroy()

    def OnExit(self, event):
        self.Close()  # Close the main window.

class PypadGui():
    """
    A class that contains both a PypadGuiText and 
    PypadGuiDrawing object
    """
    def __init__(self, parent=None, id=-1, title='Unconnected Pypad Client', 
                 position=(50, 50), size=(700, 600), \
    titled='Pypad Drawing', positiond=(750, 50), sized=(500, 600)): 
        """
        Constructor for PypadGui class.
        Creates a text and drawing window.
        
        variable names appended with 'd' are the drawing window equivalents
        """
        self.t = PypadGuiText(parent, id, title, position, size) 
        self.d = PypadGuiDrawing(parent, id, titled, positiond, sized)
        self.t.Show()
        self.d.Show()
		
def main(script, *args):
    app = wx.App(False)
    gui = PypadGui()

    app.MainLoop()

if __name__ == '__main__':
    main(*sys.argv)