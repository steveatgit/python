#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import csv
import time
import pipes
import shutil
import socket
import platform
import subprocess
import signal
import xmlrpclib
import ConfigParser
from threading import Thread, Semaphore
import re
import string
import tarfile


from xmlrpclib import ServerProxy
try:
   import atomac
except ImportError, err:
   pass
try:
   from _winreg import *
except ImportError, err:
   pass
try:
   import win32api, win32con
except ImportError, err:
   pass
   
# Import self modules
import core


from utils.common import getProcessCountWin
from utils.common import getProcessCountLinux
from utils.common import connectRPCServer
from utils.common import FakeSecHeader

from utils.racetrack import UploadBoostLog
from utils.racetrack import UploadJSCDKLog
from utils.racetrack import UploadWebclientLog
from utils.racetrack import UploadXMLLog
from utils.reporter import Reporter
from utils.dlers import Downloader
from utils.mailer import Mailer
from utils.log import logger
from utils.downloadRdesdkDll import *
from utils.libcdk.runtest_libcdk import runtest_libcdk
from utils.urllib2_upload import *
from utils.buildwebutils import Buildweb


class TestRunner():
   '''
   This class is a super class for test runner.
   '''

   def __init__(self):
      self.resultList = []
      self.precheckinResult = 'SUCCESS'

   def __call__(self):
      self.logoffVM()
      self.launch()
      if not self.connectProxySvr():
         sys.exit(2)
      self.configure()
      self.run()
      self.done(core.Conf['testasset'])
      if core.Conf['rtavTestFlag']:
         self.exitView()
         return True
      if core.Conf['testsets'] == []:
         self.allDone()

   def logoffVM(self):
      if not (core.Conf['linuxVDI'].lower() == 'yes'):
         os.system('staf %s process start shell command "shutdown /l /f"' % core.Conf['defaultConfig']['agentip'])
         time.sleep(60)

   def configure(self):
      if not (core.Conf['linuxVDI'].lower() == 'yes'):
         core.Conf['proxy'].downloadTestBinariesAgentWin()
      # proxy.downloadVDPServiceDLL()
      return True

   def launchArgv(self):
      for i in ('user','password','domain','server'):
         if core.Conf.has_key(i) and core.Conf[i]:
            core.Conf['defaultConfig'][i] = core.Conf[i]
      server = core.Conf['defaultConfig']['server']
      user = core.Conf['defaultConfig']['user']
      if os.name == 'nt':
         password = core.Conf['defaultConfig']['password']
      else:
         password =  pipes.quote(core.Conf['defaultConfig']['password'])
      domain = core.Conf['defaultConfig']['domain']
      poolName = core.Conf['defaultConfig']['poolname']
      protocol = core.Conf['defaultConfig']['protocol']
      return (server, user, password, domain, poolName, protocol)

   def launchNativeClient(self, clArgv):
      isClientStarted = False
      if sys.platform.startswith('win'):
         command = ##
      return isClientStarted

   def inputPassword(self):
      self.wwwwclient.windows()[0].Raise()
      self.addlg = self.wwwwclient.windows()[0]
      time.sleep(10)
      self.addlg.groups()[0].findFirst(AXRole='AXTextField', AXRoleDescription='secure text field').AXFocused = True
      self.addlg.groups()[0].findFirst(AXRole='AXTextField', AXRoleDescription='secure text field').setString('AXValue', core.Conf['defaultConfig']['password'])
      time.sleep(2)
      self.addlg.findFirst(AXRole='AXButton', AXTitle='Login').Press()
      time.sleep(20)
      

   def connectProxySvr(self):
      return connectRPCServer()

   def launch(self):
      clArgv = self.launchArgv()
      ret = self.launchNativeClient(clArgv)
      if ret !=  True:
         logger.error('Cannot find remote mks process, launch failed')
         sys.exit(2)
      return True

   def run(self):
      return True

   def receiveResultLog(self, resultLogBaseName):
      logPath = r'c:\tools\vlogs'
      if sys.platform.startswith('linux'):
         logPath = r'/home/tools/vlogs'
      elif sys.platform.startswith('darwin'):
         logPath = r'/jenkins/tools/vlogs'
      resultLog = os.path.join(logPath, resultLogBaseName)
      with open(resultLog, 'wb') as fp:
         data = core.Conf['proxy'].sendResultLog().data
         logger.info(data)
         fp.write(data)
      # Rename the log file in server side
      if (core.Conf['linuxVDI'].lower() == 'yes'):
         resultLogOnServer = os.path.join(r'/home/tools', resultLogBaseName)
      else:
         resultLogOnServer = os.path.join(r'c:\tools', resultLogBaseName)
      core.Conf['proxy'].renameResultLog(resultLogOnServer)
      Reporter(core.Conf['testasset'], resultLog)()

   def sendFileToAgent(self, fileOnClient, fileOnAgent):
      with open(fileOnClient, 'rb') as fp:
         binData = xmlrpclib.Binary(fp.read())
      core.Conf['proxy'].receiveFile(fileOnAgent, binData)

   def sendPreCheckInResult(self, racetrackResult):
      return True

   def uploadLog(self, logPath, protocol):
      ubl = UploadBoostLog(logPath, protocol)
      return ubl()

   def done(self, testName):
      logger.info('[%s] -- Testing Done.' % testName)

   def exitView(self):

   def allDone(self):
      logger.info('Upload results to racetrack server.')
      logPath = r'c:\tools\vlogs'
      protocol = core.Conf['defaultConfig']['protocol']
      if sys.platform.startswith('linux'):
         logPath = r'/home/tools/vlogs'
      elif sys.platform.startswith('darwin'):
         logPath = r'/jenkins/tools/vlogs'
      racetrackResult = self.uploadLog(logPath, protocol)
      # Copy log files to Jenkins workspace
      if os.environ.has_key('WORKSPACE'):
         logger.info('Copy log files to Jenkins workspace.')
         logWSPath = os.path.join(os.environ['WORKSPACE'], os.path.basename(logPath))
         if os.path.exists(logWSPath):
            logger.info('Remove the vlogs folder which is in workspace.')
            shutil.rmtree(logWSPath)
         shutil.copytree(logPath, logWSPath)
      # Exit vvvvvv-wwww
      self.exitView()
      # Send pre check-in result to submitter
      if os.environ.has_key('resultReceiver'):
         self.sendPreCheckInResult(racetrackResult)
      return True

