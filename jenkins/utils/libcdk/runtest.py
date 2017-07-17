#!/build/toolchain/lin32/python-2.7.1/bin/python2.7

import codecs
import re
import os, sys
import time
import sys,os,logging,urllib,urllib2
import subprocess
import StringIO
import shutil
import tarfile
import zipfile
from optparse import OptionParser
from xml.dom.minidom import parseString

try:
   import simplejson as json
except ImportError:
   import json

from utils.reporter import *

import racetrack
from utils.log import logger

racetrack.server = 'racetrack-dev.eng.vvvvvv.com'

def getCommandLine():
   '''Get the command line options'''
   usage = 'Usage: ./runtest.py [options]'
   parser = OptionParser(usage)
   parser.add_option ('--buildId', dest = 'buildId', type = int,
      help = 'Build number')
   parser.add_option ('--extractPath', dest = 'extPath',
      help = 'Where to extract the test binaries. default to /build/ or c:\\build\\')
   parser.add_option ('--caseNameFile', dest = 'caseNameFile',
      help = 'Load case names from this file.')
   options, testProg = parser.parse_args()
   if not options.extPath:
      if sys.platform == 'win32':
         options.extPath = 'c:\\build\\'
      else:
         options.extPath = '/build/'
   if not options.buildId:
      logger.error('buildId is not set.')
      parser.error('--buildId must be set.')
   return options


def getResourceList(url):
   '''Get build info data'''
   buildweb = 'http://buildapi.eng.vvvvvv.com'
   url = '%s%s' % (buildweb, url)
   #print 'Fetching %s ...\r\n' % url
   ret = urllib2.urlopen(url)
   status = int(ret.code)
   if status != 200:
      logger.error('HTTP status %d', status)
      raise Exception('Error: %s' % data['http_response_code']['message'])
   content = ret.read()
   if json:
      data = json.loads(content)
   else:
     dataDict = {}
     dataList = []
     for i in content.replace(' ','').split('[{')[1].split('}]')[0].split('},{'):
        for j in i.split(','):
           dataDict[j.split(':')[0].strip().strip('"')] = j.split(':')[1].strip().strip('"')
        dataList.append(dataDict)
        dataDict = {}
     dataDict['_list'] = dataList
     data = dataDict
   return data


def getBuildType(buildId):
   '''Get the buildType is sb or ob'''
   url1 = ('http://buildapi.eng.vvvvvv.com/sb/build/%d' % buildId)
   url2 = ('http://buildapi.eng.vvvvvv.com/ob/build/%d' % buildId)
   status1 = None
   status2 = None
   try:
      status1 = int(urllib2.urlopen(url1).code)
      status2 = int(urllib2.urlopen(url2).code)
   except:
      pass
   if status1 == 200 and status2 != 200:
      return 'sb'
   elif status1 != 200 and status2 == 200:
      return 'ob'
   elif status1 == 200 and status2 == 200:
      logger.info('Build %d is found in both official and sandbox builds.', buildId)
      logger.info('Assuming build %d is official build.', buildId)
      return 'ob'
   else:
      logger.error('HTTP status for %s %d', url1, status1)
      logger.error('HTTP status for %s %d', url2, status2)
      raise Exception('Error: network issue')
      return 'netError'


def getRacetrackResult(racetrackUrl):
   f = urllib2.urlopen(racetrackUrl)
   data = f.readlines()
   f.close()
   for line in data:
      if line.find(r'''<td class="pass" title="">''') != -1 or line.find(r'''Total test execution time:''') != -1:
         passed = '0'
         failed = ''
         p1 = re.compile(r"""<td>PASS - (.*?)</td>""")
         p2 = re.compile(r"""<td>FAIL - (.*?)</td>""")
         p3 = re.compile(r"""<td class="fail" title="">(.*?)</td>""")
         p4 = re.compile(r"""<td class="passfail" title="">(.*?)</td>""")
         if p1.search(line):
            passed = p1.search(line).group(1)
         if p2.search(line):
            failed = p2.search(line).group(1)
         elif p3.search(line):
            failed = p3.search(line).group(1)
         elif p4.search(line):
            failed = p4.search(line).group(1)
         return (int(passed), int(failed))
   return 'Unknown'

