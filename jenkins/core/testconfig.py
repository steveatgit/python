# -*- coding:utf-8 -*-

import os
import sys
import time
import shutil
import socket
import zipfile
import tarfile
import platform
import subprocess
import urllib
import getpass
import glob
import xml.etree.ElementTree as ET


# Import self modules
import core

from urllib import urlopen, urlretrieve
from utils.common import disableCertCheckLinux
from utils.common import disableCertCheckWin,\
                         disableBlastSSLCheckWin,\
                         mountToolchain, \
                         disableCertCheckMac
from utils.common import connectRPCServer
from utils.downloadRdesdkDll import *
from utils.log import logger

from utils.libcdk.certSetup import createAll


class DownloadTestBinaries():
   '''
   [Download Test Binaries]
   This class is used for Test Binaries Downloading process.
   '''
   def __call__(self):
      if os.name == 'nt':
         self.downloadTestBinariesClientWin()
      elif sys.platform.startswith('linux'):
         self.downloadTestBinariesClientLinux()
      elif sys.platform.startswith('darwin'):
         pass

   # For Platform Windows
   def downloadTestBinariesClientWin(self):
      testBinariesFolder = os.path.join(core.Conf['newShareFolder'],
                                        core.Conf['testBinFolder'])
      # comment 
	  #subprocess.call(r'net use %s ## /user:administrator' % testBinariesFolder)
      # Check local tools folder - c:\tools
      localDestToolsFolder = core.Conf['clientToolsFolder']
      if not os.path.exists(localDestToolsFolder):
         os.mkdir(localDestToolsFolder)
      rdsTestFolder = core.Conf['rdsTestFolder']
      if not os.path.exists(rdsTestFolder):
         os.mkdir(rdsTestFolder)
      subprocess.call(r'xcopy %s\client\rds\* %s /R /Y' % (testBinariesFolder, rdsTestFolder))
      subprocess.call(r'xcopy %s\client\common\* C:\tools /R /Y' % testBinariesFolder)
      if "PROGRAMFILES(x86)" not in os.environ:
         subprocess.call(r'xcopy %s\client\x86\* C:\tools /R /Y' % testBinariesFolder)
      else:
         subprocess.call(r'xcopy %s\client\x64\* C:\tools /R /Y' % testBinariesFolder)
      return True

   def downloadTestBinariesClientLinux(self):
      return True

class ConfigOnClient():
   '''
   [Super Class]
   This class is a super class.
   '''
   def __call__(self):
      if os.name == 'nt':
         self.configWindows()
      elif sys.platform.startswith('linux'):
         self.configLinux()
      elif sys.platform.startswith('darwin'):
         self.configMac()
      return True


   def extractZip(self, zipFile, destFolder):
      if os.path.exists(zipFile):
         logger.info('Unzip %s' % zipFile)
      else:
         logger.error('File NOT Exists...')
         sys.exit(2)
      extName = os.path.splitext(zipFile)[-1]
      if extName in ['.zip', '.war']:
         with zipfile.ZipFile(zipFile) as fp:
            fp.extractall(destFolder)
      elif extName in ['.gz', '.tar', '.bz2']:
         with tarfile.open(zipfile) as fp:
            fp.extractall(destFolder)
      return True


   def downloadE2ETestFilesWin(self):
      # Remove testE2E folder before download a new one.
      e2eFolder = core.Conf['e2eFolderWin']
      if os.path.exists(e2eFolder):
         shutil.rmtree(e2eFolder)
      buildNo = int(core.Conf['defaultConfig']['clientbuildno'])
      destFolder = core.Conf['clientToolsFolder']
      fileName = DownloadTestE2E(buildNo)(destFolder)
      fileFullPath = os.path.join(destFolder, fileName)
      if os.path.exists(fileFullPath):
         with zipfile.ZipFile(fileFullPath) as fp:
            fp.extractall(destFolder)
      return True