class RDPTestRunner(TestRunner):
      
   def run(self):
      core.Conf['testasset'] = 'rdpvcbridge_test'
      logger.info('[%s] -- Testing Start.' % core.Conf['testasset'])
      core.Conf['testsets'].remove(core.Conf['testasset'])
      resultLogBaseName = core.Conf['testasset'] + '.log'
      core.Conf['proxy'].downloadRDPTestFilesWin(core.Conf['newShareFolder'])
      if sys.platform.startswith('darwin'):
         core.Conf['proxy'].netUseAttic()
      if core.Conf['precheckinBuildNo']:
         #Download vdp_rdpvcbridge.dll from buildweb on agent.
         buildNo = int(core.Conf['precheckinBuildNo'])
         buildTypeOBSB = getBuildTypeOBSB(buildNo)
         buildTypeBetaRelease = getBuildTypeBetaRelease(buildTypeOBSB, buildNo)
         core.Conf['proxy'].downloadRdesdkDLL(buildNo, buildTypeOBSB, buildTypeBetaRelease, 'vdp_rdpvcbridge.dll')
      hostname = socket.gethostname()
      core.Conf['proxy'].generateRDPTestConfigFileAgentWin(core.Conf['defaultConfig']['clientip'], hostname)
      core.Conf['proxy'].Popen(r'c:\tools\rdpvc_Test.exe --log_level=all --report_level=detailed --run_test=*/*P0', r'c:\tools')
      core.Conf['proxy'].Popen(r'c:\tools\rdpvc_Test.exe --log_level=all --report_level=detailed --run_test=*/*P1', r'c:\tools')
      core.Conf['proxy'].Popen(r'c:\tools\rdpvc_Test.exe --log_level=all --report_level=detailed --run_test=*/*P2', r'c:\tools')
      #core.Conf['proxy'].Popen(r'c:\tools\rdpvc_Test.exe --log_level=all --report_level=detailed --run_test=*/*P3', r'c:\tools')
      #core.Conf['proxy'].Popen(r'c:\tools\rdpvc_Test.exe --log_level=all --report_level=detailed --run_test=*/*P4', r'c:\tools')

      if sys.platform.startswith('win'):
         core.Conf['proxy'].Popen(r'c:\tools\DVCTestServer.exe -p 0', r'c:\tools')
         core.Conf['proxy'].Popen(r'c:\tools\DVCTestServer.exe -p 1', r'c:\tools')
      self.receiveResultLog(resultLogBaseName)
      subprocess.call(r'taskkill /F /IM vvvvvv-wwww.exe', shell = True)
      subprocess.call(r'taskkill /F /IM vvvvvv-remotemks.exe', shell = True)
      return True


