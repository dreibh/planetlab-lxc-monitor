#!/bin/env python
#
# Helper functions that minipulate the PLC api.
# 
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
# Copyright (C) 2006, 2007 The Trustees of Princeton University
#
# $Id: plctool.py,v 1.2 2007/04/19 20:43:00 mef Exp $
#

from monitor.wrapper.emailTxt import *
import xml, xmlrpclib
import logging
import time
import config
import getpass, getopt
import sys

logger = logging.getLogger("monitor")
XMLRPC_SERVER = 'https://www.planet-lab.org/PLCAPI/'
api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False, allow_none = True)
auth = None

def nodesDbg(argv):
	"""Returns list of nodes in dbg as reported by PLC"""

	global api, auth
	dbgNodes = []
	allnodes = api.GetNodes(auth, None, ['hostname','boot_state'])
	for node in allnodes:
		if node['boot_state'] == 'dbg': dbgNodes.append(node['hostname'])
	logger.info("%d nodes in debug according to PLC." %len(dbgNodes))
	return dbgNodes


def siteId(argv):
	"""Returns loginbase for given nodename"""

	global api, auth
	nodename = argv[0]
	site_ids = api.GetNodes(auth, [nodename], ['site_id'])
	if len(site_ids) == 1:
		site_id = [site_ids[0]['site_id']]
		loginbase = api.GetSites (auth, site_id, ["login_base"])
		return loginbase[0]['login_base']

def slices(argv):
	"""Returns list of slices for a site."""

	global api, auth
	if len(argv) < 1:
		printUsage("not enough arguments; please provide loginbase")
		sys.exit(1)

	loginbase = argv[0]
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	slices = api.GetSlices (auth, {'name':"%s_*"%loginbase},['name'])
	slices = map(lambda x: x['name'],slices)
	return slices

def getpcu(argv):
	"""Returns dict of PCU info of a given node."""

	global api, auth
	nodename = argv[0].lower()
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	pcus = api.GetNodes(auth, [nodename], ['pcu_ids'])
	if len(pcus):
		pcus = map(lambda x: x['pcu_ids'],pcus)[0]
		nodepcus = api.GetPCUs(auth,pcus)
	else:
		nodepcus = []
	return nodepcus


def getSiteNodes(argv):
	"""Returns all site nodes for site id (loginbase)."""
	global api, auth
	if len(argv) < 1:
		printUsage("not enough arguments; please provide loginbase")
		sys.exit(1)

	loginbase = argv[0]
	nodelist = []
	site_ids = api.GetSites(auth, {'login_base': "%s" % loginbase}, ['node_ids'])
	if len(site_ids) == 1:
		node_ids = site_ids[0]['node_ids']
		nodes = api.GetNodes(auth,node_ids,['hostname'])
		nodelist = map(lambda x: x['hostname'], nodes)
	elif len(site_ids) == 0:
		logger.info("getSiteNodes: can't find site %s" %loginbase)	      
	nodelist.sort()
	return nodelist

def renewAllSlices (argv):
	"""Sets the expiration date of all slices to given date"""
	global api, auth

	newexp = argv[0]
	# convert time string using fmt "%B %d %Y" to epoch integer
	try:
		newexp = int(time.mktime(time.strptime(newexp,"%B %d %Y")))
	except ValueError, e:
		errormsg = """Expecting date to be in Month Day Year
  e.g., April 7 2007
  new expiration date provided %s""" % newexp
		printUsage(errormsg)
		sys.exit(1)
		
	slices = api.GetSlices(auth)
	for slice in slices:
		name = slice['name']
		exp = int(slice['expires'])
		olddate = time.asctime(time.localtime(exp))
		slice_attributes = api.GetSliceAttributes(auth,slice['slice_attribute_ids'])
		for slice_attribute in slice_attributes:
			if slice_attribute['name'] == "enabled":
				print "%s is suspended" % name
		if exp < newexp:
			newdate = time.asctime(time.localtime(newexp))
			ret = api.SliceRenew(auth,name,newexp)
			if ret == 0:
				print "failed to renew %s" %name

