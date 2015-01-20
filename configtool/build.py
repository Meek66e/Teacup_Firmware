import wx
import wx.lib.newevent
import thread, shlex, subprocess
import os
from os.path import isfile, join
from sys import platform

if platform == "win32":
	from _subprocess import STARTF_USESHOWWINDOW


(scriptEvent, EVT_SCRIPT_UPDATE) = wx.lib.newevent.NewEvent()
SCRIPT_RUNNING = 1
SCRIPT_FINISHED = 2
SCRIPT_CANCELLED = 3

class ScriptThread:
	def __init__(self, win, script):
		self.win = win
		self.running = False
		self.cancelled = False
		self.script = script

	def Start(self):
		self.running = True
		self.cancelled = False
		thread.start_new_thread(self.Run, ())

	def Stop(self):
		self.cancelled = True

	def IsRunning(self):
		return self.running

	def Run(self):
		if platform == "win32":
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= STARTF_USESHOWWINDOW

		for cmd in self.script:
			evt = scriptEvent(msg = cmd, state = SCRIPT_RUNNING)
			wx.PostEvent(self.win, evt)
			args = shlex.split(str(cmd))
			try:
				if platform == "win32":
					p = subprocess.Popen(args,stderr=subprocess.STDOUT,stdout=subprocess.PIPE, startupinfo=startupinfo)
				else:
					p = subprocess.Popen(args,stderr=subprocess.STDOUT,stdout=subprocess.PIPE)
			except:
				evt = scriptEvent(msg = "Exception occurred trying to spawn command (%s)" % cmd, state = SCRIPT_CANCELLED)
				wx.PostEvent(self.win, evt)
				self.running = False
				return
			obuf = ''
			while not self.cancelled:
				o = p.stdout.read(1)
				if o == '': break
				if o == '\r' or o == '\n':
					if obuf.strip() != "":
						evt = scriptEvent(msg = obuf, state = SCRIPT_RUNNING)
						wx.PostEvent(self.win, evt)
					obuf = ''
				elif ord(o) < 32:
					pass
				else:
					obuf += o
					
			if self.cancelled:
				evt = scriptEvent(msg = None, state = SCRIPT_CANCELLED)
				wx.PostEvent(self.win, evt)
				p.kill()
				self.running = False
				return
			
			rc = p.wait()
			if rc != 0:
				msg = "RC = " + str(rc) + " - Build terminated"
				evt = scriptEvent(msg = msg, state = SCRIPT_CANCELLED)
				wx.PostEvent(self.win, evt)
				self.running = False
				return
			
			evt = scriptEvent(msg = "", state = SCRIPT_RUNNING)
			wx.PostEvent(self.win, evt)

				
		evt = scriptEvent(msg = None, state = SCRIPT_FINISHED)
		wx.PostEvent(self.win, evt)

		self.running = False