class BuildInfo(object):
   '''Download and extract test binaries from buildweb'''
   def __init__(self,
                buildId):
      self.buildId = buildId
      self.buildType = getBuildType(buildId)
      self.data = getResourceList('/%s/build/%d' % (self.buildType, self.buildId))
      self.version = self.data['version']
      self.branch = self.data['branch']
      self.releaseType = self.data['releasetype']
      self.product = self.data['product']


class GetTestBin(object):
   def __init__(self,
                aBuildInfo,
                extPath,
                androidTest=False):
      self.bi = aBuildInfo
      self.extPath = extPath
      if sys.platform == 'win32':
         self.zipName = "testE2E-VMware-wwww-client-Windows-%s-%d.zip" % (self.bi.version, self.bi.buildId)
      elif sys.platform == 'linux2':
         self.zipName = "testE2E-VMware-wwww-client-Linux-%s-%d.tar.gz" % (self.bi.version, self.bi.buildId)
      elif sys.platform == 'darwin':
         self.zipName = "testE2E-VMware-wwww-client-Mac-%s-%d.tar.gz" % (self.bi.version, self.bi.buildId)
      if androidTest:
         self.zipName = "testE2E-VMware-wwww-client-AndroidOS-arm-%s-%d.tar.gz" % (self.bi.version, self.bi.buildId)
      self.zipPath = os.path.join(self.extPath, self.zipName)
      self.warName = 'testwebclient.war'
      self.warPath = os.path.join(self.extPath, self.warName)


   def waitBuildComplete(self):
      '''Wait the specified build complete'''
      url = '/%s/build/%d' % (self.bi.buildType, self.bi.buildId)
      for i in range(60):
         data = getResourceList(url)
         if data['buildstate'] == 'succeeded':
            logger.info('Build %d succeeded', self.bi.buildId)
            return True
         logger.info('Waiting for build %d to complete: %d mins', self.bi.buildId, i)
         time.sleep(60)
      logger.error('Build %d timed out: 60 mins', self.bi.buildId)
      return False


   def downloadTestLibcdkBinaries(self):
      if os.name == 'nt':
         url = 'http://buildweb.eng.vvvvvv.com/%s/api/%d/deliverable/?file=publish/tests/%s' % (self.bi.buildType, self.bi.buildId, self.zipName)
      else:
         url = 'http://buildweb.eng.vvvvvv.com/%s/api/%d/deliverable/?file=publish/%s' % (self.bi.buildType, self.bi.buildId, self.zipName)
      logger.info('Retrieving %s to %s ', url, self.zipPath)
      retry = 6
      rUrl = r'%s' % url
      rPath = r'%s' % self.zipPath
      while(retry > 0):
         try:
            urllib.urlretrieve(rUrl, rPath)
            break
         except IOError:
            print "IOError! retry %d" %retry
            retry = retry - 1
            time.sleep(60)


   def extractTestLibcdkBinaries(self):
      if sys.platform == 'linux2':
         self.extractTestLibcdkBinariesLinux()
      elif sys.platform == 'darwin':
         self.extractTestLibcdkBinariesMac()
      elif sys.platform == 'win32':
         self.extractTestLibcdkBinariesWin()


   def extractTestLibcdkBinariesLinux(self):
      path = os.path.join(self.extPath, 'testE2E')
      if os.path.exists(path):
         shutil.rmtree(path, ignore_errors=1)
      logger.info('Extracting test binaries %s.', self.zipPath)
      if subprocess.call(['tar', 'zxf', self.zipPath, '-C', self.extPath]) != 0:
         logger.error('Extracting test binaries failed.')
         sys.exit()
      else:
         logger.info('Extracting test binaries completed.')


   def extractTestLibcdkBinariesMac(self):
      path = os.path.join(self.extPath, 'E2E')
      if os.path.exists(path):
         shutil.rmtree(path, ignore_errors=1)
      logger.info('Extracting test binaries %s.', self.zipPath)
      if subprocess.call(['tar', 'zxf', self.zipPath, '-C', self.extPath]) != 0:
         logger.error('Extracting test binaries failed.')
         sys.exit()
      else:
         logger.info('Extracting test binaries completed.')


   def extractTestLibcdkBinariesWin(self):
      path = os.path.join(self.extPath, 'testE2E')
      if os.path.exists(path):
         os.system('rd /S /Q %s' % path)
      logger.info('Extracting test binaries %s.', self.zipPath)
      z = zipfile.ZipFile(self.zipPath)
      z.extractall(self.extPath)
      logger.info('Extracting test binaries completed.')


   def extractTestLibcdkBinariesAndroid(self):
      path = os.path.join(self.extPath, 'testE2E')
      if os.path.exists(path):
         os.system('rd /S /Q %s' % path)
      logger.info('Extracting test binaries %s.', self.zipPath)
      tar = tarfile.open(self.zipPath)
      tar.extractall(self.extPath)
      tar.close()
      logger.info('Extracting test binaries completed.')


   def downloadTestJscdkBinaries(self):
      url = 'http://buildweb.eng.vvvvvv.com/%s/api/%d/deliverable/?file=publish/%s' % (self.bi.buildType, self.bi.buildId, self.warName)
      logger.info('Retrieving %s to %s', url, self.warPath)
      urllib.urlretrieve(url,self.warPath)


   def extractTestJscdkBinaries(self):
      path = os.path.join(self.extPath, 'testwebclient')
      if os.path.exists(path):
         shutil.rmtree(path)
      logger.info('Extracting test binaries %s.', self.warPath)
      z = zipfile.ZipFile(self.warPath)
      z.extractall(self.extPath)
      logger.info('Extracting test binaries completed.')


   def downloadTestWebclientBinaries(self):
      self.downloadTestJscdkBinaries()


   def extractTestWebclientBinaries(self):
      self.extractTestJscdkBinaries()