def nodeBootState(argv):
	"""Sets boot state of a node."""

	global api, auth
	if len(argv) < 1:
		printUsage("not enough arguments")
		sys.exit(1)
		
	if len(argv) >=1:
		nodename = argv[0]
	if len(argv) >=2:
		state = argv[1]

	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	node = api.GetNodes(auth, [nodename], ['node_id','boot_state'])
	if len(node) == 1:
		node = node[0]
		try:
			logger.info("%s boot_state=%s" %(nodename, node['boot_state']))
			if len(argv) >=2 and not config.debug:
				logger.info("Setting node %s boot_state=%s" %(nodename, state))
				node_id = node['node_id']
				api.UpdateNode(auth, node_id, {'boot_state': state})
		except Exception, exc:
			logger.info("nodeBootState:  %s" % exc)
	else:
		logger.info("Cant find node %s to toggle boot state" % nodename)


def nodePOD(argv):
	"""Sends Ping Of Death to node."""

	global api, auth
	if len(argv) < 1:
		printUsage("not enough arguments")
		sys.exit(1)
		
	nodename = argv[0]
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	node = api.GetNodes(auth, [nodename], ['node_id'])
	if len(node) == 1:
		node = node[0]
		logger.info("Sending POD to %s" % nodename)
		try:
			if not config.debug:
				api.RebootNode(auth, node['node_id'])
		except Exception, exc:
			logger.info("nodePOD:  %s" % exc)
	else:
		logger.info("Cant find node %s to send POD." % nodename)

def suspendSlice(argv):
	"""Freeze specific slice."""
	global api, auth
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	slice = argv[0]
	logger.info("Suspending slice %s" % slice)
	try:
		if not config.debug:
			api.AddSliceAttribute(auth, slice, "enabled", "0")
	except Exception, exc:
		logger.info("suspendSlices:  %s" % exc)

def suspendSlices(argv):
	"""Freeze all site slices."""
	global api, auth
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	if argv[0].find(".") <> -1: siteslices = slices([siteId(argv)])
	else: siteslices = slices(argv)

	for slice in siteslices:
		suspendSlice([slice])

def __enableSlice(slice):
	logger.info("unfreezing slice %s" % slice['name'])
	slice_attributes = api.GetSliceAttributes(auth,slice['slice_attribute_ids'])
	for slice_attribute in slice_attributes:
		if slice_attribute['name'] == "enabled":
			api.DeleteSliceAttribute(auth, slice_attribute['slice_attribute_id'])
	
def enableSlice(arg):
	"""Enable suspended slice."""
	global api, auth
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	slicename = arg[0]
	gSlices = {'name':slicename}
	slice = api.GetSlices(auth,gSlices)
	if len(slice) == 1:
		__enableSlice(slice[0])
	else:
		logger.info("slice %s not found" % slicename)

def enableSlices(argv):
	"""Enable suspended site slices."""

	global api, auth
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	if argv[0].find(".") <> -1:
		slices = api.GetSlices(auth,[siteId(argv)])
	else:
		gSlices = {'name':"%s_*"%argv[0]}
		slices = api.GetSlices(auth,gSlices)

	for slice in slices:
		__enableSlice(slice)

def setSliceMax(argv):
	"""Set max_slices for Slice. Returns previous max_slices"""
	global api, auth
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	name = argv[0]
	val = int(argv[1])
	if name.find(".") <> -1:
		site_ids = api.GetNodes(auth, [name], ['site_id'])
		if len(site_ids) == 1:
			site_id = [site_ids[0]['site_id']]
			loginbase = api.GetSites (auth, site_id, ["login_base"])
		else:
			printUsage("invalid hostname %s" % name)
			sys.exit(1)
	else:
		site_ids = api.GetSites(auth, {'login_base': "%s" % name}, ['site_id'])
		if len(site_ids) == 1:
			siteid = site_ids[0]['site_id']
		loginbase = name

	numslices = api.GetSites(auth, [siteid], ["max_slices"])[0]['max_slices']
	try:
		api.UpdateSite(auth, siteid, {'max_slices': val})
		logger.info("_SetSliceMax:  %s max_slices was %d set to %d" % (loginbase,numslices,val))
		return numslices
	except Exception, exc:
		logger.info("_SetSliceMax:  %s" % exc)


