#!/usr/bin/python
# -*- coding:utf-8 -*-
import csv
import os
import sys
import time
import platform
import subprocess
import shutil
import xmlrpclib
import logging
import zipfile

if os.name == 'nt':
   import win32con
   import win32file
   import pywintypes
   LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
   LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
   # Lock file
   lockfp = open(r'C:\Users\Public\svr.lock', 'w')
   def lock():
      hfile = win32file._get_osfhandle(lockfp.fileno())
      try:
         print('>>> Locking...')
         win32file.LockFileEx(hfile, LOCK_EX | LOCK_NB,
                              0, -0x10000, pywintypes.OVERLAPPED())
      except pywintypes.error:
         print('>>> Server.py is already running...')
         sys.exit(1)
elif os.name == 'posix':
   import fcntl
   LOCK_EX = fcntl.LOCK_EX
   LOCK_NB = fcntl.LOCK_NB
   # Lock file
   lockfp = open(os.path.expanduser(r'~/svr.lock'), 'w')
   def lock():
      try:
         print('>>> Locking...')
         fcntl.lockf(lockfp.fileno(), LOCK_EX | LOCK_NB)
      except IOError:
         print('>>> Server.py is already running...')
         sys.exit(1)

def GetServerOS():
   """
   Detect the server OS:
   Linux, Mac, NT etc.

   """
   if os.sep == '\\' and os.linesep == '\r\n':
      clientOS = 'NT'
   if os.sep == '/' and os.linesep == '\n':
      clientOS = 'Linux'
   if not clientOS:
      raise Exception('Unknow client OS.')
   return clientOS

sServerOS = GetServerOS()
if sServerOS == 'NT':
   rxAPIAutoSvrLog = r'c:\rx-api-auto-svr.log'
   resultFile = r'c:\tools\result.log'
elif sServerOS == 'Linux':
   rxAPIAutoSvrLog = r'/home/tools/rx-api-auto-svr.log'
   resultFile = r'/home/tools/result.log'

from SimpleXMLRPCServer import SimpleXMLRPCServer
from urllib import urlopen, urlretrieve
from xml.parsers import expat

# Logging
logger = logging.getLogger('RX-API')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler(rxAPIAutoSvrLog)
fh.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)


dllURLs = []
testBinariesFolder = r'\\10.117.41.125\share\jenkins\TestBinaries'


def connected():
   toolsFolder = os.path.dirname(resultFile)
   if not os.path.exists(toolsFolder):
      os.mkdir(toolsFolder)
   return True


def call(cmd):
   subprocess.call(cmd)
   return True


def Popen(cmd, myCwd = None, asyncMode = False):
   #resultFile = r'c:\tools\result.log'
   logger.info(cmd)
   if asyncMode:
      subprocess.Popen(cmd, cwd = myCwd, shell = True)
      return True
   p = subprocess.Popen(cmd, cwd = myCwd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
#   while if p.poll() == None::
#      consoleOutput = p.stdout.readline()
#      logger.info(consoleOutput)
#      with open(resultFile, 'ab') as fp:
#         fp.write(consoleOutput)
   stdout, stderr = p.communicate()
   logger.info(stdout)
   with open(resultFile, 'ab') as fp:
      if isinstance(cmd, list):
         for c in cmd:
            fp.write("%s\n" % c)
      else:
         fp.write("%s\n" % cmd)
      fp.write(stdout)
   return True


def sendResultLog():
   #resultFile = r'c:\tools\result.log'
   with open(resultFile, 'rb') as fp:
      return xmlrpclib.Binary(fp.read())


def receiveFile(filePath, binData):
   with open(filePath, 'wb') as fp:
      fp.write(binData.data)
   if not os.path.exists(filePath):
      logger.error('Receive file failed...')
      return False
   return True


def renameResultLog(logName):
   #resultFile = r'c:\tools\result.log'
   if os.path.exists(logName):
      os.remove(logName)
   if os.path.exists(resultFile):
      os.rename(resultFile, logName)
   if not os.path.exists(logName):
      logger.error('Rename result log failed...')


def downloadTestBinariesAgentWin():
   toolsFolder = r'c:\tools'
   # sourceVdpServerDLL = r'C:\Program Files\Common Files\VMware\Teradici PCoIP Server\vdpService.dll'
   subprocess.call(r'net use %s /user:administrator' % testBinariesFolder)
   if not os.path.exists(toolsFolder):
      os.mkdir(toolsFolder)
   subprocess.call(r'xcopy %s\agent\common\* %s /R /Y' % (testBinariesFolder, toolsFolder))
   if "PROGRAMFILES(x86)" not in os.environ:
      subprocess.call(r'xcopy %s\agent\x86\* %s /R /Y' % (testBinariesFolder, toolsFolder))
   else:
      subprocess.call(r'xcopy %s\agent\x64\* %s /R /Y' % (testBinariesFolder, toolsFolder))
   return True

def downloadTestBinariesAgentLinux():
   toolsFolder = r'/home/tools'
   subprocess.call(r'sudo cp /mnt/jenkins/TestBinaries/agent/x64/linux/* /home/tools/', shell = True)
   return True


def downloadRDPTestFilesWin(shareFolder):
   testFilesFolder = r'c:\tools\RDPTestFiles'
   # Create RDPTestFiles folder
   if not os.path.exists(testFilesFolder):
      os.mkdir(testFilesFolder)
   # Copy test files
   subprocess.call(r'xcopy %s\TestFiles\RDPTestFiles\* %s /Y' % (shareFolder, testFilesFolder))
   return True


if __name__ == '__main__':
   lock()
   s = SimpleXMLRPCServer(('0.0.0.0', 8000), allow_none=True)
   s.register_function(connected)
   s.register_function(Popen)
   s.register_function(sendResultLog)
   s.register_function(receiveFile)
   s.register_function(renameResultLog)
   s.register_function(call)
   s.serve_forever()