class RunTestView(object):
   '''Execute test cases for testView(libcdk)'''
   def __init__(self,
                aBuildInfo,
                extPath,
                caseNameFile = 'libcdk.txt',
                userName = 'SHD-API-PRECHECKIN',
                description = 'Libcdk'):
      self.bi = aBuildInfo
      self.caseNamePath = os.path.join(sys.path[0], caseNameFile)
      self.userName = userName
      self.description = description
      self.racetrackInfo = []
      self.logPath = os.path.join(extPath, 'vlogs', 'libcdk_result.log')
      if sys.platform == 'linux2':
         self.path = os.path.join(extPath, 'testE2E')
         self.testViewPath = os.path.join(self.path, 'testView')
         self.certSetupPath = os.path.join(self.path, 'certSetup.py')
         self.hostName = 'Linux'
      elif sys.platform == 'darwin':
         self.path = os.path.join(extPath, 'E2E', 'VMware Horizon Client.app', 'Contents', 'MacOS').rstrip()
         self.testViewPath = os.path.join(self.path, 'testView')
         self.certSetupPath = os.path.join(self.path, 'certSetup.py')
         self.hostName = 'Mac'
      elif sys.platform == 'win32':
         self.path = os.path.join(extPath, 'testE2E')
         self.testViewPath = os.path.join(self.path, 'testView.exe')
         self.certSetupPath = os.path.join(self.path, 'certSetup.bat')
         self.hostName = 'Windows'


   def runTestCase(self,
                   caseName,
                   options):
      result = ''
      cmd = '"%s" -p %s ' % (self.testViewPath, caseName)
      if sys.platform == 'win32':
         proc = subprocess.Popen([self.testViewPath, '-p', caseName], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      else:
         proc = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      proc.wait()
      caseOutput = proc.stdout.readlines()
      caseErr =  proc.stderr.readlines()
      resultLogBaseName = 'libcdk_result.log'
      with open(self.logPath,'a+') as fp:
         for line in caseOutput:
            fp.write(line)
            fp.write('\n')
      xmlGenerator('libcdk', self.logPath)()
      for line in caseOutput:
         if line.find(caseName) != -1:
            logger.info(line.strip())
            #Determine feature name by case name.
            if caseName.split('/')[1] == 'MainLoop':
               featureName = caseName.split('/')[1]
            else:
               featureName = ' '.join(caseName.split('/')[1:3])
            racetrack.testCaseBegin(caseName, featureName, "libcdk API test")
            if 'OK' in line[line.find(':'):]:
               result = 'PASS'
            else:
               result = 'FAIL'
               racetrack.comment(caseErr)
               for err in caseErr:
                  if err.find("Using log file") != -1:
                     dbgLogPathFile = ((err.split('Using log file '))[1]).rstrip()
                     logger.info('Uploading log file: %s', dbgLogPathFile)
                     racetrack.log('Debug log', dbgLogPathFile)
            racetrack.testCaseEnd(result)
            break


   def runTestCasesFromFile(self):
      logger.info('Reading test cases from %s', self.caseNamePath)
      #fd = codecs.open(self.caseNamePath, 'r', 'utf-8-sig')
      if not os.path.exists(self.caseNamePath):
         logger.error('Can not find %s.', self.caseNamePath)
         sys.exit()
      if not os.path.exists(self.testViewPath):
         logger.error('Can not find %s.', self.testViewPath)
         sys.exit()
      fd = open(self.caseNamePath, 'r')
      output = fd.readlines()
      fd.close()
      cwd = os.getcwd()
      os.chdir(self.path)
      os.putenv('TEST_SSL_SKIP_CERT_SETUP', '1')
      racetrack.testSetBegin(self.bi.buildId, self.userName, self.bi.product,
         self.description, self.hostName, BuildType=self.bi.releaseType,
         Branch=self.bi.branch)
      logger.info("Racetrack: http://%s/result.php?id=%s", racetrack.server, racetrack.testSetID)
      for line in output:
         if line.startswith('/'):
            self.runTestCase(line.strip(), None)
      logger.info("=" * 50)
      logger.info("Racetrack: http://%s/result.php?id=%s", racetrack.server, racetrack.testSetID)
      logger.info("=" * 50)
      racetrack.testSetEnd()
      os.chdir(cwd)


   def runTestCasesAll(self):
      logger.info('Running all test cases.')
      if not os.path.exists(self.testViewPath):
         logger.error('Can not find %s.', self.testViewPath)
         sys.exit()
      cwd = os.getcwd()
      os.chdir(self.path)
      os.putenv('TEST_SSL_SKIP_CERT_SETUP', '1')
      cmd = '"%s" -l' % self.testViewPath
      if sys.platform == 'win32':
         proc = subprocess.Popen([self.testViewPath, '-l'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      else:
         proc = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      time.sleep(20)
      caseOutput = proc.stdout.readlines()
      caseErr =  proc.stderr.readlines()
      logger.info(cmd)
      proc.wait()
      racetrack.testSetBegin(self.bi.buildId, self.userName, self.bi.product,
         self.description, self.hostName, BuildType=self.bi.releaseType,
         Branch=self.bi.branch)
      for line in caseOutput:
         if line.strip().startswith('/'):
            self.runTestCase(line.strip(), None)
      self.getRacetrackInfo()
      logger.info("=" * 50)
      logger.info("Racetrack: http://%s/result.php?id=%s", racetrack.server, racetrack.testSetID)
      logger.info("=" * 50)
      racetrack.testSetEnd()
      os.chdir(cwd)


   def generateTestCert(self):
      logger.info('Generating test certs for "/Unit/CdkSsl/Verify/" cases.')
      if not os.path.exists(self.certSetupPath):
         logger.error('Can not find %s.', self.certSetupPath)
         sys.exit()
      cwd = os.getcwd()
      os.chdir(self.path)
      if sys.platform == 'win32':
         if not os.getenv('TCROOT'):
            logger.info('TCROOT is not set.')
            logger.info('Set TCROOT to N:\\')
            os.putenv('TCROOT', 'N:\\')
         proc = subprocess.Popen([self.certSetupPath, '>nul', '2>&1'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
         proc.wait()
      else:
         cmd = '"%s" > /dev/null 2>&1' % self.certSetupPath
         logger.info(cmd)
         proc = subprocess.Popen([cmd], shell=True, stdout=None, stderr=None)
         proc.wait()
      os.mkdir('gtk')
      os.chdir(cwd)
      logger.info('Finished Generating Test cert for "/Unit/CdkSsl/Verify/" cases.')

   def getRacetrackInfo(self):
      url = racetrack.getURL()
      self.racetrackInfo.extend(getRacetrackResult(url))
      self.racetrackInfo.append(url)
      self.racetrackInfo.append(racetrack.testSetID)


class RunTestViewAndroid(object):
   '''Execute test cases for testView(libcdk) on Android'''
   def __init__(self,
                aBuildInfo,
                extPath,
                caseNameFile = 'libcdk.txt',
                userName = 'SHD-API-PRECHECKIN',
                description = 'Libcdk'):
      self.bi = aBuildInfo
      self.caseNamePath = os.path.join(sys.path[0], caseNameFile)
      self.userName = userName
      self.description = description
      self.path = os.path.join(extPath, 'testE2E')
      self.path_device = '/data/data/testE2E/'
      self.testViewPath = os.path.join(self.path_device, 'testView.android')
      self.hostName = 'Android'


   def SetupTestEnv(self):
      logger.info('Start Setting up test environment ')
      proc = subprocess.Popen(['adb', 'shell'], shell=True, stdin=subprocess.PIPE) #stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      time.sleep(0.5)
      #Run as root
      proc.stdin.write('su\n')
      proc.stdin.write('mount -o rw,remount /\n')
      proc.stdin.write('mount -o rw,remount /system\n')
      proc.stdin.write('chmod 777 /\n')
      proc.stdin.write('chmod 777 /data/data\n')
      proc.stdin.write('chmod 777 /vendor/lib\n')
      proc.stdin.write('exit\n')
      proc.stdin.write('exit\n')
      proc.wait()
      #Run as normal user
      os.system('adb shell mkdir -p /tmp/')
      os.system('adb shell mkdir -p %s' % self.path_device)
      os.system('adb shell mkdir -p /vendor/lib/ndk/lib/armeabi/')
      os.system('adb push %s %s' % (os.path.join(self.path, 'testView.android'), self.path_device))
      os.system('adb shell chmod 777 %s' % self.testViewPath)
      os.system('adb push %s /vendor/lib/' % os.path.join(self.path, 'libwwwwclient.so'))
      os.system('adb push %s /vendor/lib/' % os.path.join(self.path, 'libgnustl_shared.so'))
      os.system('adb push %s /vendor/lib/ndk/lib/armeabi/' % os.path.join(self.path, 'libwwwwclient.so'))
      logger.info('Setting up test environment completed')


   def runTestCase(self,
                   caseName,
                   options):
      featureName = ''
      dbgLogPathFile = ''
      proc = subprocess.Popen(['adb', 'shell', self.testViewPath, '-p', caseName], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      (stdoutdata, stderrdata) = proc.communicate()
      logger.debug(stdoutdata)
      caseOutput = stdoutdata.splitlines()
      print caseOutput
      caseErr = stderrdata.splitlines()
      #Determine feature name by case name.
      if caseName.split('/')[1] == 'MainLoop':
         featureName = caseName.split('/')[1]
      else:
         featureName = ' '.join(caseName.split('/')[1:3])
      racetrack.testCaseBegin(caseName, featureName, "libcdk API test")
      for line in caseOutput:
         if line.find('Using log file') != -1:
            dbgLogPathFile = line.split('Using log file ')[1].rstrip()
      if caseOutput[-2].find(caseName) != -1 and caseOutput[-2].find('OK') != -1:
         logger.info('%s:OK', caseName)
         racetrack.testCaseEnd('PASS')
      elif caseOutput[-6].endswith('OK'):
         logger.info('%s:OK', caseName)
         racetrack.testCaseEnd('PASS')
      else:
         logger.info('%s:FAIL', caseName)
         logger.info('Uploading log file: %s', dbgLogPathFile)
         localLog = os.path.join(self.path, 'android.log')
         os.system('adb pull %s %s' % (dbgLogPathFile, localLog))
         racetrack.log('Debug log', localLog)
         os.remove(localLog)
         racetrack.comment(stdoutdata)
         racetrack.testCaseEnd('FAIL')


   def runTestCasesFromFile(self):
      logger.info('Reading test cases from %s', self.caseNamePath)
      #fd = codecs.open(self.caseNamePath, 'r', 'utf-8-sig')
      if not os.path.exists(self.caseNamePath):
         logger.error('Can not find %s.', self.caseNamePath)
         sys.exit()
      fd = open(self.caseNamePath, 'r')
      output = fd.readlines()
      fd.close()
      racetrack.testSetBegin(self.bi.buildId, self.userName, self.bi.product,
         self.description, self.hostName, BuildType=self.bi.releaseType,
         Branch=self.bi.branch)
      for line in output:
         if line.strip().startswith('/'):
            self.runTestCase(line.strip(), None)
      logger.info("=" * 50)
      logger.info("Racetrack: http://%s/result.php?id=%s", racetrack.server, racetrack.testSetID)
      logger.info("=" * 50)
      racetrack.testSetEnd()


class RunTestJscdk(object):
   '''Execute test cases for jscdk'''
   def __init__(self,
                aBuildInfo,
                extPath,
                caseNameFile = 'libcdk.txt',
                userName = 'SHD-API-PRECHECKIN',
                description = 'Jscdk'):
      self.bi = aBuildInfo
      self.path = os.path.join(extPath, 'testwebclient', 'jscdkapitest')
      self.caseNamePath = os.path.join(sys.path[0], caseNameFile)
      self.userName = userName
      self.description = description
      self.testJscdkPath = os.path.join(self.path, 'tests', 'qunit.html')
      self.logPath = os.path.join(self.path, 'debug.log')
      if sys.platform == 'linux2':
         self.hostName = 'Linux'
      elif sys.platform == 'darwin':
         self.hostName = 'Mac'
      elif sys.platform == 'win32':
         self.hostName = 'Windows'


   def runTestCasesAll(self):
      if sys.platform == 'win32':
         self.runTestCasesWin()
      elif sys.platform == 'linux2':
         self.runTestCasesLinux()
      else:
         logger.error('Jscdk tests are only supported on Windows and Linux.')
         sys.exit()


   def runTestCasesWin(self):
      logger.info('Start running jscdk test cases.')
      proc = subprocess.Popen(['N:\\win32\\chutzpah-2.2.1\\chutzpah.console.exe', self.testJscdkPath, '/debug', '>', self.logPath], shell=True, stdout=None, stderr=None)
      proc.wait()
      self.uploadResultWin()


   def runTestCasesLinux(self):
      #need to figure out why following doesn't work.
      sys.path.append('/build/toolchain/lin32/node-0.6.5/bin/')
      sys.path.append('/build/toolchain/lin32/phantomjs-1.7.0/bin/')
      cmd = '/build/toolchain/noarch/grunt-0124eb4/bin/grunt --config=%s/tests/grunt.js  --no-color > %s' % (self.path, self.logPath)
      logger.info(cmd)
      logger.info('Start running jscdk test cases.')
      proc = subprocess.Popen([cmd], shell=True, stdout=None, stderr=None)
      proc.wait()
      self.uploadResultLinux()


   def uploadResultLinux(self):
      if not os.path.exists(self.logPath):
         logger.error('Can not find %s.', self.logPath)
         sys.exit()
      file = open(self.logPath)
      racetrack.testSetBegin(self.bi.buildId, self.userName, self.bi.product,
         self.description, self.hostName, BuildType=self.bi.releaseType,
         Branch=self.bi.branch)
      line = file.readline()
      while(line):
         if line.find(r'****** Entering test case') != -1:
            caseLog = []
            caseName = line.split(r'******')[1].split(r'Entering test case')[1].strip()
            featureName = ' '.join(caseName.split('/')[1:3])
            racetrack.testCaseBegin(caseName, featureName, "jscdk API test")
            while(True):
               caseLog.append(line)
               line = file.readline()
               if line.startswith('.'):
                  logger.info('%s:OK', caseName)
                  racetrack.testCaseEnd('PASS')
                  break
               elif line.startswith('F'):
                  logger.info('%s:FAIL', caseName)
                  logger.info('Uploading log to racetrack.')
                  for eachLine in caseLog:
                     racetrack.comment(eachLine)
                     racetrack.testCaseEnd('FAIL')
                  break
         else:
            line = file.readline()
      logger.info("=" * 50)
      logger.info("Racetrack: http://%s/result.php?id=%s", racetrack.server, racetrack.testSetID)
      logger.info("=" * 50)
      file.close()
      racetrack.testSetEnd()


   def uploadResultWin(self):
      if not os.path.exists(self.logPath):
            logger.error('Can not find %s.', self.logPath)
            sys.exit()
      file = open(self.logPath)
      racetrack.testSetBegin(self.bi.buildId, self.userName, self.bi.product,
         self.description, self.hostName, BuildType=self.bi.releaseType,
         Branch=self.bi.branch)
      line = file.readline()
      while(line):
         if line.find(r'#_#TestStart#_#') != -1:
            caseName = line.split(r'"testName":"')[1].split(r'","testResults":')[0].strip()
            featureName = ' '.join(caseName.split('/')[1:3])
            caseLog = []
            racetrack.testCaseBegin(caseName, featureName, "jscdk API test")
            while True:
               line = file.readline()
               caseLog.append(line)
               if line.find(r'#_#TestDone#_#') != -1:
                  if line.find(caseName) != -1:
                     if line.find(r'"passed":true') != -1:
                        logger.info('%s:OK', caseName)
                        racetrack.testCaseEnd('PASS')
                     elif line.find(r'"passed":false') != -1:
                        logger.info('%s:FAIL', caseName)
                        logger.info('Uploading log to racetrack.')
                        for eachLine in caseLog:
                           racetrack.comment(eachLine)
                        racetrack.testCaseEnd('FAIL')
                     else:
                        logger.error('Incorrect log format: %s', line)
                        sys.exit()
                     break
                  else:
                     logger.error('Incorrect log format: %s', line)
                     sys.exit()
         line = file.readline()
      logger.info("=" * 50)
      logger.info("Racetrack: http://%s/result.php?id=%s", racetrack.server, racetrack.testSetID)
      logger.info("=" * 50)
      file.close()
      racetrack.testSetEnd()



class RunTestMacUT(object):
   '''Execute test cases for wwwwUnitTests(View Mac client UT)'''
   def __init__(self,
                aBuildInfo,
                extPath,
                #caseNameFile = 'libcdk.txt',
                userName = 'SHD-API-PRECHECKIN',
                description = 'MacUT'):
      self.bi = aBuildInfo
      #self.caseNamePath = os.path.join(sys.path[0], caseNameFile)
      self.userName = userName
      self.description = description
      if sys.platform == 'darwin':
         self.path = os.path.join(extPath, 'E2E')
         self.otestPath = '/build/toolchain/mac32/xcode-3.2-10a421/Tools/otest'
         self.testMacUTPath = os.path.join(self.path, 'wwwwUnitTests.octest', 'Contents', 'MacOS', 'wwwwUnitTests')
         self.hostName = 'Mac'


   def runTestCasesAll(self):
      logger.info('Running all test cases.')
      if not os.path.exists(self.testMacUTPath):
         logger.error('Can not find %s.', self.testMacUTPath)
         sys.exit()
      if not os.path.exists(self.otestPath):
         logger.error('Can not find %s.', self.otestPath)
         sys.exit()
      cwd = os.getcwd()
      os.chdir(self.path)
      cmd = 'arch -arch x86_64 %s %s/wwwwUnitTests.octest' % (self.otestPath, self.path)
      proc = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      time.sleep(20)
      racetrack.testSetBegin(self.bi.buildId, self.userName, self.bi.product,
         self.description, self.hostName, BuildType=self.bi.releaseType,
         Branch=self.bi.branch)
      caseName = ''
      featureName = ''
      while(True):
         line = proc.stdout.readline()
         logger.info(line.strip())
         if not line:
            break
         if line.find('Test Case') == 0 and line.find('started') != -1:
            featureName = 'wwwwUnitTests'
            caseName = line.split('wwwwUnitTests')[1].split(']')[0].strip()
            racetrack.testCaseBegin(caseName, featureName, "Mac UT test")
         if line.find(caseName) != -1 and line.find('passed') != -1:
            racetrack.testCaseEnd('PASS')
         if line.find(caseName) != -1 and line.find('failed') != -1:
            racetrack.testCaseEnd('FAIL')
      proc.wait()
      logger.info("=" * 50)
      logger.info("Racetrack: http://%s/result.php?id=%s", racetrack.server, racetrack.testSetID)
      logger.info("=" * 50)
      racetrack.testSetEnd()
      os.chdir(cwd)

class RunTestWebClient(object):
   '''Execute test cases for webclient'''
   def __init__(self,
                aBuildInfo,
                extPath,
                caseNameFile = 'libcdk.txt',
                userName = 'SHD-API-PRECHECKIN',
                description = 'webclient'):
      self.bi = aBuildInfo
      self.path = os.path.join(extPath, 'testwebclient', 'jscdkapitest')
      self.caseNamePath = os.path.join(sys.path[0], caseNameFile)
      self.userName = userName
      self.description = description
      #self.logPath = os.path.join(self.path, 'debug.log')      
      if sys.platform == 'linux2':
         self.hostName = 'Linux'
      elif sys.platform == 'darwin':
         self.hostName = 'Mac'
      elif sys.platform == 'win32':
         self.hostName = 'Windows'


   def setupTestEnv(self):
      if sys.platform == 'win32':
         self.runningDir = r'C:\Users\Administrator\AppData\Roaming'
         self.testBinaryDir =r'C:\build\testwebclient\webclientapitest'        
         commands = [r'rmdir /s /q %runningDir%\web %runningDir%\npm\API %runningDir%\npm\config %runningDir%\npm\lib',
                     r'del /f /q %runningDir%\npm\test-results.xml %runningDir%\npm\bower.json %runningDir%\npm\Gruntfile.js %runningDir%\npm\package.json %runningDir%\npm\README.md',
                     r'xcopy %testBinaryDir%\web %runningDir%\web /e /i /h',
                     r'xcopy %testBinaryDir%\test\* %runningDir%\npm /e /i /h'
                     ]
         for cmd in commands:
            cmd = cmd.replace('%runningDir%',self.runningDir)
            cmd = cmd.replace('%testBinaryDir%',self.testBinaryDir)
            logger.info(cmd)
            os.system(cmd)
         self.logPath = os.path.join(self.runningDir, 'npm\\test-results.xml')
         workingPath = os.path.join(self.runningDir, 'npm')
         os.chdir(workingPath)
         logger.info('Current working dir: ' + os.getcwd())
      elif sys.platform == 'linux2':
         logger.info('TBD')
      else:
         logger.error('Jscdk tests are only supported on Windows and Linux.')
         sys.exit()

   def runTestCasesAll(self):
      if sys.platform == 'win32':
         self.runTestCasesWin()
      elif sys.platform == 'linux2':
         self.runTestCasesLinux()
      else:
         logger.error('Jscdk tests are only supported on Windows and Linux.')
         sys.exit()


   def runTestCasesWin(self):
      logger.info('Start running webclient test cases.')
      proc = subprocess.Popen('grunt test >test.log 2>&1', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      proc.wait()
      self.uploadResultWin()

   def runTestCasesLinux(self):
      logger.info('TBD')

   def uploadResultLinux(self):
      logger.info('TBD')

   def uploadResultWin(self):
      if not os.path.exists(self.logPath):
            logger.error('Can not find %s.', self.logPath)
            sys.exit()
      file = open(self.logPath,'r')
      racetrack.testSetBegin(self.bi.buildId, self.userName, self.bi.product,
         self.description, self.hostName, BuildType=self.bi.releaseType,
         Branch=self.bi.branch)
      data = file.read()
      file.close()
      dom = parseString(data)
      testcaseList = dom.getElementsByTagName('testcase')
      for item in testcaseList:
         caseName = item.attributes['name'].value
         featureName = ""
         caseLog = []
         racetrack.testCaseBegin(caseName, featureName, "webclient API test")
         #process a successful test case
         if (len(item.childNodes) < 2):
            logger.info('%s:OK', caseName)
            racetrack.testCaseEnd('PASS')
         #process a failed test case
         else:
            logger.info('%s:FAIL', caseName)
            logger.info('Uploading log to racetrack.')
            node = item.childNodes[1]
            #get failure message
            if node.toxml().find(r'failure type=""') != -1:
               racetrack.comment(node.firstChild.data)
            racetrack.testCaseEnd('FAIL')
      logger.info("=" * 50)
      logger.info("Racetrack: http://%s/result.php?id=%s", racetrack.server, racetrack.testSetID)
      logger.info("=" * 50)
      racetrack.testSetEnd()
