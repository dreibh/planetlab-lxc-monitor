#!/usr/bin/python2
#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: mailer.py,v 1.9 2007/07/03 19:57:16 soltesz Exp $
from emailTxt import *
import smtplib
from config import config
import logging
import os
import time

config = config()
logger = logging.getLogger("monitor")

MTA="localhost"
FROM="monitor@planet-lab.org"

def reformat_for_rt(text):
	lines = text.split("\n")
	spaced_text = ""
	for line in lines:
		spaced_text += " %s\n" %line
	return spaced_text
		

def _setupRTenvironment():
	os.environ['PATH'] = os.environ['PATH'] + ":/home/soltesz/rpm/opt/rt3/bin/"
	os.environ['RTSERVER'] = "https://rt.planet-lab.org/"
	os.environ['RTUSER']   = "monitor"
	os.environ['RTPASSWD'] = "ssorcmor"
	os.environ['RTDEBUG'] = "0"
	return

def setAdminCCViaRT(ticket_id, to):
	# Set ENV Variables/PATH
	_setupRTenvironment()
	if ticket_id == None or ticket_id == "":
		raise Exception("ERROR: ticket_id must be set to some integer value")

	# This will raise an exception if it is not a valid id.
	i_ticket_id = int(ticket_id)

	# create a comma-separated list
	s_to = ",".join(to)
	cmd = "rt edit ticket/%s set admincc='%s'" % (ticket_id, s_to)
	(f_in, f_out, f_err) = os.popen3(cmd)
	value = f_out.read()
	l_values = value.split()
	f_in.close() ; f_out.close() ; f_err.close()
	if len(l_values) > 3 and "updated" in l_values[3]:
		# Success
		pass
	else:
		print "ERROR: RT failed to update AdminCC for ticket %s" % ticket_id

	return

def setSubjectViaRT(ticket_id, subject):
	# Set ENV Variables/PATH
	_setupRTenvironment()
	if ticket_id == None or ticket_id == "":
		raise Exception("ERROR: ticket_id must be set to some integer value")

	# This will raise an exception if it is not a valid id.
	i_ticket_id = int(ticket_id)

	cmd = "rt edit ticket/%s set subject='%s'" % (ticket_id, subject)
	(f_in, f_out, f_err) = os.popen3(cmd)
	value = f_out.read()
	l_values = value.split()
	f_in.close() ; f_out.close() ; f_err.close()
	if len(l_values) > 3 and "updated" in l_values[3]:
		# Success
		pass
	else:
		print "ERROR: RT failed to update subject for ticket %s" % ticket_id

	return
		

def addCommentViaRT(ticket_id, comment):
	# Set ENV Variables/PATH
	_setupRTenvironment()
	if ticket_id == None or ticket_id == "":
		raise Exception("ERROR: ticket_id must be set to some integer value")

	# This will raise an exception if it is not a valid id.
	i_ticket_id = int(ticket_id)

	cmd = "rt comment -m '%s' ticket/%s" % (comment, i_ticket_id)
	(f_in, f_out, f_err) = os.popen3(cmd)
	value = f_out.read()
	l_values = value.split()
	f_in.close() ; f_out.close() ; f_err.close()
	if len(l_values) > 1 and "recorded" in l_values[1]:
		# Success
		pass
	else:
		# Error
		f_in.close() ; f_out.close() ; f_err.close()
		print "ERROR: RT failed to add comment to id %s" % ticket_id

	return

def closeTicketViaRT(ticket_id, comment):
	# Set ENV Variables/PATH
	_setupRTenvironment()
	if ticket_id == None or ticket_id == "":
		raise Exception("ERROR: ticket_id must be set to some integer value")

	# This will raise an exception if it is not a valid id.
	i_ticket_id = int(ticket_id)

	# Append comment to RT ticket
	addCommentViaRT(ticket_id, comment)

	if not config.debug:
		cmd = "rt edit ticket/%s set status=resolved" % i_ticket_id
		(f_in, f_out, f_err) = os.popen3(cmd)
		f_in.close()
		value = f_out.read()
		f_out.close()
		f_err.close()
		l_values = value.split()
		if len(l_values) >= 4 and "updated" in l_values[3]:
			# Success!!
			pass
		else:
			# Failed!!
			print "FAILED to resolve Ticket %d" % ticket_id
			print "FAILED to resolve Ticket %d" % i_ticket_id

	return

def emailViaRT(subject, text, to, ticket_id=None):
	if ticket_id == None or ticket_id == "":
		return emailViaRT_NoTicket(subject, text, to)
		

	# Set ENV Variables/PATH
	_setupRTenvironment()

	if config.mail and not config.debug:
		setSubjectViaRT(ticket_id, subject)
		setAdminCCViaRT(ticket_id, to)

		cmd = "rt correspond -m - %s" % ticket_id
		(f_in, f_out, f_err) = os.popen3(cmd)
		f_in.write(text)
		f_in.flush()
		f_in.close()
		value = f_out.read()

		# TODO: rt doesn't write to stderr on error!!!
		if value == "":
			raise Exception, f_err.read()

		del f_in
		f_out.close(); del f_out
		f_err.close(); del f_err
		os.wait()

	return ticket_id
	

