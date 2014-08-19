#!/usr/bin/env python

import os

parse = []
process = []
notify = []

with open('parse.py') as f:
	for line in f:
		parse.append(line)

with open('process.py') as f:
	for line in f:
		process.append(line)

with open('notify.py') as f:
	for line in f:
		notify.append(line)

localdir = os.getcwd()
logdir = raw_input('Path to ospfn logs: (exclude the trailing "/")\n>> ')
prefix = raw_input('Prefix to publish under (i.e. /ndn/netlab/status)\n>> ')

with open('parse.py', 'w') as f:
	for line in parse:
		if 'localdir =' in line:
			f.write('localdir = \'' + localdir + '\'\n')
		elif 'pubprefix = ' in line:
			f.write('pubprefix = \'' + prefix + '\'\n')
		else:
			f.write(line)
			
with open('process.py', 'w') as f:
	for line in process:
		if 'localdir =' in line:
			f.write('localdir = \'' + localdir + '\'\n')
		elif 'pubprefix = ' in line:
			f.write('pubprefix = \'' + prefix + '\'\n')
		else:
			f.write(line)

with open('notify.py', 'w') as f:
        for line in notify:
                if 'LOCAL_DIR =' in line:
                        f.write('LOCAL_DIR = \'' + localdir + '\'\n')
                else:
                        f.write(line)

with open('parse.conf', 'w') as f:
	f.write('logdir=' + logdir + '\n')
	f.write('lastfile=0\n')
	f.write('lasttimestamp=0\n')
	f.write('lastbyte=0\n')
	f.write('timetaken=0\n')
	f.write('timzone=CST\n')
	f.write('logtag=nlsr_\n')
os.system("python createtopology.py")
os.system("rm prefix links link_timestamp")
os.system("touch prefix links link_timestamp")