class RDPPerfTestRunner(TestRunner):

   def run(self):
      core.Conf['testasset'] = 'rdpvcbridge_perftest'
      logger.info('[%s] -- Testing Start.' % core.Conf['testasset'])
      core.Conf['testsets'].remove(core.Conf['testasset'])
      resultLogBaseName = core.Conf['testasset'] + '.log'
      core.Conf['proxy'].downloadRDPTestFilesWin(core.Conf['newShareFolder'])
      if core.Conf['precheckinBuildNo']:
         #Download vdp_rdpvcbridge.dll from buildweb on agent.
         buildNo = int(core.Conf['precheckinBuildNo'])
         buildTypeOBSB = getBuildTypeOBSB(buildNo)
         buildTypeBetaRelease = getBuildTypeBetaRelease(buildTypeOBSB, buildNo)
         core.Conf['proxy'].downloadRdesdkDLL(buildNo, buildTypeOBSB, buildTypeBetaRelease, 'vdp_rdpvcbridge.dll')
      hostname = socket.gethostname()
      core.Conf['proxy'].generateRDPTestConfigFileAgentWin(core.Conf['defaultConfig']['clientip'], hostname)
      core.Conf['proxy'].Popen(r'c:\tools\rdpvc_Test.exe --log_level=all --report_level=detailed --run_test=*TransportPerfTest/*Write*', r'c:\tools')

      self.receiveResultLog(resultLogBaseName)
      logPath = r'c:\tools\vlogs'
      if os.name == 'posix':
         logPath = os.path.expanduser('~/vlogs')
      resultLog = os.path.join(logPath, resultLogBaseName)
      self.generatePerfDataFiles(resultLog)
      return True

   def generatePerfDataFiles(self, resultLog):
      logger.info('Generating result properties file')
      filenameList = []
      dataList = []
      caseBegin = False
      fobj = open(resultLog)
      direction = ''
      for eachLine in fobj:
         if (eachLine.find('Leave test case ') > -1 or eachLine.find('Entering test case ') > -1) and caseBegin:
            caseBegin = False
         if eachLine.find('Entering test case ') > -1:
            caseBegin = True
            mode = re.compile(r'\d+')
            psize = mode.findall(eachLine)
            if eachLine.find('Write') > -1:
               direction = 'a2c'
            elif eachLine.find('Read') > -1:
               direction = 'c2a'
            filename = 'rdp_%sk_%s_%s.properties' % (psize[0], direction, core.Conf['protocol'])
            filenameList.append(filename)
         if caseBegin:
            if eachLine.find('Transport time ') > -1:
               mode = re.compile(r'\d+\.?\d*')
               time = string.atof(mode.findall(eachLine)[0])
               time *= 1000
               dataList.append(time)
      fobj.close()
      for n in range(len(dataList)):
         with open(filenameList[n], 'w') as fp:
            line = 'YVALUE=%s' % dataList[n]
            fp.write(line)
            fp.close()