def emailViaRT_NoTicket(subject, text, to):
	"""Use RT command line tools to send email.
		return the generated RT ticket ID number.
	"""
	i_ticket = 0

	if config.mail and config.debug:
   		to = [config.email]

	# Set ENV Variables/PATH
	_setupRTenvironment()

	# NOTE: AdminCc: (in PLC's RT configuration) gets an email sent.
	# This is not the case (surprisingly) for Cc:
	input_text  = "Subject: %s\n"
	input_text += "Requestor: monitor@planet-lab.org\n"
	input_text += "id: ticket/new\n"
	input_text += "Queue: Monitor\n"
	for recipient in to:
		input_text += "AdminCc: %s\n" % recipient
	input_text += "Text: %s"

	# Add a space for each new line to get RT to accept the file.
	spaced_text = reformat_for_rt(text)

	if config.mail and not config.debug:
		cmd = "rt create -i -t ticket"
		(f_in, f_out, f_err) = os.popen3(cmd)
		f_in.write(input_text % (subject, spaced_text))
		f_in.flush()
		f_in.close()
		value = f_out.read()

		# TODO: rt doesn't write to stderr on error!!!
		if value == "":
			raise Exception, f_err.read()

		print "MAILER: ticket value == %s" % value.split()[2]
		i_ticket = int(value.split()[2])
		# clean up the child process.
		f_in.close();  del f_in
		f_out.close(); del f_out
		f_err.close(); del f_err
		os.wait()
	elif config.mail and config.debug:
		email(subject, spaced_text, to)
		i_ticket = 0
	else:
		i_ticket = 0

	return i_ticket

def email(subject, text, to):
	"""Create a mime-message that will render HTML in popular
	MUAs, text in better ones"""
	import MimeWriter
	import mimetools
	import cStringIO

	if (config.mail and config.debug) or (not config.mail and not config.debug and config.bcc):
   		to = [config.email]

	out = cStringIO.StringIO() # output buffer for our message 
	txtin = cStringIO.StringIO(text)

	writer = MimeWriter.MimeWriter(out)
	#
	# set up some basic headers... we put subject here
	# because smtplib.sendmail expects it to be in the
	# message body
	#
	writer.addheader("Subject", subject)
	if to.__class__ == [].__class__ :	
		writer.addheader("To", to[0])
		cc = ""
		for dest in to[1:len(to)]:
			cc +="%s, " % dest
		cc = cc.rstrip(", ") 
		writer.addheader("Cc", cc)
	else:
		writer.addheader("To", to)

	if config.bcc and not config.debug:
		writer.addheader("Bcc", config.email)

	writer.addheader("Reply-To", 'monitor@planet-lab.org')
		
	writer.addheader("MIME-Version", "1.0")
	#
	# start the multipart section of the message
	# multipart/alternative seems to work better
	# on some MUAs than multipart/mixed
	#
	writer.startmultipartbody("alternative")
	writer.flushheaders()
	#
	# the plain text section
	#
	subpart = writer.nextpart()
	subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
	pout = subpart.startbody("text/plain", [("charset", 'us-ascii')])
	mimetools.encode(txtin, pout, 'quoted-printable')
	txtin.close()
	#
	# Now that we're done, close our writer and
	# return the message body
	#
	writer.lastpart()
	msg = out.getvalue()
	out.close()

	# three cases:
	# 	mail but no-debug
	#	mail and debug, 'to' changed at the beginning'
	#   nomail, but report who I'd send to.
	if config.mail:
		try:
			# This is normal operation
			server = smtplib.SMTP(MTA)
			server.sendmail(FROM, to,  msg)
			if config.bcc and not config.debug:
				server.sendmail(FROM, config.email,  msg)
			server.quit()
		except Exception, err:
			print "Mailer error: %s" % err
	elif not config.debug and not config.mail and config.bcc:
		try:
			server = smtplib.SMTP(MTA)
			server.sendmail(FROM, to,  msg)
			server.quit()
		except Exception, err:
			print "Mailer error: %s" % err
	else:
		#print "Would mail %s" %to
		logger.debug("Would send mail to %s" % to)

if __name__=="__main__":
	import smtplib
	import emailTxt
	import plc 
	#email("[spam] bcc test from golf.cs.princeton.edu", 
	#	  "It gets to both recipients", 
	#	  "soltesz@cs.utk.edu")
	#emailViaRT("rt via golf", 
	#	  "It gets to both recipients", 
	#	  "soltesz@cs.utk.edu")
	email("Re: [PL #21323] TEST 7", 
			   mailtxt.newbootcd_one[1] % {'hostname_list':"hostname list..."},
			   ['monitor@planet-lab.org'])
	#print "ticketid: %d" % id
	#id = plc.siteId(["alice.cs.princeton.edu"])
	#print id
	#if id:
   		#email('TEST', emailTxt.mailtxt.ssh % {'hostname': "ALICE.cs.princeton.edu"}, "tech-" + id + "@sites.planet-lab.org")
	#else:
	#	print "No dice."
	#email("TEST111", "I'd like to see if this works anywhere", ["soltesz@cs.princeton.edu", "soltesz@cs.utk.edu"])
	#print "mailer does nothing in main()"
