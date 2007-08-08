import os
import sys
import pickle
import inspect
import shutil
from config import config
config = config()

DEBUG= 0
PICKLE_PATH="pdb"

def dbLoad(name):
	return SPickle().load(name)

def dbExists(name):
	#if self.config.debug:
	#	name = "debug.%s" % name
	return SPickle().exists(name)

def dbDump(name, obj=None):
	# depth of the dump is 2 now, since we're redirecting to '.dump'
	return SPickle().dump(name, obj, 2)

def if_cached_else(cond, name, function):
	s = SPickle()
	if (cond and s.exists(name)) or \
	   (cond and config.debug and s.exists("debug.%s" % name)):
		o = s.load(name)
	else:
		o = function()
		if cond:
			s.dump(name, o)	# cache the object using 'name'
	return o

class SPickle:
	def __init__(self):
		self.config = config

	def if_cached_else(self, cond, name, function):
		if cond and self.exists(name):
			o = self.load(name)
		else:
			o = function()
			if cond:
				self.dump(name, o)	# cache the object using 'name'
		return o

	def __file(self, name):
		return "%s/%s.pkl" % (PICKLE_PATH, name)
		
	def exists(self, name):
		return os.path.exists(self.__file(name))

	def load(self, name):
		""" 
		In debug mode, we should fail if neither file exists.
			if the debug file exists, reset name
			elif the original file exists, make a copy, reset name
			else neither exist, raise an error
		Otherwise, it's normal mode, if the file doesn't exist, raise error
		Load the file
		"""

		if self.config.debug:
			if self.exists("debug.%s" % name):
				name = "debug.%s" % name
			elif self.exists(name):
				debugname = "debug.%s" % name
				if not self.exists(debugname):
					shutil.copyfile(self.__file(name), self.__file(debugname))
				name = debugname
			else:	# neither exist
				raise Exception, "No such pickle based on %s" % self.__file(name)
		else:
			if not self.exists(name):
				raise Exception, "No such file %s" % name

		print "loading %s" % self.__file(name)
		f = open(self.__file(name), 'r')
		o = pickle.load(f)
		f.close()
		return o
			
	
	# use the environment to extract the data associated with the local
	# variable 'name'
	def dump(self, name, obj=None, depth=1):
		if obj == None:
			o = inspect.getouterframes(inspect.currentframe())
			up1 = o[depth][0] # get the frame one prior to (up from) this frame
			argvals = inspect.getargvalues(up1)
			# TODO: check that 'name' is a local variable; otherwise this would fail.
			obj = argvals[3][name] # extract the local variable name 'name'
		if not os.path.isdir("%s/" % PICKLE_PATH):
			os.mkdir("%s" % PICKLE_PATH)
		if self.config.debug:
			name = "debug.%s" % name
		f = open(self.__file(name), 'w')
		pickle.dump(obj, f)
		f.close()
		return


ssh_options = { 'StrictHostKeyChecking':'no', 
				'BatchMode':'yes', 
				'PasswordAuthentication':'no',
				'ConnectTimeout':'20'}

class SSH:
	def __init__(self, user, host, options = ssh_options):
		self.options = options
		self.user = user
		self.host = host
		return

	def __options_to_str(self):
		options = ""
		for o,v in self.options.iteritems():
			options = options + "-o %s=%s " % (o,v)
		return options

	def run(self, cmd):
		cmd = "ssh %s %s@%s '%s'" % (self.__options_to_str(), 
									self.user, self.host, cmd)
		if ( DEBUG == 1 ):
			print cmd,
		(f_in, f_out, f_err) = os.popen3(cmd)
		value = f_out.read()
		if value == "":
			raise Exception, f_err.read()
		if ( DEBUG == 1 ):
			print " == %s" % value
		f_out.close()
		f_in.close()
		f_err.close()
		return value

	def runE(self, cmd):
		cmd = "ssh %s %s@%s '%s'" % (self.__options_to_str(), 
									self.user, self.host, cmd)
		if ( DEBUG == 1 ):
			print cmd,
		(f_in, f_out, f_err) = os.popen3(cmd)

		value = f_out.read()
		if value == "":	# An error has occured
			value = f_err.read()

		if ( DEBUG == 1 ):
			print " == %s" % value
		f_out.close()
		f_in.close()
		f_err.close()
		return value.strip()
		
import time
class MyTimer:
	def __init__(self):
		self.start = time.time()

	def end(self):
		self.end = time.time()
		t = self.end-self.start
		return t

	def diff(self):
		self.end = time.time()
		t = self.end-self.start
		self.start = self.end
		return t