class RDPConfigOnClient(ConfigOnClient):
   '''
   '''
   def configWindows(self):
      self.downloadTestFilesWin(core.Conf['newShareFolder'])
      if core.Conf['precheckinBuildNo']:
         buildNo = int(core.Conf['precheckinBuildNo'])
         downloadAndReplaceRdesdkDll(buildNo, '##.dll')
      disableCertCheckWin()
      disableBlastSSLCheckWin()
      self.generateConfigFileWin()
      self.registerTestPluginsWin()

   def configLinux(self):
      self.downloadTestFilesLinux(core.Conf['mntFolder'])
      disableCertCheckLinux()
      self.generateConfigFileLinux()
      self.registerTestPluginsLinux()

   def configMac(self):
      self.downloadTestFilesMac(core.Conf['mntFolder'])
      disableCertCheckMac()
      self.generateConfigFileMac()
      self.registerTestPluginsMac()

   def downloadTestFilesWin(self, shareFolder):
      rdpTestFilesFolder = core.Conf['rdpTestFilesFolderWin']
      # Create RDPTestFiles folder
      if not os.path.exists(rdpTestFilesFolder):
         os.mkdir(rdpTestFilesFolder)
      # Copy test files
      subprocess.call(r'xcopy %s\TestFiles\RDPTestFiles\* %s /Y' % (shareFolder, rdpTestFilesFolder), shell = True)
      return True

   def downloadTestFilesLinux(self, mntFolder):
      rdpTestFilesFolder = core.Conf['rdpTestFilesFolder']
      # Create RDPTestFiles folder
      if not os.path.exists(rdpTestFilesFolder):
         os.system('sudo mkdir -p %s' % rdpTestFilesFolder)
      subprocess.call('sudo chown -R $USER:$USER %s' % rdpTestFilesFolder, shell = True)
      # Copy test files
      subprocess.call('cp -f %s/TestFiles/RDPTestFiles/* %s' % (mntFolder, rdpTestFilesFolder), shell = True)
      return True

   def downloadTestFilesMac(self, mntFolder):
      rdpTestFilesFolder = core.Conf['rdpTestFilesFolder']
      if not os.path.exists(rdpTestFilesFolder):
         os.system('sudo mkdir -p %s' % rdpTestFilesFolder)
      subprocess.call('sudo chown -R $USER %s' % rdpTestFilesFolder, shell = True)
      logger.info("Copying rdp test files from server to local...")
      subprocess.call('cp -f %s/TestFiles/RDPTestFiles/* %s' % (mntFolder, rdpTestFilesFolder), shell = True)
      return True

   def registerTestPluginsWin(self):
      libFile = os.path.join(core.Conf['clientToolsFolder'],
                             core.Conf['rdpSVCLibFileWin'])
      # After update the test code, revert the libFile to original one [libFile].
      libFileTemp = os.path.join(os.path.dirname(core.Conf['clientToolsFolder']),
                                                 core.Conf['rdpSVCLibFileWin'])
      shutil.copy(libFile, libFileTemp)
      subprocess.call('regsvr32.exe /s %s' % libFileTemp, shell = True)
      libFile = os.path.join(core.Conf['clientToolsFolder'],
                             core.Conf['rdpDVCLibFileWin'])
      libFileTemp = os.path.join(os.path.dirname(core.Conf['clientToolsFolder']),
                                                 core.Conf['rdpDVCLibFileWin'])
      shutil.copy(libFile, libFileTemp)
      subprocess.call('regsvr32.exe /s %s' % libFileTemp, shell = True)
      #regcmd = r'echo Yes | Reg Add "HKLM\SOFTWARE\VMware, Inc.\VMware VDM\Client\Vvc\Plugins\RdpVcBridge" /f /v filename /t REG_SZ /d "C:\Program Files\VMware\VMware Horizon View Client\vdp_rdpvcbridge.dll"'
      #if "PROGRAMFILES(x86)" in os.environ:
      #   regcmd = r'echo Yes | Reg Add "HKLM\SOFTWARE\Wow6432Node\VMware, Inc.\VMware VDM\Client\Vvc\Plugins\RdpVcBridge" /f /v filename /t REG_SZ /d "C:\Program Files (x86)\VMware\VMware Horizon View Client\vdp_rdpvcbridge.dll"'
      #if core.Conf['defaultConfig']['protocol'].lower() == 'blast':
      #   subprocess.call(regcmd, shell = True)
      time.sleep(3)
      return True

   def registerTestPluginsLinux(self):
      libFile = os.path.join(core.Conf['rdpLibFolderLinux'],
                             core.Conf['rdpLibFileLinux'])
      rdpLogFolder = core.Conf['rdpLogFolderLinux']
      subprocess.call('sudo cp -f ###' %
                      (core.Conf['mntFolder'], core.Conf['rdpLibFileLinux'], core.Conf['rdpLibFolderLinux']), shell = True)
      if not os.path.exists(libFile):
         return False
      subprocess.call('sudo chmod 755 %s' % libFile, shell = True)
      if not os.path.exists(rdpLogFolder):
         logger.info('create rdpvcbridge log folder...')
         os.system('mkdir -p %s' % rdpLogFolder)
      return True

   def registerTestPluginsMac(self):
      logger.info('register test plugins for mac client...')
      libFile = os.path.join(core.Conf['rdpLibFolderMac'],
                             core.Conf['rdpLibFileMac'])
      logger.info('ccc %s' % os.path.normpath(libFile))
      rdpLogFolder = core.Conf['rdpLogFolderMac']
      subprocess.call(r'cp -f ## "%s"' %
                      (core.Conf['mntFolder'], core.Conf['rdpLibFileMac'], core.Conf['rdpLibFolderMac']), shell = True)
      if not os.path.exists(libFile):
         logger.info('error: rdp lib file doesnt exist')
         return False
      subprocess.call('chmod 755 %s' % libFile, shell = True)
      if not os.path.exists(rdpLogFolder):
         logger.info('create rdpvcbridge log folder...')
         os.system('mkdir -p %s' % rdpLogFolder)
      return True
      
   def generateConfigFileWin(self):
      return True

   def generateConfigFileLinux(self):
      return True
      
   def generateConfigFileMac(self):
      return True 


