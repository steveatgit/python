#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Jenkins Usage:
   set Client IP
   set Agent IP
   set protocol
   set PoolName
   set Client Build Number
   set testsete
   If you didn't set above mentioned variables, default values will be used.
   Copy automation scripts to c:\tools or $HOME direcotry.

Manual Usage:
   python startup.py -h | --help # Show help documentation
   python startup.py             # Usage the default settings in file <config.ini>

   The configuration file <config.ini> which must contain following item:

   [Default]
   server = 10.117.45.68
   user = administrator
   password = ca$hc0w
   domain = wwwwpro
   poolname = testPoolName
   protocol = PCoIP
   serverwithdomainname = wwwwpro.com
   agentip = 10.117.0.2
   agenttoken = 456
   inputmonitor = C:/Tools/InputMonitor.exe
   clipboardmonitor = C:/Tools/ClipboardMonitor.exe
   browser = chrome
   clientbuildno = 100200
   agentbuildno = 100200
   clientip = 10.117.0.1

   [Blast]
   agentip = 10.117.41.74
   blastfakeauth = 456
   browser = chrome
   inputmonitor = C:/Tools/InputMonitor_blastHtml.exe
   resolutionmonitor = C:/Tools/GetScreenResolution.exe

   [Testset]
   vdpservice_rpc_test = true
   vdpservice_web_test = false
   vdpservice_overlay_test = false
   rdpvcbridge_test = false
   rdpvcbridge_perftest = false
   vvc_outproc_test = false
   vvc_inproc_test = false
   vvc_service_test = false
   vvc_full_test = false
   usb_test = false
   usb_rdsh_test = false
   jscdk_test = false
   webclient_test = false
