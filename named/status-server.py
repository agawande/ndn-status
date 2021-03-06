
#!/usr/bin/python
#coding=utf-8

############
# Imports. #
############
import sys
sys.path.append('/usr/local/lib/python2.7/dist-packages/PyNDN-2.0a3-py2.7.egg/pyndn')  #'/usr/local/lib/python2.7/dist-packages/PyNDN-2.0a3-py2.7.egg/pyndn
import socket
import time
import pyndn
from pyndn import Face
from pyndn import Name
from pyndn import Data
from pyndn.security import KeyChain
from pyndn.util import Common
import multiprocessing
from collections import defaultdict
import datetime
import logging
import threading

################################################
# Delcaring and initializing needed variables. #
################################################
localdir = '/home/op_mhoque/nlsr-status/ndn-status/named'

links_list = []

prefix_timestamp = {}
link_timestamp = {}
host_name = {}
topology  = {}

set_topology = defaultdict(set)
router_links  = defaultdict(set)
router_prefixes = defaultdict(set)

logging.basicConfig(filename='process.log', level=logging.DEBUG)
logging.debug('Starting')

g_responseCount = 0

LINK_STATUS_NAME     = Name('/ndn/memphis.edu/internal/status/link')
METADATA_STATUS_NAME = Name('/ndn/memphis.edu/internal/status/metadata')
PREFIX_STATUS_NAME   = Name('/ndn/memphis.edu/internal/status/prefix')

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
    #print(result)

class StatusServer(object):
    def __init__(self):
        self._face = Face()
        self._keyChain = KeyChain()
        #print(dir(self._keyChain))
        self._certificateName = self._keyChain.getDefaultCertificateName()
        self.registerWithNfd()
        #self.nfdCheck()

    def registerWithNfd(self):
        #self._face = Face()
        # Use the system default key chain and certificate name to sign commands.
        self._face.setCommandSigningInfo(self._keyChain, self._certificateName)

        logging.debug('Register prefix ' + LINK_STATUS_NAME.toUri())
        self._face.registerPrefix(LINK_STATUS_NAME, self.onLinkInterest, self.onRegisterFailed)

        logging.debug('Register prefix ' + METADATA_STATUS_NAME.toUri())
        self._face.registerPrefix(METADATA_STATUS_NAME, self.onMetaDataInterest, self.onRegisterFailed)

        logging.debug('Register prefix ' + PREFIX_STATUS_NAME.toUri())
        self._face.registerPrefix(PREFIX_STATUS_NAME, self.onPrefixInterest, self.onRegisterFailed)

    def onLinkInterest(self, prefix, interest, face, registeredPrefixId, filter):
        self._linkData = getLinkData()
        logging.debug('Received interest for Link')
        self.sendData(prefix, interest, face, registeredPrefixId, self._linkData)

    def onMetaDataInterest(self, prefix, interest, face, registeredPrefixId, filter):
        print("on meta interest")
        print("interest rcvd for: ", interest.getName().toUri())
        print("interest must be fresh value: ", interest.getMustBeFresh())
        processFiles()
        self._metaData = processAndGetMetaData()
        logging.debug('Received interest for Metadata')
        self.sendData(prefix, interest, face, registeredPrefixId, self._metaData)
        print("Data send")

    def onPrefixInterest(self, prefix, interest, transport, registeredPrefixId, filter):

        self._prefixData = getPrefixData()
        logging.debug('Received interest for Prefix')
        self.sendData(prefix, interest, transport, registeredPrefixId, self._prefixData)

    def sendData(self, prefix, interest, face, registeredPrefixId, content):      #onInterest

        #transport.send(encodedData.toBuffer())
	#print(prefix)
        # Publish segments
        dataSize = len(content)
        print("Dat size: ",dataSize)
        segmentBegin = 0
        segmentNo = 0
        print "Start"
        while segmentBegin < dataSize: 
            segmentEnd = segmentBegin + 2000 #Common.MAX_NDN_PACKET_SIZE

            if segmentEnd > dataSize:
                segmentEnd = dataSize

            # Make and sign a Data packet.
	    print("Prefix: ")
	    print(prefix)
            if not "%" in str(prefix)[-7:]:
                segmentName = prefix
		#print("NO % in name: ", segmentName)
                segmentName.appendSegment(segmentNo)
            else:
                segmentName = str(prefix)[:-1]
                #print("% in name: ",segmentName)
		segmentName += str(segmentNo)
		segmentName = Name(segmentName)
            print("Segment Name: ")
	    print(segmentName)

            print("Segment Name appended: ", segmentName)

            print "Segmenting data from %d to %d" % (segmentBegin, segmentEnd)
            print("COntent: ")
            print(content[segmentBegin:segmentEnd])

            data = Data(segmentName)
            data.setContent(content[segmentBegin:segmentEnd])
            data.getMetaInfo().setFreshnessPeriod(2000)
            self._keyChain.sign(data, self._certificateName)

            if segmentEnd >= dataSize:
              print("yes")
              data.getMetaInfo().setFinalBlockId(segmentName[-1])

            #encodedData = data.wireEncode()

            segmentBegin = segmentEnd

            print "Sending data " + segmentName.toUri()
            #transport.send(encodedData.toBuffer())
            face.putData(data)

            segmentNo += 1
            time.sleep(0.5)
        print "Finish"

    def onRegisterFailed(self, prefix):
        dump("Register failed for prefix", prefix.toUri())

    def nfdCheck(self):
	try:
            try:
                output=subprocess.check_output('nfd-status | grep memphis.edu/internal', shell=True)
            except subprocess.CalledProcessError,e:
                output=e.output
            print("output", output)	
	    if "memphis.edu/internal" not in output:
	        try:
                    self.registerWithNfd()
		    threading.Timer(1, self.nfdCheck).start()
		    self.run()
                except:
	            pass
            else:
	         pass
        except:
	    pass
	threading.Timer(1, self.nfdCheck).start()

    def run(self):
        while True:
            #print("true")
            self._face.processEvents()
            # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
            time.sleep(0.01)

        self._face.shutdown()
        

##############################
# Functions to process data. #
##############################
def getPrefixData():
  publish = []
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
  #print data
  return data

def getLinkData():
  publish = []  
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
  #print data
  return data

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
def processAndGetMetaData():
  publish = [] 
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

  publish.append('{"lastlog":"' + lastfile + '",')
  publish.append('"lasttimestamp":"' + timestamp + '",')
  publish.append('"lastupdated":"' + curtime + '"}')
  data = ''.join(publish)
  #print data
  return data


######################################################
# Read in prefixes, links, timestamps, and topology. #
######################################################
def processFiles():
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
	    #print line
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

if __name__ == "__main__":
  server = StatusServer()
  server.run()
