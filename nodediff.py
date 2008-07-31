#!/usr/bin/python

import sys
import soltesz

from config import config as cfg

def nodes_from_time(time_str):
	path = "archive-pdb"
	archive = soltesz.SPickle(path)
	d = datetime_fromstr(config.fromtime)
	glob_str = "%s*.production.findbad.pkl" % d.strftime("%Y-%m-%d")
	os.chdir(path)
	#print glob_str
	file = glob.glob(glob_str)[0]
	#print "loading %s" % file
	os.chdir("..")
	fb = archive.load(file[:-4])

	nodelist = fb['nodes'].keys()
	nodelist = node_select(config.select, nodelist, fb)
	

def main():
	parser = OptionParser()
	parser.set_defaults(nodeselect=None,)
	parser.add_option("", "--nodeselect", dest="nodeselect", metavar="state=BOOT", 
						help="""Query on the nodes to count""")

	config = cfg(parser)
	config.parse_args()

	time1 = config.args[0]
	time2 = config.args[1]

	s1 = nodes_from_time(time1)
	s2 = nodes_from_time(time2)

# takes two arguments as dates, comparing the number of up nodes from one and
# the other.