def authCheck(arg):
	"""Enable suspended slice."""
	global api, auth
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	if len(arg) != 2:
		printUsage("incorrect arguments")
		sys.exit(1)
	user= arg[0]
	pwd = arg[1]
	
	check = {}
	check['Username'] = user
	check['AuthMethod'] = "password"
	check['AuthString'] = pwd
	for role in ['user','tech','pi','admin']:
		check['Role'] = role
		res = api.AdmAuthCheck(check)
		print "%s -> %s %d" % (user,role,res)


def cleanSlices(arg):
	"""Remove all disabled/deleted users from all slices."""
	disabledUsers = {'enabled':False}
	persons = api.GetPersons(auth,disabledUsers,['enabled','slice_ids','email','person_id'])
	for person in persons:
		assert (person['enabled']==False)
		person_id = person['person_id']
		if len(person['slice_ids'])>0:
			for slice_id in person['slice_ids']:
				print "deleting slice %d from %s" % (slice_id,person['email'])
				api.DeletePersonFromSlice(auth,person_id,slice_id)



USAGE = """
Usage: %s [-u user] [-p password] [-r role] CMD

Options:
-u      PLC account username
-p      PLC account password
-r      PLC account role
-h      This message
""" % sys.argv[0]

def printUsage(error = None):
	global funclist
	if error <> None:
		print "%s %s" %(sys.argv[0],error)
	print USAGE
	print "CMD:"
	for name,function in funclist:
		print "%20s\t%20s" % (name, function.__doc__)
	
def main():
	global api, auth

	auth = None
	user = None
	password = None
	role = 'admin'

	(opts, argv) = getopt.getopt(sys.argv[1:], "u:p:r:h")
	if len(argv)==0:
		printUsage()
		sys.exit(1)

	for (opt, optval) in opts:
		if opt == '-u':
			user = optval
		elif opt == '-p':
			password = optval
		elif opt == '-r':
			role = optval
		elif opt == '-h':
			print USAGE
			sys.exit(0)

	if user <> None:
		if password is None:
			try:
				password = getpass.getpass()
			except (EOFError, KeyboardInterrupt):
				print( "" )
				sys.exit(1)
		auth = {}
		auth['Username'] = user
		auth['AuthMethod'] = "password"
		auth['AuthString'] = password
		auth['Role'] = role

	cmd = functbl.get(argv[0], None)
	if cmd is None:
		printUsage()
		sys.exit(1)

	logger.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter('logger - %(message)s')
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	result = cmd(argv[1:])
	if result <> None:
		if argv[0] == "nodesDbg":
			for n in result:
				print n
		else:
			print result

funclist = (("nodesDbg",nodesDbg),
	    ("siteId", siteId),
	    ("slices", slices),
	    ("pcu", getpcu),
	    ("siteNodes", getSiteNodes),
	    ("nodeBootState", nodeBootState),
	    ("nodePOD", nodePOD),
	    ("freezeSlice", suspendSlice),
	    ("unfreezeSlice", enableSlice),
	    ("freezeSlices", suspendSlices),
	    ("unfreezeSlices", enableSlices),
	    ("setSliceMax", setSliceMax),
	    ("authCheck", authCheck),
	    ("cleanSlices", cleanSlices),
	    ("renewAllSlices", renewAllSlices))

functbl = {}
for f in funclist:
	functbl[f[0]]=f[1]

if __name__=="__main__":
	import reboot
	main() 