"""

import os
import sys
import re
import time
import platform
import pipes
import subprocess
import getopt
import ConfigParser
import pprint
import shutil
import socket


from xmlrpclib import ServerProxy
try:
   from _winreg import *
except ImportError, err:
   pass

# Import self modules
import core

from core.testrunner import *
from core.testconfig import *
from utils.log import logger

core.DEBUG = False

testcases = ['Positive_CreateConnectionWithServerDisconnect_P0',
             'Positive_CreateConnectionWithClientDisconnect_P0',
             'Positive_ServerCreateObjectFirst_P0',
             'Positive_ServerContextSetCommand_P0',
             'Positive_ServerContextAppendParam_P0',
             'Positive_ServerContextSetCommandMax_P1',
             'Positive_ServerContextSetCommandMin_P1',
             'Positive_ServerContextSetNamedCommand_P1',
             'Positive_ServerContextAppendParamInt32Max_P1',
             'Positive_ServerContextAppendParamInt32Min_P1',
             'Positive_ServerContextAppendParamString_P1',
             'Positive_ServerContextAppendParamUInt32Max_P1',
             'Positive_ServerContextAppendParamUInt32Min_P1',
             'Positive_ServerContextAppendParamCharMin_P1',
             'Positive_ServerContextAppendParamCharMax_P1']

core.testcases = ['Positive_CreateConnectionWithServerDisconnect_P0',
             'Positive_CreateConnectionWithClientDisconnect_P0',
             'Positive_ServerCreateObjectFirst_P0',
             'Positive_ServerContextSetCommand_P0',
             'Positive_ServerContextAppendParam_P0',
             'Positive_ServerContextSetCommandMax_P1',
             'Positive_ServerContextSetCommandMin_P1',
             'Positive_ServerContextSetNamedCommand_P1',
             'Positive_ServerContextAppendParamInt32Max_P1',
             'Positive_ServerContextAppendParamInt32Min_P1',
             'Positive_ServerContextAppendParamString_P1',
             'Positive_ServerContextAppendParamUInt32Max_P1',
             'Positive_ServerContextAppendParamUInt32Min_P1',
             'Positive_ServerContextAppendParamCharMin_P1',
             'Positive_ServerContextAppendParamCharMax_P1']



core.Conf = {
      'proxy':                      None,
      'testasset':                  None,
      'protocol':                   None,
      'clientBuildNo':              None,
      'agentBuildNo':               None,
      'clientIp':                   None,
      'agentIp':                    None,
      'wanemIp':                    None,
      'poolName':                   None,
      'rdesdkBuildNo':              None,
      'rderftallBuildNo':           None,
      'precheckinBuildNo':          None,
      'cfgFile':                    None,
      'resetTestSet':               None,
      'server':                     None,
      'user':                       None,
      'domain':                     None,
      'password':                   None,
      'inputMonitor':               None,
      'clipboardMonitor':           None,
      'linuxAgent':                 None,
      'isCCEnabled':                False,
      'rtavTestFlag':               False,
      'enableUDP':                  False,
      'jobName':                    None,
      'mntFolder':                  '~/mntShare',
      'testsets':                   [],
      'testset':                    {},
      'defaultConfig':              {},
      'blastConfig':                {},
      'clientToolsFolder':          r'c:\tools',
      'shareFolder':                r'\\10.136.240.99\publish',
      'shareFolderLinux':           r'//10.136.240.99/publish',
      'newShareFolder':             r'\\10.117.41.125\share\jenkins',
      'winRxapiS1':                 r'WINDOWS-LOT16MF',
      'testBinFolder':              r'TestBinaries',
      'certConfigDirLinux':         r'.vvvvvv',
      'certConfigFileLinux':        'wwww-preferences',
      'vdpLibFileLinux':            'libvdpservice.so',
      'rpcConfigFile':              r'c:\tools\rpc_testconfig.ini',
      'rpcLibFolderLinux':          r'/usr/lib/vvvvvv/wwww/vdpService',
      'rpcLogFolderLinux':          r'/tmp/vdpService',
      'rpcLibFileLinux':            'librpcchanneltest.so',
      'rpcLibFileWin':              'RPCChannelTestClient.dll',
      'rpcRegisterFileWin32':       'vdpserviceReg_x86.reg',
      'rpcRegisterFileWin64':       'vdpserviceReg_x86.reg',
      'rpcTestFilesFolder':         r'/home/tools/RPCTestFiles',
      'rpcTestFilesFolderWin':      r'c:\tools\RPCTestFiles',
      'rpcTestFiles':               ['1m.1m', '10m.10m', '50m.50m'],
      'rpcResultLog':               'rpcResult.log',
      'rpcWebResultLog':            'rpcWebResult.log',
      'rdpConfigFile':              r'c:\rdpvcbridge.ini',
      'rdpDVCCfgFile':              r'c:\dvc_testconfig.ini',
      'rdpLibFolderLinux':          r'/usr/lib/vvvvvv/rdpvcbridge',
      'rdpLogFolderLinux':          r'/tmp/rdpvcbridgetest',
      'rdpLibFileLinux':            'librdpvcbridgetest.so',
      'rdpLibFolderMac':            r'/Applications/VMware Horizon Client.app/Contents/Frameworks/rdpvcbridge',
      'rdpLibFileMac':              r'librdpvcbridgetest.dylib',
      'rdpLogFolderMac':            r'/tmp/rdpvcbridgetest',
      'bundlePath':                 r'/Applications/VMware Horizon Client.app',
      'bundleId':                   r'com.vvvvvv.horizon',
      'rdpSVCLibFileWin':           'rdpvchantestplugin.dll',
      'rdpDVCLibFileWin':           'DVCTestPlugin.dll',
      'rdpvcPingTestLibFileLinux':  'pingRdpVcbridgeClient.so',
      'rdpvcPingTestLibFileWin':    'pingRdpVcbridgeClient.dll',
      'rdpTestFilesFolder':         r'/tools/RDPTestFiles',
      'rdpTestFilesFolderWin':      r'c:\tools\RDPTestFiles',
      'rdpResultLog':               'rdpResult.log',
      'overlayConfigFile':          r'c:\overlay_testconfig.ini',
      'overlayDisplayCfgFile':      'display_testconfig.ini',
      'overlayLibFolderLinux':      r'/usr/lib/vvvvvv/wwww/vdpService',
      'overlayLibFileLinux':        'liboverlaytest.so',
      'overlayLibFileWin':          'OverlayClientTest.dll',
      'overlayTestFilesFolder':     r'/home/tools/OverlayTestFiles',
      'overlayTestFilesFolderWin':  r'c:\tools\OverlayTestFiles',
      'overlayResultLog':           'overlayResult.log',
      'tsmmrPlayerRunLogPath':      r'c:\tools\vlogs',
      'tsmmrTestFilesFolderWin':    r'c:\tools\TsmmrTestFiles',
      'tsmmrConfigFile':            r'c:\tools\mmr_testconfig.ini',
      'tsmmrMovieName':             'Minion_Rocket.mp4',
      'd3dx9dDll':                  'D3DX9d_36.dll',
      'tsmmrClientTestPluginWin':   'tsmmrTestPlugin.dll',
      'tsmmrPlayerTestSuite':       'TsmmrPlayerCases',
      'tsmmrServerTestSuite':       'TsmmrServerCases',
      'vvcConfigFile':              r'c:\Users\Public\vvc_testconfig.ini',
      'vvcPerfCfgFile':             r'c:\Users\Public\vvc_perfdata.ini',
      'vvcConfigFileLinux':         r'/tmp/vvc_testconfig.ini',
      'vvcLibFileLinux':            'libvvcClientTestPlugin.so',
      'vvcLibFileWin':              'vvcClientTestPlugin.dll',
      'vvcLibFolderLinux':          r'/usr/lib/pcoip/vchan_plugins',
      'vvcTestFilesFolder':         r'/tmp/vvcTestFiles',
      'vvcTestFilesFolderWin':      r'c:\tools\VVCTestFiles',
      'vvcTestFiles':               ['10M', '50M', '100M'],
      'vvcResultLog':               'vvcResult.log',
      'e2eFolderWin':               r'c:\tools\testE2E',
      'e2eFolderUnix':              r'~/testE2E',
      'e2eResultLog':               'e2eResult.log',
      'mfwTestFolder':              r'c:\tools\MFWTest',
      'rdsTestFolder':              r'c:\tools\RDSTest',
      'udpPerfTestFilesFolderWin':  r'c:\tools\UDPPerfTestFiles',
      'udpPerfTestFilesFolderLinux':r'/tmp/UDPPerfTestFiles',
      'cdrPerfTestFilesFolderWin':  r'c:\tools\CDRPerfTestFiles',
      'rpcPerfTestFilesFolderWin':  r'c:\tools\RPCPerfTestFiles',
      'linuxVDI':                   r'no',
      'rdesdkrelbranch':            None,
      'rdesdkrelbuild':             None,
      }

def usage():
   print __doc__

def getParamsFromEnviron():
   execArgs = {
      'user':              'domainuser',
      'domain':            'domainname',
      'password':          'password',
      'protocol':          'Protocol',
      'clientBuildNo':     'clientBuildNo',
      'agentBuildNo':      'agentBuildNo',
      'clientIp':          'clientIp',
      'agentIp':           'agentIp',
      'wanemIp':           'wanemIp',
      'poolName':          'PoolName',
      'rdesdkBuildNo':     'rdesdkBuildNo',
      'rderftallBuildNo':  'rderftallBuildNo',
      'precheckinBuildNo': 'precheckinBuildNo',
      'isCCEnabled':       'isCCEnabled',
      'enableUDP':         'enableUDP',
      'resetTestSet':      'resetTestSet',
      'server':            'Server',
      'inputMonitor':      'InputMonitor',
      'clipboardMonitor':  'ClipboardMonitor',
      'linuxAgent':        'LinuxAgent',
      'linuxVDI':          'linuxvdi',
      'jobName':           'jobName',
      'rdesdkrelbranch':   'rdesdkrelbranch',
      'rdesdkrelbuild':    'rdesdkrelbuild',
      }
   for k, v in execArgs.iteritems():
      if ((v in os.environ.keys()) or (v.upper() in os.environ.keys())):
         core.Conf[k] = os.environ[v]
      else:
         logger.warn('[%s] is not set in environment...' % v)
         logger.info('[%s] will be default value in configuration file.' % v)

def parseCommandLine():
   try:
      optlst, args = getopt.getopt(sys.argv[1:], '-h', \
            ['help'])
      if optlst == [] and len(sys.argv) == 1:
         logger.info('Get parameters from environment variables...')
      elif len(sys.argv) != 5:
         usage()
         sys.exit(2)
      elif len(sys.argv) == 5:
         if 'protocol' in os.environ.keys():
            core.Conf['protocol'] = os.environ['protocol']
         else:
            logger.warn('Variable protocol is not in Environment.')
            logger.info('Using the default value: PCoIP.')
            core.Conf['protocol'] = 'PCoIP'
         core.Conf['clientBuildNo'] = sys.argv[1]
         core.Conf['clientIp'] = sys.argv[2]
         core.Conf['agentIp'] = sys.argv[3]
         core.Conf['poolName'] = sys.argv[4]

      for option, arg in optlst:
         if option in ['-h', '--help']:
            usage()
            sys.exit()

   except getopt.GetoptError, err:
      logger.error(err)
      usage()
      sys.exit(2)

def parseConfigFile():
   cfgFileHandler = ConfigParser.ConfigParser()
   cfgFileHandler.read(core.Conf['cfgFile'])
   core.Conf['defaultConfig'] = dict(cfgFileHandler.items('Default'))
   core.Conf['blastConfig']   = dict(cfgFileHandler.items('Blast'))
   core.Conf['testset']       = dict(cfgFileHandler.items('Testset'))

def updateConfigFile():
   testset = [
      'vdpservice_rpc_test',
      'vdpservice_perf_test',
      'vdpservice_rpc_web_test',
      'vdpservice_overlay_test',
      'rdpvcbridge_test',
      'rdpvcbridge_perftest',
      'rdpvcbridge_ping_test',
      'tsmmr_player_test',
      'tsmmr_server_test',
      'vvc_outproc_test',
      'vvc_inproc_test',
      'vvc_service_test',
      'vvc_full_test',
      'vvc_stress_test',
      'vvc_perf_test',
      'e2e_test',
      'e2e_linvdi_test',
      'e2e_web_test',
      'usb_test',
      'usb_rdsh_test',
      'jscdk_test',
      'libcdk_test',
      'webclient_test',
      'mfw_test',
      'audiodevtap_test',
      'inputdevtap_test',
      'svgadevtap_test',
      'rds_test',
      'wincdkut_test',
      'cdkut_test',
      'smartcard_linvdi_test',
      'rtav_test',
      'udp_perf_test',
      'cdr_perf_test',
      ]
   cfgFileHandler = ConfigParser.ConfigParser()
   cfgFileHandler.optionxform = str
   cfgFileHandler.read(core.Conf['cfgFile'])
   if core.Conf['resetTestSet']:
      if str2bool(core.Conf['resetTestSet']):
         logger.info('Reset value of all test set to false.')
         [cfgFileHandler.set('Testset', item, 'false') for item in testset]
   if core.Conf['protocol']:         cfgFileHandler.set('Default', 'Protocol', core.Conf['protocol'])
   if core.Conf['clientBuildNo']:    cfgFileHandler.set('Default', 'clientbuildno', core.Conf['clientBuildNo'])
   if core.Conf['agentBuildNo']:     cfgFileHandler.set('Default', 'agentbuildno', core.Conf['agentBuildNo'])
   if core.Conf['clientIp']:         cfgFileHandler.set('Default', 'ClientIP', socket.gethostbyname(core.Conf['clientIp']))
   if core.Conf['agentIp']:          cfgFileHandler.set('Default', 'AgentIP', socket.gethostbyname(core.Conf['agentIp']))
   if core.Conf['wanemIp']:          cfgFileHandler.set('Default', 'wanemIP', socket.gethostbyname(core.Conf['wanemIp']))
   if core.Conf['poolName']:         cfgFileHandler.set('Default', 'PoolName', core.Conf['poolName'])
   if core.Conf['clientIp']:         cfgFileHandler.set('Blast', 'ClientIP', socket.gethostbyname(core.Conf['clientIp']))
   if core.Conf['agentIp']:          cfgFileHandler.set('Blast', 'AgentIP', socket.gethostbyname(core.Conf['agentIp']))
   if core.Conf['rdesdkBuildNo']:    cfgFileHandler.set('Default', 'rdesdkBuildNo', core.Conf['rdesdkBuildNo'])
   if core.Conf['rderftallBuildNo']: cfgFileHandler.set('Default', 'rderftallBuildNo', core.Conf['rderftallBuildNo'])
   if core.Conf['server']:           cfgFileHandler.set('Default', 'Server', core.Conf['server'])
   if core.Conf['user']:             cfgFileHandler.set('Default', 'Server', core.Conf['user'])
   if core.Conf['domain']:           cfgFileHandler.set('Default', 'Server', core.Conf['domain'])
   if core.Conf['password']:         cfgFileHandler.set('Default', 'Server', core.Conf['password'])
   if core.Conf['inputMonitor']:     cfgFileHandler.set('Default', 'InputMonitor', core.Conf['inputMonitor'])
   if core.Conf['clipboardMonitor']: cfgFileHandler.set('Default', 'ClipboardMonitor', core.Conf['clipboardMonitor'])
   if core.Conf['linuxAgent']:       cfgFileHandler.set('Default', 'LinuxAgent', core.Conf['linuxAgent'])
   if core.Conf['jobName']:          cfgFileHandler.set('Default', 'jobName', core.Conf['jobName'])
   if core.Conf['jobName']:          cfgFileHandler.set('Default', 'jobName', core.Conf['jobName'])
   if core.Conf['rdesdkrelbranch']:  cfgFileHandler.set('Default', 'rdesdkrelbranch', core.Conf['rdesdkrelbranch'])
   if core.Conf['rdesdkrelbuild']:  cfgFileHandler.set('Default', 'rdesdkrelbuild', core.Conf['rdesdkrelbuild'])
   if os.name == 'nt':
      [cfgFileHandler.set('Testset', item, os.environ[item]) for item in testset if item.upper() in os.environ.keys()]
   else:
      [cfgFileHandler.set('Testset', item, os.environ[item]) for item in testset if item in os.environ.keys()]
   with open(core.Conf['cfgFile'], 'w') as fp:
      cfgFileHandler.write(fp)

def showConfigFile():
   with open(core.Conf['cfgFile'], 'r') as fp:
      logger.info('Test Configuration:\n' + fp.read())

def str2bool(strv):
   return strv.lower() in ('true', 'yes', '1')

def receiveResultLog(proxyName, resultLogBaseName):
   if os.name == 'posix':
      logPath = os.path.expanduser('~')
   resultLog = os.path.join(core.Conf['clientToolsFolder'], resultLogBaseName)
   with open(resultLog, 'wb') as fp:
      fp.write(proxyName.sendResultLog().data)
   # Rename the log file in server side
   resultLogOnServer = os.path.join(r'c:\tools', resultLogBaseName)
   proxyName.renameResultLog(resultLogOnServer)
   return True

def showResultLog(resultLogBaseName):
   resultLog = os.path.join(core.Conf['clientToolsFolder'], resultLogBaseName)
   with open(resultLog, 'r') as fp:
      logger.info(fp.read())
   return True

def preConfigure():
   if sys.platform.startswith('darwin'):
      logPath = r'/jenkins/tools/vlogs'
   else:
      logPath = r'/home/tools/vlogs'
   loadEnvFile = r'LoadEnv.bat'
   envParamsDefault = {'MyRole': 'Client',
                       'Machine': socket.gethostname(),
                       'HostOS': platform.system(),
                       'BuildType': 'ob'}
   if os.name == 'nt':
      [envParamsDefault.update({key: os.environ[key]}) for key in envParamsDefault.keys() if key.upper() in os.environ.keys()]
   else:
      [envParamsDefault.update({key: os.environ[key]}) for key in envParamsDefault.keys() if key in os.environ.keys()]
   envParams = (envParamsDefault['MyRole'],
                envParamsDefault['Machine'],
                envParamsDefault['HostOS'],
                core.Conf['defaultConfig']['clientbuildno'],
                envParamsDefault['BuildType'])
   envStrings = '''\
set MYROLE=%s
set Client.MachineName=%s
set Client.Properties.OS=%s
set BuildNo=%s
set BuildType=%s''' % envParams
   if os.name == 'nt':
      logPath = r'c:\tools\vlogs'
   if not os.path.exists(logPath):
      os.makedirs(logPath)
   else:
      shutil.rmtree(logPath)
      time.sleep(2)
      os.makedirs(logPath)
   with open(os.path.join(logPath, loadEnvFile), 'wb') as fp:
      fp.write(envStrings)
   # Download Test Binnaries
   DownloadTestBinaries()()
   return True

def actionOnClient():
   preConfigure()
   if str2bool(core.Conf['testset']['vdpservice_rpc_test']):
      core.Conf['testsets'].append('vdpservice_rpc_test')
      RPCConfigOnClient()()
   if str2bool(core.Conf['testset']['vdpservice_rpc_web_test']):
      core.Conf['testsets'].append('vdpservice_rpc_web_test')
      RPCWebConfigOnClient()()
   if str2bool(core.Conf['testset']['vdpservice_overlay_test']):
      core.Conf['testsets'].append('vdpservice_overlay_test')
      OverlayConfigOnClient()()
   if str2bool(core.Conf['testset']['rdpvcbridge_test']):
      core.Conf['testsets'].append('rdpvcbridge_test')
      RDPConfigOnClient()()
   if str2bool(core.Conf['testset']['rdpvcbridge_perftest']):
      core.Conf['testsets'].append('rdpvcbridge_perftest')
      RDPConfigOnClient()()
   if str2bool(core.Conf['testset']['rdpvcbridge_ping_test']):
      core.Conf['testsets'].append('rdpvcbridge_ping_test')
      RDPPingConfigOnClient()()
   if str2bool(core.Conf['testset']['tsmmr_player_test']):
      core.Conf['testsets'].append('tsmmr_player_test')
   if str2bool(core.Conf['testset']['tsmmr_server_test']):
      core.Conf['testsets'].append('tsmmr_server_test')
   if str2bool(core.Conf['testset']['vvc_inproc_test']):
      core.Conf['testsets'].append('vvc_inproc_test')
   if str2bool(core.Conf['testset']['vvc_outproc_test']):
      core.Conf['testsets'].append('vvc_outproc_test')
   if str2bool(core.Conf['testset']['vvc_service_test']):
      core.Conf['testsets'].append('vvc_service_test')
   if str2bool(core.Conf['testset']['e2e_test']):
      core.Conf['testsets'].append('e2e_test')
      E2EConfigOnClient()()
   if str2bool(core.Conf['testset']['e2e_linvdi_test']):
      core.Conf['testsets'].append('e2e_linvdi_test')
      E2EConfigOnClient()()
      E2ELinVDIConfigOnClient()()
   if str2bool(core.Conf['testset']['e2e_web_test']):
      core.Conf['testsets'].append('e2e_web_test')
      E2EConfigOnClient()()
   if str2bool(core.Conf['testset']['usb_test']):
      core.Conf['testsets'].append('usb_test')
      USBConfigOnClient()()
   if str2bool(core.Conf['testset']['usb_rdsh_test']):
      core.Conf['testsets'].append('usb_rdsh_test')
      USBConfigOnClient()()
   if str2bool(core.Conf['testset']['jscdk_test']):
      core.Conf['testsets'].append('jscdk_test')
      JSCDKConfigOnClient()()
   if str2bool(core.Conf['testset']['libcdk_test']):
      core.Conf['testsets'].append('libcdk_test')
      LIBCDKConfigOnClient()()
   if str2bool(core.Conf['testset']['webclient_test']):
      core.Conf['testsets'].append('webclient_test')
      WebclientConfigOnClient()()
   if str2bool(core.Conf['testset']['mfw_test']):
      core.Conf['testsets'].append('mfw_test')
      MFWConfigOnClient()()
   if str2bool(core.Conf['testset']['audiodevtap_test']):
      core.Conf['testsets'].append('audiodevtap_test')
      AudioConfigOnClient()()
   if str2bool(core.Conf['testset']['inputdevtap_test']):
      core.Conf['testsets'].append('inputdevtap_test')
      InputConfigOnClient()()
   if str2bool(core.Conf['testset']['svgadevtap_test']):
      core.Conf['testsets'].append('svgadevtap_test')
      SvgaConfigOnClient()()
   if str2bool(core.Conf['testset']['rds_test']):
      core.Conf['testsets'].append('rds_test')
      RDSConfigOnClient()()
   if str2bool(core.Conf['testset']['wincdkut_test']):
      core.Conf['testsets'].append('wincdkut_test')
      WincdkUTConfigOnClient()()
   if str2bool(core.Conf['testset']['cdkut_test']):
      #Using the same config as wincdkut
      core.Conf['testsets'].append('cdkut_test')
      WincdkUTConfigOnClient()()
   if str2bool(core.Conf['testset']['smartcard_linvdi_test']):
      core.Conf['testsets'].append('smartcard_linvdi_test')
      SmartcardLinVDIConfigOnClient()()
   if str2bool(core.Conf['testset']['rtav_test']):
      core.Conf['testsets'].append('rtav_test')
      RtavConfigOnClient()()
   if str2bool(core.Conf['testset']['udp_perf_test']):
      core.Conf['testsets'].append('udp_perf_test')
      UDPPerfConfigOnClient()()
   if str2bool(core.Conf['testset']['cdr_perf_test']):
      core.Conf['testsets'].append('cdr_perf_test')
      CDRPerfConfigOnClient()()


def main():
   if os.name == 'nt':
      core.Conf['cfgFile'] = r'c:\tools\config.ini'
   elif sys.platform.startswith('darwin'):
      core.Conf['cfgFile'] = r'/jenkins/tools/config.ini'
   else:
      core.Conf['cfgFile'] = r'/home/tools/config.ini'
   if not os.path.exists(core.Conf['cfgFile']):
      logger.warn('Please copy file <config.ini> to %s ...' % core.Conf['cfgFile'])
      sys.exit(2)
   # Get environment variabls and update configuration file.
   parseCommandLine()
   getParamsFromEnviron()
   updateConfigFile()
   showConfigFile()
   parseConfigFile()

   # Startup
   actionOnClient()
   # VDPService testset
   vdpPerfTest   = str2bool(core.Conf['testset']['vdpservice_perf_test'])
   # VVC testset
   vvcFullTest   = str2bool(core.Conf['testset']['vvc_full_test'])
   vvcStressTest = str2bool(core.Conf['testset']['vvc_stress_test'])
   vvcPerfTest   = str2bool(core.Conf['testset']['vvc_perf_test'])
   if str2bool(core.Conf['testset']['vdpservice_rpc_test']):
      RPCTestRunner(vdpPerfTest)()
   if str2bool(core.Conf['testset']['vdpservice_rpc_web_test']):
      RPCWebTestRunner()()
   if str2bool(core.Conf['testset']['vdpservice_overlay_test']):
      OverlayTestRunner()()
   if str2bool(core.Conf['testset']['rdpvcbridge_test']):
      RDPTestRunner()()
   if str2bool(core.Conf['testset']['rdpvcbridge_perftest']):
      RDPPerfTestRunner()()
   if str2bool(core.Conf['testset']['rdpvcbridge_ping_test']):
      RDPPingTestRunner()()
   if str2bool(core.Conf['testset']['tsmmr_player_test']):
      TsmmrConfigOnClientForPlayer()()
      TsmmrPlayerTestRunner()()
      TsmmrCleanupConfigOnClient()()
   if str2bool(core.Conf['testset']['tsmmr_server_test']):
      TsmmrConfigOnClientForServer()()
      TsmmrServerTestRunner()()
      TsmmrCleanupConfigOnClient()()
   if str2bool(core.Conf['testset']['vvc_outproc_test']):
      VVCConfigOnClient()()
      VVCTestRunner(vvcFullTest, vvcStressTest, vvcPerfTest)()
   if str2bool(core.Conf['testset']['vvc_inproc_test']):
      VVCInProcConfigOnClient()()
      VVCInProcTestRunner(vvcFullTest, vvcStressTest, vvcPerfTest)()
   if str2bool(core.Conf['testset']['vvc_service_test']):
      VVCConfigOnClient()()
      VVCServiceTestRunner(vvcFullTest, vvcStressTest, vvcPerfTest)()
   if str2bool(core.Conf['testset']['e2e_test']):
      E2ETestRunner()()
   if str2bool(core.Conf['testset']['e2e_linvdi_test']):
      E2ELinVDITestRunner()()
   if str2bool(core.Conf['testset']['e2e_web_test']):
      E2EWebTestRunner()()
   if str2bool(core.Conf['testset']['usb_test']):
      USBTestRunner()()
   if str2bool(core.Conf['testset']['usb_rdsh_test']):
      USBTestRunner(isRDS = True)()
   if str2bool(core.Conf['testset']['jscdk_test']):
      JSCDKTestRunner()()
   if str2bool(core.Conf['testset']['libcdk_test']):
      LIBCDKTestRunner()()
   if str2bool(core.Conf['testset']['webclient_test']):
      WebclientTestRunner()()
   if str2bool(core.Conf['testset']['mfw_test']):
      MFWTestRunner()()
   if str2bool(core.Conf['testset']['audiodevtap_test']):
      AudioTestRunner()()
   if str2bool(core.Conf['testset']['inputdevtap_test']):
      InputTestRunner()()
   if str2bool(core.Conf['testset']['svgadevtap_test']):
      SvgaTestRunner()()
   if str2bool(core.Conf['testset']['rds_test']):
      RDSTestRunner()()
   if str2bool(core.Conf['testset']['wincdkut_test']):
      WincdkUTTestRunner()()
   if str2bool(core.Conf['testset']['cdkut_test']):
      CdkUTTestRunner()()
   if str2bool(core.Conf['testset']['smartcard_linvdi_test']):
      SmartcardLinVDITestRunner()()
   if str2bool(core.Conf['testset']['rtav_test']):
      RtavTestRunner()()
   if str2bool(core.Conf['testset']['udp_perf_test']):
      UDPPerfTestRunner()()
   if str2bool(core.Conf['testset']['cdr_perf_test']):
      CDRPerfTestRunner()()
      # core.Conf['testsets'].append('cdr_perf_test')
      # CDRPerfTestRunner('tcp')()


if __name__ == '__main__':
   main()
