#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import time
import subprocess
from xmlrpclib import ServerProxy

# Import self modules
import core

from log import logger
from xml.etree import ElementTree

def disableCertCheckWin():
   logger.info('Disabling wwwwclient cert checking...')
   filePath = os.path.join(os.environ['APPDATA'],
         r'VMware\VMware Horizon View Client\prefs.txt')
   if not os.path.exists(os.path.dirname(filePath)):
      os.makedirs(os.path.dirname(filePath))
   if not os.path.exists(filePath):
      logger.warn('File prefs.txt not found, create new one...')
      prefsWords = '<Root><SecurityMode certCheckMode="2" /></Root>'
      with open(filePath, 'wb') as fp:
         fp.write(prefsWords)
      logger.info('Now SecurityMode has been changed to 2 ...')
   else:
      xmlDoc = ElementTree.parse(filePath)
      root = xmlDoc.getroot()
      # Search SecurityMode
      node = root.find('SecurityMode')
      certAttr = {}
      if node != None:
         node.set('certCheckMode', '2')
      else:
         certAttr['certCheckMode'] = '2'
         ElementTree.SubElement(root, 'SecurityMode', certAttr)
         # Write back to prefs.txt
         xmlDoc.write(filePath)
      # Checking
      node = root.find('SecurityMode')
      logger.info("Now SecurityMode has been changed to %s..." % node.attrib)
   return True

def disableBlastSSLCheckWin():
   logger.info('Disabling blast SSL checking...')
   folder = os.path.join(os.environ['APPDATA'], r'VMware')
   configFile = os.path.join(folder, r'config.ini')
   if not os.path.exists(folder):
      os.mkdir(folder)
   with open(configFile, 'wb') as fp:
      fp.write('RemoteDisplay.permitUnverifiedWebSocketSSL=TRUE')
   return True

def getProcessCountWin(imageName):
   p = os.popen('tasklist /FI "IMAGENAME eq %s"' % imageName)
   return p.read().count(imageName)

def disableCertCheckLinux():
   logger.info('Disabling wwwwclient cert checking...')
   cfgString = '''
wwww.defaultLogLevel = "0"
vdpServiceClient.log.logMinLevel = 8142
wwww.sslVerificationMode = "3"
'''
   configDir = os.path.join(os.path.expanduser('~'),
                            core.Conf['certConfigDirLinux'])
   configFileUser = os.path.join(configDir, core.Conf['certConfigFileLinux'])
   if not os.path.exists(configDir):
      os.makedirs(configDir)
   if not os.path.exists(configFileUser):
      logger.warn("%s not exsits..." % configFileUser)
   with open(configFileUser, 'w') as fp:
      fp.write(cfgString)
   if os.path.exists(configFileUser):
      logger.info("Disable wwwwclient cert checking successfully...")
   else:
      logger.error('Cannot find related configuration file...')

def disableCertCheckMac():
   logger.info('Disabling wwwwclient cert checking...')
   cmd = "defaults write com.vvvvvv.horizon certificateVerificationMode 3"
   subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
   
def getProcessCountLinux(imageName):
   p = os.popen('ps -eo comm')
   return p.read().count(imageName)

def connectRPCServer():
   # Action on Agent
   agentIp = core.Conf['defaultConfig']['agentip']
   logger.info('Connecting RPC server in agent %s:8000' % agentIp)
   timeout = 600
   startTime = time.time()
   while True:
      try:
         core.Conf['proxy'] = ServerProxy(('http://%s:8000' % agentIp),
                                          allow_none = True)
         core.Conf['proxy'].connected()
         break
      except Exception, err:
         if time.time() - startTime < timeout:
            time.sleep(60)
            continue
         else:
            logger.error('Connect to RPC Server timeout...')
            return False
   return True

def mountToolchain():
   os.system(r'net use n: /delete')
   os.system(r'net use n: \\build-toolchain.eng.vvvvvv.com\toolchain /persistent:yes /user:VMWAREM\mts-automation U9NqLq11qjd2u7T')

class FakeSecHeader():
   '''
   [Fake Section Header]
   This class is used for configuration parser without section header.
   '''
   def __init__(self, fp):
      self.fp = fp
      self.secheader = '[asection]\n'

   def readline(self):
      if self.secheader:
         try:
            return self.secheader
         finally:
            self.secheader = None
      else:
         return self.fp.readline()
