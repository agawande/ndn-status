#!/usr/bin/python
 
############
# Imports. #
############
import os
import time
import datetime
from collections import defaultdict

################################################
# Delcaring and initializing needed variables. #
################################################
localdir = '/home/nlsr-status/ndn-status/named'
router_prefixes	 = {}
prefix_timestamp = {}
link_timestamp 	 = {}

router_links	 = defaultdict(set)

#############################################################################################
# Read the configuration file to find the log directory, last log file, and last line read. #
#############################################################################################
with open (localdir + '/parse.conf') as f:
	for line in f:
		line = line.rstrip()
		
		if 'logdir' in line:
			keyword, value = line.split('=', 1)
			logdir = value
			continue

		if 'lastfile' in line:
			keyword, value = line.split('=', 1)
        		lastfile = value
        		lastfilestamp = value.rstrip('.log')
       			continue			

		if 'lasttimestamp' in line:
			keyword, value = line.split('=', 1)
			lasttimestamp = value
			continue

		if 'timezone' in line:
			keyword, value = line.split('=', 1)
			timezone = value
			continue	

		if 'lastbyte' in line:
			keyword, value = line.split('=', 1)
                        lastbyte = int(0)
                        continue
		if 'logtag' in line:
                        keyword, value = line.split('=', 1)                                                                                                                               
                        logtag = value                                                                                                                                                 
                        continue 
			lastbyte = int(0)
			continue
		if 'logtag' in line:
			keyword, value = line.split('=', 1)
			logtag = value
			continue 
###################################
# Read in prefix and links files. #
###################################
with open (localdir + '/prefix') as f:
	for line in f:
		line = line.rstrip()
		if not line: break
		
		prefix, router, timestamp = line.split(':', 2)
		router_prefixes[prefix] = router
		prefix_timestamp[prefix] = timestamp

with open (localdir + '/links') as f:
        while 1:
                line = (f.readline()).rstrip()
                if not line: break

                if 'Router' in line:
                        extra, router = line.split(':', 1)

                        while not 'END' in line:
                                line = (f.readline()).rstrip()
                                if not line: break
                                if 'END' in line: break

                                adj_router = line
                                router_links[router].add(adj_router)
		
with open (localdir + '/link_timestamp') as f:
	for line in f:
		line = line.rstrip()
		if not line: break
		
		router, timestamp = line.split(':', 1)
		link_timestamp[router] = timestamp

# Read in names of all files in the log directory and add them to the file array. 
directory = os.listdir(logdir)
directory.sort();
dir = []

for cur in directory:
	if cur == 'nlsr.log':
		dir.append(cur)
directory = dir

######################################################################################
# Starting with the last file read, jump to the last read byte and continue parsing. #
######################################################################################
for cur in directory:
	if cur[:5] != logtag:       # cur[:5] != logtag
		print cur + " does not have the correct log tag ( nlsr_ )."
		directory.remove(cur)
		break

	if lastfilestamp > cur.rstrip('.log'):
		continue
	
	with open (logdir + '/' + cur) as f:
		if lastfilestamp == cur.rstrip('.log'):
                	f.seek(lastbyte)
		count = 0
		while 1:
			line = (f.readline()).rstrip()
			if not line: break

			left, extra, right = line.partition(':')
			timestamp, extra = left.split(' ', 1)		
			timestamp = str(time.mktime(datetime.datetime.strptime(timestamp, "%Y%m%d%H%M%S%f").timetuple()))
			line = right

			if 'Adding Name Lsa' in line:        #Name-LSA
				while (not 'name_lsa_end' in line):
					#line = (f.readline()).rstrip()
					#if not line: break

					#print line					
					if 'Name 1:' in line:
						while (not 'name_lsa_end' in line):
							extra, prefix = line.split('Name 1: ', 1)
							if router and prefix:
								if action == 'add':
									router_prefixes[prefix] = router
									prefix_timestamp[prefix] = timestamp
								elif action == 'del':
									del router_prefixes[prefix]
									prefix_timestamp[prefix] = timestamp

							line = (f.readline()).rstrip()
							if 'name_lsa_end' in line:break
					
					if 'name_lsa_end' in line:break

					elif 'Origination Router:' in line:
						extra, router = line.split('Router: ', 1)
					elif 'Deleting Name Lsa' in line:
						action = 'del'
					elif 'Adding Name Lsa' in line:
						action = 'add'         

					line = (f.readline()).rstrip()
					if not line:break                          

				if router and prefix:
					# Process the action
					if action == 'add':
						router_prefixes[prefix] = router
						prefix_timestamp[prefix] = timestamp
					elif action == 'del' and router_prefixes.has_key(prefix):
						del router_prefixes[prefix]
						prefix_timestamp[prefix] = timestamp

 
 			elif 'Adding Adj Lsa' in line:               #Adj-LSA
				while (not 'adj_lsa_end' in line):
					#line = (f.readline()).rstrip()
					#if not line: break

					if 'Origination Router:' in line:
						extra, router = line.split('Router: ', 1)
					elif 'Deleting Adj Lsa' in line:
						action = 'del'
					elif 'Adding Adj Lsa' in line:
						action = 'add'
					elif 'Adjacents:' in line:
						#extra, run = line.split('No of Link: ', 1)
						
						'''
						for i in range(0, int(run)):
							for j in range(0, 3):
								line = (f.readline()).rstrip()
								
								if 'Adjacent Name:' in line:
									extra, adj_router = line.split('Name: ', 1)
								#elif 'Connecting Face:' in line:
								#	extra, face = line.split('Face: ', 1)

							if router and adj_router:
								if action == 'add':
									router_links[router].add(adj_router)
								elif action == 'del':
									try:
										router_links[router].remove(adj_router)
									except:
										pass
						'''

						while(not 'adj_lsa_end' in line):
							if 'Adjacent Name:' in line:
								extra, adj_router = line.split('Name: ', 1)

								if router and adj_router:
									if action == 'add':
										router_links[router].add(adj_router)
									elif action == 'del':
										try:
											router_links[router].remove(adj_router)
										except:
											pass
							line = (f.readline()).rstrip()

						if('adj_lsa_end' in line): break

					line = (f.readline()).rstrip()
					if not line: break

				link_timestamp[router] = timestamp

		lasttimestamp = timestamp
		lastbyte = f.tell()

################
# Update files #
################
with open (localdir + '/prefix', 'w') as f:
	for prefix, router in router_prefixes.items():
		timestamp = prefix_timestamp[prefix]
		#t = time.mktime(datetime.datetime.strptime(timestamp, "%Y%m%d%H%M%S%f").timetuple())
		f.write(prefix + ':' + router + ':' + timestamp + '\n')

with open (localdir + '/links', 'w') as f:
	linkinfo = set

	for router, linkinfo in router_links.items():
		f.write('Router:' + router + '\n')
		for adj_router in linkinfo:
			f.write(adj_router + '\n')

		f.write('END\n')

with open (localdir + '/link_timestamp', 'w') as f:
	for router, timestamp in link_timestamp.items():
		#t = time.mktime(datetime.datetime.strptime(timestamp, "%Y%m%d%H%M%S%f").timetuple())
		f.write(router + ':' + timestamp + '\n')

with open (localdir + '/parse.conf', 'w') as f:
	f.write('logdir=' + logdir + '\n')
	f.write('lastfile=' + directory[-1] + '\n')
	f.write('lasttimestamp=' + lasttimestamp + '\n')
	f.write('lastbyte=' + str(lastbyte) + '\n')
	f.write('logtag=' + logtag + '\n')
	f.write('timezone=' + timezone + '\n')