class Build(wx.Dialog):
	def __init__(self, parent, settings, f_cpu, cpu, baud):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Build teacup", style=wx.RESIZE_BORDER+wx.DEFAULT_DIALOG_STYLE)
		self.settings = settings
		self.SetFont(self.settings.font)
		self.root = self.settings.folder
		self.f_cpu = f_cpu
		self.cpu = cpu
		self.baud = baud
		self.Bind(wx.EVT_CLOSE, self.onExit)
		
		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer((10, 10))
		
		sz = wx.BoxSizer(wx.VERTICAL)
		sz.AddSpacer((10,10))
		
		tc = wx.TextCtrl(self, wx.ID_ANY, size=(900, 300), style=wx.TE_READONLY + wx.TE_MULTILINE)
		sz.Add(tc, 1, wx.EXPAND)
		self.log = tc
		
		sz.AddSpacer((10,10))
		hsz.Add(sz, 1, wx.EXPAND)
		hsz.AddSpacer((10, 10))
				
		self.SetSizer(hsz)
		
		self.Fit()
		builddir = join(self.root, "build")
		if not os.path.exists(builddir):
			os.makedirs(builddir)
			self.log.AppendText("Directory (%s) created\n\n" % builddir)
		
		self.compile()
		
	def compile(self):
		self.generateCompileScript()
		if len(self.script) == 0:
			self.log.AppendText("Nothing to compile!\n")
			self.active = False
		else:
			self.Bind(EVT_SCRIPT_UPDATE, self.compileUpdate)
			t = ScriptThread(self, self.script)
			self.active = True
			t.Start()
		
	def link(self):
		self.generateLinkScript()
		if len(self.script) == 0:
			self.log.AppendText("Nothing to link!\n")
			self.active = False
		else:
			self.Bind(EVT_SCRIPT_UPDATE, self.linkUpdate)
			t = ScriptThread(self, self.script)
			self.active = True
			t.Start()
		
	def generateCompileScript(self):
		self.script = []
		if platform == "win32":
			cmdpath = "\"" + join(self.settings.arduinodir, "avr-gcc") + "\""
		else:
			cmdpath = "avr-gcc"
		
		cfiles = [ f for f in os.listdir(self.root) if isfile(join(self.root,f)) and f.endswith(".c") ]
		for f in cfiles:
			basename = f[:-2]
			ofile = basename + ".o"
			alfile = basename + ".al"
			opath = "\"" + join(self.root, "build", ofile) + "\""
			cpath = "\"" + join(self.root, f) + "\""
			
			opts = self.settings.cflags
			opts = opts.replace("%ALNAME%", alfile)
			opts = opts.replace("%F_CPU%", self.f_cpu)
			opts = opts.replace("%CPU%", self.cpu)
			
			cmd = cmdpath + " -c " + opts + " -MMD -o " + opath + " " + cpath
			self.script.append(cmd)
			
	def generateLinkScript(self):
		self.script = []
		if platform == "win32":
			cmdpath = "\"" + join(self.settings.arduinodir, "avr-gcc") + "\""
		else:
			cmdpath = "avr-gcc"

		ofiles = [ "\"" + join(self.root, "build", f) + "\"" for f in os.listdir(join(self.root, "build")) if isfile(join(self.root,"build",f)) and f.endswith(".o") ]
		opath = " ".join(ofiles)
		elfpath = "\"" + join(self.root, "build", "teacup.elf") + "\""
		opts = self.settings.cflags
		opts = opts.replace("%ALNAME%", "teacup.elf")
		opts = opts.replace("%F_CPU%", self.f_cpu)
		opts = opts.replace("%CPU%", self.cpu)
		cmd = cmdpath + " " + self.settings.ldflags + " " + opts + " -o " + elfpath + " " + opath + " -lm "
		self.script.append(cmd)

		if platform == "win32":
			cmdpath = "\"" + join(self.settings.arduinodir, "avr-objcopy") + "\""
		else:
			cmdpath = "avr-objcopy"
		cmd = cmdpath + " " + self.settings.objcopyflags + " " +  elfpath + " teacup.hex"
		self.script.append(cmd)

	def compileUpdate(self, evt):
		if evt.msg is not None:
			self.log.AppendText(evt.msg + "\n")
			
		if evt.state == SCRIPT_RUNNING:
			pass
		if evt.state == SCRIPT_CANCELLED:
			self.log.AppendText("Compile terminated abnormally\n\n")
			self.active = False
		if evt.state == SCRIPT_FINISHED:
			self.log.AppendText("Compile completed normally\n\n")
			self.link()

	def linkUpdate(self, evt):
		if evt.msg is not None:
			self.log.AppendText(evt.msg + "\n")
			
		if evt.state == SCRIPT_RUNNING:
			pass
		if evt.state == SCRIPT_CANCELLED:
			self.log.AppendText("Link terminated abnormally\n\n")
			self.active = False
		if evt.state == SCRIPT_FINISHED:
			self.log.AppendText("Link completed normally\n\n")
			self.active = False
		
	def onExit(self, evt):
		if self.active:
			return
		
		self.EndModal(wx.ID_OK)

class Upload(wx.Dialog):
	def __init__(self, parent, settings, f_cpu, cpu, baud):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Upload teacup", style=wx.RESIZE_BORDER+wx.DEFAULT_DIALOG_STYLE)
		self.settings = settings
		self.SetFont(self.settings.font)
		self.root = self.settings.folder
		self.f_cpu = f_cpu
		self.cpu = cpu
		self.baud = baud
		self.Bind(wx.EVT_CLOSE, self.onExit)
		
		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer((10, 10))
		
		sz = wx.BoxSizer(wx.VERTICAL)
		sz.AddSpacer((10,10))
		
		tc = wx.TextCtrl(self, wx.ID_ANY, size=(900, 300), style=wx.TE_READONLY + wx.TE_MULTILINE)
		sz.Add(tc, 1, wx.EXPAND)
		self.log = tc
		
		sz.AddSpacer((10,10))
		hsz.Add(sz, 1, wx.EXPAND)
		hsz.AddSpacer((10, 10))
				
		self.SetSizer(hsz)
		
		self.Fit()
		self.generateUploadScript()
		if len(self.script) == 0:
			self.log.AppendText("Nothing to upload!\n")
			self.active = False
		else:
			self.Bind(EVT_SCRIPT_UPDATE, self.uploadUpdate)
			t = ScriptThread(self, self.script)
			self.active = True
			t.Start()
		
	def generateUploadScript(self):
		self.script = []
		if platform == "win32":
			cmdpath = "\"" + join(self.settings.arduinodir, "avrdude") + "\""
		else:
			cmdpath = "avrdude"
		
		cmd = cmdpath + " -c %s -b %s -p %s -P %s -U flash:w:teacup.hex" % \
			(self.settings.programmer, self.baud, self.cpu, self.settings.port)
		self.script.append(cmd)
	
	def uploadUpdate(self, evt):
		if evt.msg is not None:
			self.log.AppendText(evt.msg + "\n")
			
		if evt.state == SCRIPT_RUNNING:
			pass
		if evt.state == SCRIPT_CANCELLED:
			self.log.AppendText("Upload terminated abnormally" + "\n")
			self.active = False
		if evt.state == SCRIPT_FINISHED:
			self.log.AppendText("Upload completed normally" + "\n")
			self.active = False

		
	def onExit(self, evt):
		if self.active:
			return
		
		self.EndModal(wx.ID_OK)

