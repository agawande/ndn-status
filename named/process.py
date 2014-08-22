#!/usr/bin/python
#coding=utf-8

############
# Imports. #
############
import sys
sys.path.append('/usr/local/lib/python2.7/dist-packages/pyndn')
import socket
import time
import pyndn
from pyndn import Face
from pyndn import Name
from pyndn import Data
from pyndn.security import KeyChain
import multiprocessing
from collections import defaultdict
import datetime

################################################
# Delcaring and initializing needed variables. #
################################################
localdir = '/home/ndnuser/named'

links_list = []
publish = []

prefix_timestamp = {}
link_timestamp = {}
host_name = {}
topology  = {}

set_topology = defaultdict(set)
router_links  = defaultdict(set)
router_prefixes	= defaultdict(set)

#####################
# Timeout function. #
#####################
def lookup(host, q):
	q.put(socket.gethostbyaddr(host))

###################################
# pyndn Class to publish content. #
###################################

def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else repr(element)) + " "
    print(result)

class Echo(object):
    def __init__(self, keyChain, certificateName, data):
        self._keyChain = keyChain
        self._certificateName = certificateName
        self._responseCount = 0
        self.data = data

    def onInterest(self, prefix, interest, transport, registeredPrefixId):
        self._responseCount += 1

        # Make and sign a Data packet.
        data = Data(interest.getName())
        content = self.data#interest.getName().toUri()
        data.setContent(content)
        self._keyChain.sign(data, self._certificateName)
        encodedData = data.wireEncode()

        dump("Sent content", content)
        transport.send(encodedData.toBuffer())

    def onRegisterFailed(self, prefix):
        self._responseCount += 1
        dump("Register failed for prefix", prefix.toUri())

def status_put(name, data):
    # The default Face will connect using a Unix socket, or to "localhost".
    face = Face()

    # Use the system default key chain and certificate name to sign commands.
    keyChain = KeyChain()
    face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName())
    
    # Also use the default certificate name to sign data packets.
    echo = Echo(keyChain, keyChain.getDefaultCertificateName(), data)
    prefix = Name(name)
    dump("Register prefix", prefix.toUri())
    face.registerPrefix(prefix, echo.onInterest, echo.onRegisterFailed)
    
    timeout = time.time() + 6    # wait only 6 seconds for interest, otherwise status page can get old data
    while echo._responseCount < 1:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01) 
        if time.time() > timeout:
           break

    face.shutdown()


##############################
# Functions to process data. #
##############################
def prefix_json():
	prefixes = set
	search = list(set(set_topology.keys()) | set(router_prefixes.keys()))

	for router in sorted(search):
		status = 'Online'
		prefixes = router_prefixes[router]

		publish.append('{"router":"' + router + '",')
		publish.append('"prefixes":[')

		if not prefixes:
			router_prefixes[router].add('-')
			status = 'Offline'

		if router not in set_topology.keys():
			status = 'notintopology'

		for prefix in prefixes:
			if not prefix_timestamp.has_key(prefix):
                                timestamp = '-'
			else:
				timestamp = prefix_timestamp[prefix]

			publish.append('{"prefix":"' + prefix + '",')
			publish.append('"timestamp":"' + timestamp + '",')
			publish.append('"status":"' + status + '"}')
			publish.append(',')

		del publish[-1]
		publish.append(']}')
		publish.append('END')
	del publish[-1]

	data = ''.join(publish)
	status_put('/ndn/memphis.edu/internal/status/prefix', data)  #/ndn/memphis.edu/internal/status/prefix
	#put.start()
	del publish[:]
	print data

def link_json():
	links = set
	status = ''
	search = dict(router_links.items() + set_topology.items())

	for router, links in sorted(search.items()):
		if not link_timestamp.has_key(router):
			timestamp = '-'
		else:
			timestamp = link_timestamp[router]
	
		publish.append('{"router":"' + router + '",')
		publish.append('"timestamp":"' + timestamp + '",')
		publish.append('"links":[')

		for link in links:
			if topology[router, link] == 'lime':
                        	status = 'Online'
                	elif topology[router, link] == 'Red':
                        	status = 'Offline'
                	elif topology[router, link] == 'skyblue':
                        	status = 'notintopology'

			#print(link)
			#print(link_timestamp[link])

                	if status == 'Online' and float(time.time() - (float(link_timestamp[link]))) > 2400:
                        	status = 'Out-of-date'

			publish.append('{"link":"' + link + '",')
			publish.append('"status":"' + status + '"}')
			publish.append(',')

		del publish[-1]
		publish.append(']}')
		publish.append('END')
	del publish[-1]

	data = ''.join(publish)
        status_put('/ndn/memphis.edu/internal/status/link', data)
        del publish[:]
	print data

def process_topo():
	links = set
        
	for router, links in router_links.items():
		for link in links:
			if not topology.has_key((router, link)):
				topology[router, link] = 'skyblue'
			else:
				topology[router, link] = 'lime'

#############################################################################################
# Read the configuration file to find the last file timestamp, last timestamp and timezone. #
#############################################################################################
with open (localdir + '/parse.conf') as f:
        for line in f:
                line = line.rstrip()

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

curtime = time.asctime(time.localtime(time.time())) + ' ' + timezone
timestamp = time.asctime(time.localtime(float(lasttimestamp))) + ' ' + timezone
#timestamp = datetime.datetime.strptime(lasttimestamp,'%Y%m%d%H%M%S%f')
#timestamp = str(timestamp) + ' ' + timezone

publish.append('{"lastlog":"' + lastfile + '",')
publish.append('"lasttimestamp":"' + timestamp + '",')
publish.append('"lastupdated":"' + curtime + '"}')
data = ''.join(publish)
status_put('/ndn/memphis.edu/internal/status/metadata', data)
#put.start()
del publish[:]


######################################################
# Read in prefixes, links, timestamps, and topology. #
######################################################
with open (localdir + '/topology') as f:
        while 1:
                line = (f.readline()).rstrip()
                if not line: break

                if 'Router' in line:
                        extra, router = line.split(':', 1)

                        while not 'END' in line:
                                line = (f.readline()).rstrip()
                                if not line: break
                                if 'END' in line: break

                                adj_router, status = line.split(':', 1)
				set_topology[router].add(adj_router)
                                topology[router, adj_router] = status

with open (localdir + '/prefix') as f:
        for line in f:
                line = line.rstrip()
                if not line: break

                prefix, router, timestamp = line.split(':', 2)
                router_prefixes[router].add(prefix)
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

                                link = line
				router_links[router].add(link)

with open (localdir + '/link_timestamp') as f:
	for line in f:
		line = line.rstrip()
		if not line: break

		link, timestamp = line.split(':', 1)
		link_timestamp[link] = timestamp

process_topo()
prefix_json()
publish.append("\n")
link_json()

print 'Completed'

