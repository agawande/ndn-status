ndn-status - Scripts to parse NLSR logs
==========

Introduction
------------
This repo provides scripts that parse NLSR logs and publish the data as content. The child branch (web branch, of this repo), provides a web page that retrieves this data and displays it visually.


Dependencies
------------
To run the scripts, the following dependencies are required:

* python2.7
* pyNDN2
* ndn.js(see other branch for details)
* NFD


Setting up the scripts
----------------------
To set up the scripts, cd into the cloned directory and run the configure script.

    ./configure
    
This will ask you to enter in the directory of the NLSR logs, and the prefix you would like to publish the content under.

Running the scripts
-------------------
To run the scripts, simply run:

    python status.py
    
The status data will be generated and published using the prefix you specified, publish_prefix, with the following identifiers added at the end:

1. prefix information:
> publish_prefix/status

2. link information:
> publish_prefix/link

3. metadata information:
> publish_prefix/metadata

How the current status page works
---------------------------------

