# PyPad

A network collaborative editing platform written in Python.

This was a project we did in ENGR 2510 Software Design course, Spring 2010.

Team members were:

+ Reyner Crosby
+ Jason Poon
+ Matt Huang
+ [Steven Zhang](http://stevenzhang.com)

# How to install

0. Install these Python libraries: [pyro](http://www.xs4all.nl/~irmen/pyro3/download.html) 
	[wx](http://www.wxpython.org/download.php)
	
1. Run pyro nameserver 

	* see info on how to use pyro-ns command [here](http://pyro.sourceforge.net/manual/5-nameserver.html#cmds)

2. Get IP address listed on 4th line:  URI is: ....

3. Enter IP address `default_ns_host` value in RemoteObject.py (line 9)

	* (this should have been a commandline argument but...)

4. Run PypadServer.py from command line. Add parameter -v if you want verbose output

5. Run PypadClient.py.

6. Repeat step 5 as many times as desired on any computer on the local network.

# Technical details

Look at the source code or look at our technical report [here](http://www.stevenzhang.com/files/sd_pypad.pdf). Be mindful that it was written by then college sophomores and first-years :)
