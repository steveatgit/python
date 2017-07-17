#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module is used to handle any threads related racetrack.

Purpose:
   Class <Racetrack> should be singleton.
"""

import os
import os.path
import sys
import time
import datetime
import re
import csv
import string
import urllib2
import urllib2_file
from xml.dom.minidom import parseString
import xml.parsers.expat

# Import self modules
from log import logger

class Singleton(type):
   def __init__(cls, name, bases, dict):
      super(Singleton, cls).__init__(name, bases, dict)
      cls._instance = None

   def __call__(cls, *args, **kwargs):
      if cls._instance is None:
         cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
      return cls._instance

class Racetrack():
   __metaclass__ = Singleton
   testTypes     = ['BATS', 'Smoke', 'Regression', 'DBT', 'Unit', 'Performance']
   langs         = ['English', 'Japanese', 'French', 'Italian', 'German', 'Spanish',
                    'Portuguese', 'Chinese', 'Korean']
   resultTypes   = ['PASS', 'FAIL', 'RUNNING', 'CONFIG','SCRIPT', 'PRODUCT',
                    'RERUNPASS', 'UNSUPPORTED']
   verifyResults = ['TRUE', 'FALSE']

   def __init__(self, enabled = True, advanced = False, testSetID = None,
                      testCaseID = None, testCaseResult = None):
      self.enabled = enabled
      self.advanced = advanced
      self.testSetID = testSetID
      self.testCaseID = testCaseID
      self.testCaseResult = testCaseResult
      self.server = None
      self.htp = None

   def __call__(self):
      pass

   def _post(self, method, data):
      if re.search(r'dev', self.server):
         self.htp = r'http'
      else:
         self.htp = r'https'
      url = '%s://%s/%s' % (self.htp, self.server, method)
      for key in data.keys():
         if data[key] == None:
            del data[key]
         else:
            if isinstance(data[key], unicode):
               data[key] = data[key].encode('utf-8')
            if not isinstance(data[key], basestring) and \
               not isinstance(data[key], dict):
               data[key] = str(data[key])

         if self.enabled:
            logger.debug('Racetrack post to %s: %s' % (url, data))
            try:
               null_proxy_handler = urllib2.ProxyHandler({})
               urllib2._opener = urllib2.build_opener(null_proxy_handler)
               result = urllib2.urlopen(url, data)
               result = result.read().decode('utf-8')
               logger.debug('Racetrack server resturned: %s' % result)
               return result
            except Exception, e:
               logger.error('Connect to web service error: %s' % e)
               logger.error('URL: %s\nData: %s' % (url, data))
               return False
         else:
            logger.debug('Racetrack diabled - Skipped post to %s: %s' %
                  (url, data))
            return True

   def geturl(self, ID = None):
      if ID is not None and self.advanced:
         self.testSetID = ID

      if self.testSetID is None:
         logger.error('geturl invoked with no active test set')
         return False

      if self.testSetID == True:
         return 'No url available.\nTest set created with racetrack.enable = Flase'

      return '%s://%s/result.php?id=%s' % (self.htp, self.server, self.testSetID)

   def getTokenValue(self, product, token, lang):
      '''
      getTokenValue - Retrieve a token from the Racetrack g11n database
      '''
      data = {'product':  product,
              'toke':     token,
              'language': lang
              }
      result = self._post('gettestdatavalue.php', data)
      return result

   def verify(self, description, actual, expected, result = None,
                    screenshot = None, resultID = None):
      '''
      verify - Validate the actual matches the expected
      '''
      if resultID is not None and self.advanced:
         self.testCaseID = resultID

      if self.testCaseID is None:
         logger.error('verify invoked but there is no active test case')
         return False

      if result is None:
         if expected == actual:
            result = 'TRUE'
         else:
            result = 'FALSE'
            self.testCaseResult = 'FAIL'
      else:
         if result not in self.__class__.verifyResults:
            logger.error('Specified result is not valid')
            return False
         if result == 'FAIL':
            self.testCaseResult = 'FAIL'

      data = {'Description': description,
              'Actual':      actual,
              'Expected':    expected,
              'Result':      result,
              'ResultID':    self.testCaseID
              }

      if screenshot is not None:
         if not os.path.exists(screenshot):
            logger.error('Screenshot to be uploaded not found: %s' % screenshot)
            return False
         data['Screenshot'] = {'fd':       open(screenshot),
                               'filename': os.path.basename(screenshot)
                               }

      result = self._post('TestCaseVerification.php', data)
      return expected == actual

   def testSetBegin(self, buildID = None, user = None, product = None,
                          description = None, hostOS = None, serverBuildID = None,
                          branch = None, buildType = None, testType = None, lang = None):
      '''
      testSetBegin - Begin a new test set in Racetrack.

      Returns a new test set ID when successfully or False when failure.
      Parameters:
         Please refer to Racetrack help documentation:
            https://wiki.eng.vvvvvv.com/RacetrackWebServices
      '''
      if self.testSetID is not None and not self.advanced:
         logger.error('A test set (ID %s) has already begun in Racetrack' %
               self.testSetID)
         return False

      if lang is not None and lang not in self.__class__.langs:
         logger.error('Specified language is invalid')
         return False

      if testType is not None and testType not in self.__class__.testTypes:
         logger.error('Specified test type is invalid')
         return False

      data = {'BuildID':       buildID,
              'User':          user,
              'Product':       product,
              'Description':   description,
              'HostOS':        hostOS,
              'ServerBuildID': serverBuildID,
              'Branch':        branch,
              'BuildType':     buildType,
              'TestType':      testType,
              'Language':      lang
              }

      result = self._post('TestSetBegin.php', data)
      if result:
         self.testSetID = result
         logger.info('New test set started at %s' % self.geturl())

      return result

   def testSetUpdate(self, ID = None, buildID = None, user = None, product = None,
                          description = None, hostOS = None, serviceBuildID = None,
                          branch = None, buildType = None, testType = None, lang = None):
      '''
      testSetUpdate - Update test set data after created.
      '''
      if ID is not None and self.advanced:
         self.testSetID = ID

      if self.testSetID is None:
         logger.error('testSetUpdate invoked but there is no active test set!')
         return False

      if lang is not None and lang not in self.__class__.langs:
         logger.error('Specified language is invalid')
         return False

      if testType is not None and testType not in self.__class__.testTypes:
         logger.error('Specified test type is invalid')
         return False

      data = {'ID':            self.testSetID,
              'BuildID':       buildID,
              'User':          user,
              'Product':       product,
              'Description':   description,
              'HostOS':        hostOS,
              'ServerBuildID': serverBuildID,
              'Branch':        branch,
              'BuildType':     buildType,
              'TestType':      testType,
              'Language':      lang
              }
      result = self._post('TestSetUpdate.php', data)
      return result

   def testSetData(self, name, value, resultSetID = None):
      '''
      testSetData - Update result set with additional data.
      '''
      if resultSetID is not None and self.advanced:
         self.testSetID = resultSetID

      if self.testSetID is None:
         logger.error('testSetData invoked but there is no active test set')
         return False

      data = {'ID':    self.testSetID,
              'Name':  name,
              'Value': value
              }
      result = self._post('TestSetData.php', data)
      return result

   def testSetEnd(self, ID = None):
      if ID is not None and self.advanced:
         self.testSetID = ID

      if self.testSetID is None:
         logger.error('testSetEnd invoked but there is no active test set')
         return False

      data = {'ID': self.testSetID}
      result = self._post('TestSetEnd.php', data)
      self.testSetID = None
      return result

   def testCaseBegin(self, name, feature, description = None, machineName = None,
                           tcmsID = None, inputLang = None, resultSetID = None):
      '''
      testCaseBegin - Start a new test case
      '''
      if resultSetID is not None and self.advanced:
         self.testSetID = resultSetID

      if self.testCaseID is not None and not self.advanced:
         logger.error('A test case (ID: %s) has already begun in Racetrack' %
               self.testCaseID)
         return False

      data = {'Name':          name,
              'Feature':       feature,
              'Description':   description,
              'MachineName':   machineName,
              'TCMSID':        tcmsID,
              'InputLanguage': inputLang,
              'ResultSetID':   self.testSetID
              }
      result = self._post('TestCaseBegin.php', data)
      if result is not False:
         self.testCaseID = result
         self.testCaseResult = 'PASS'
      return result

   def testCaseTriage(self, ID = None, result = None, bugNo = None, comment = ''):
      '''
      testCaseTriage - triage failed testcases
      '''
      if ID is not None and self.advanced:
         self.testCaseID = ID

      if self.testCaseID is None:
         logger.error('testCaseTriage invoked but there is no active test case')
         return False

      if result is None or result not in self.resultTypes:
         logger.error('Specified the result is invali')
         return False

      data = {'ID':        self.testCaseID,
              'Result':    result,
              'bugnumber': bugNo,
              'comment':   comment
              }
      result = self._post('TestCaseTriage.php', data)
      return result

   def uploadScreenshot(self, description, screenshot, resultID = None):
      '''
      uploadScreenshot - Upload a screenshot
      '''
      if resultID is not None and self.advanced:
         self.testCaseID = resultID

      if self.testCaseID is None:
         logger.error('uploadScreenshot invoked but there is no active test case')
         return False

      if not os.path.exists(screenshot):
         logger.error('Screenshot file to be uploaded not found: %s' % screenshot)
         return False

      data = {'Description': description,
              'ResultID':    self.testCaseID,
              'Screenshot':  {'fd':       open(screenshot),
                              'filename': os.path.basename(screenshot)}
              }
      result = self._post('TestCaseScreenshot.php', data)
      return result

   def uploadLog(self, description, logFile, resultID = None):
      '''
      uploadLog - Upload log file to Racetrack server
      '''
      if resultID is not None and self.advanced:
         self.testCaseID = resultID

      if self.testCaseID is None:
         logger.error('Log file to be uploaded not found: %s' % logFile)
         return False

      data = {'Description': description,
              'ResultID':    self.testCaseID,
              'Log': {'fd':       open(os.path.expanduser(logFile), 'rb'),
                      'filename': os.path.basename(logFile)}
              }
      result = self._post('TestCaseLog.php', data)
      return result

   def testCaseEnd(self, result = None, ID = None):
      '''
      testCaseEnd - End a test case
      '''
      if ID is not None and self.advanced:
         self.testCaseID = ID

      if self.testCaseID is not None:
         if result not in self.__class__.resultTypes:
            logger.error('Specified the result is invalid')
            return False
         else:
            self.testCaseResult = result

      data = {'Result': self.testCaseResult,
              'ID':     self.testCaseID
              }
      result = self._post('TestCaseEnd.php', data)
      self.testCaseID = None
      return result

   def getResult(self):
      url = self.geturl()
      f = urllib2.urlopen(url)
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
      return (-1, -1)

   def addComment(self, comment = None, resultID = None):
      '''
      Add comment to the test case.
      '''

      if resultID is not None and self.advanced:
         self.testCaseID = resultID

      if self.testCaseID is None:
         logger.error('Can not find the case id.')
         return False

      args = {'ResultID' : self.testCaseID,
              'Description' : comment.encode('utf-8'),
              }
      result = self._post('TestCaseComment.php', args)
      return result

class UploadBoostLog():
   def __init__(self, logPath = r'', protocol=r'', infoFile = r'', ):
      self.logPath        = logPath
      self.protocol       = protocol
      self.infoFile       = infoFile
      self.buildNo        = ''
      self.hostOS         = ''
      self.branch         = ''
      self.buildType      = ''
      self.machine        = ''
      self.role           = 'Agent'
      self.vOS            = ''
      self.setOS          = ''
      self.machineName    = ''
      self.setMachineName = ''
      # Parameters for function <parseLogFile>
      self.title          = 'API_TEST'
      self.caseBegin      = ''
      self.suiteBegin     = ''
      self.logFullName    = []
      self.parent         = ''
      self.racetrack      = Racetrack()
      # Parameters - Racerack related
      self.username       = 'SHD-API'
      self.product        = 'ViewAPI'
      self.description    = 'SHD-API Test'
      self.racetrackInfo  = []

   def __call__(self, server = ''):
         # Upload process startup here
         logger.info('Upload process startup here...')
         self.parseEnvFile()
         if server == 'dev':
            self.racetrack.server = 'racetrack-dev.eng.vvvvvv.com'
            self.username = 'SHD-API-PRECHECKIN'
         else:
            self.racetrack.server = 'racetrack.eng.vvvvvv.com'

         self.racetrack.testSetBegin(self.buildNo, self.username, self.product,
                                     self.description, self.hostOS, None,
                                     self.branch, self.buildType, None, None)

         for parent, dirnames, filenames in os.walk(self.logPath):
            for filename in filenames:
               if filename.find('.log') > -1 and filename.find('result.log') == -1 and filename.find('pcoipTestServer') == -1:
                  self.parseLogFile(os.path.join(parent, filename))

         self.racetrack.testSetEnd()
         return self.racetrackInfo

   def parseEnvFile(self):
      loadEnvFile = os.path.join(self.logPath, r'LoadEnv.bat')
      with open(loadEnvFile) as fp:
         for roleLine in fp:
            if roleLine.find('MYROLE') > -1:
               self.role = roleLine.split('=')[1].strip()
               logger.info('Role: %s' % self.role)
               self.vOS = '%s.Properties.OS' % self.role
               self.machineName = '%s.MachineName' % self.role
               self.setMachineName = 'set %s' % self.machineName
               break

         fp.seek(0)

         for eachLine in fp:
            if eachLine.find('set BuildNo') > -1:
               self.buildNo = eachLine.split('=')[1].strip()
               logger.info('BuildNo: %s' % self.buildNo)
               continue

            if eachLine.find('Build.Racetrack') > -1:
               self.buildNo = eachLine.split('=')[1].strip()
               logger.info('BuildNo: %s' % self.buildNo)
               continue

            if eachLine.find(self.vOS) > -1:
               self.hostOS = eachLine.split('=')[1].strip()
               logger.info('HostOS: %s' % self.hostOS)
               continue

            if eachLine.find('set Branch') > -1:
               self.branch = eachLine.split('=')[1].strip()
               logger.info('Branch: %s' % self.branch)
               continue

            if eachLine.find(self.machineName) > -1:
               self.machine = eachLine.split('=')[1].strip()
               logger.info('Machine: %s' % self.machine)
               continue

            if eachLine.find('BuildType') > -1:
               self.buildType = eachLine.split('=')[1].strip()
               logger.info('BuildType: %s' % self.buildType)
               continue

   def getTCMapping(self, bug = False, result = False):
      '''
      Get the bug which blocks the test case and generate mapping
      '''
      rawMapping = r''
      tcDict = {}
      exData = []
      if bug:
         rawMapping = r'./utils/bug.csv'
      elif result:
         rawMapping = r'./utils/result.csv'
      with open(rawMapping, 'rb') as fp:
         content = csv.DictReader(fp)
         for item in content:
            exData.append(item)
         for item in exData:
            if bug:
               tcDict[item['testcase']] = str(item['bugid'])
            elif result:
               tcDict[item['testcase']] = str(item['result'])
      return tcDict

   def parseLogFile(self, filename):
      caseName = ''
      ret = 'PASS'
      caseLog = None
      caseBegin = False
      flog = None
      self.title = '[%s] - %s' % (self.protocol,
                                  os.path.splitext(os.path.basename(filename))[0])
      self.parent = os.path.dirname(filename)
      logger.info('Group name is: %s' % self.title)

      with open(filename) as fp:
         for eachLine in fp:
            if ((eachLine.find('Leaving test case ') > -1 or \
                eachLine.find('Entering test case ') > -1) or \
               (eachLine.find('[       OK ]') > -1 or \
                eachLine.find('[  FAILED  ]') > -1)) and caseBegin:
               caseBegin = False
               flog.flush()
               flog.close()
               for uploadLog in self.logFullName:
                  if uploadLog.find('pcoipTestServer') == -1:
                     try:
                        self.racetrack.uploadLog('AttachedLog', uploadLog)
                        os.remove(uploadLog)
                     except IOError, err:
                        logger.error(err)
                     continue

                  self.racetrack.uploadLog(uploadLog, uploadLog)

               if (ret == 'FAIL' and
                   caseName in self.getTCMapping(result = True) and
                   caseName in self.getTCMapping(bug = True)):
                  self.racetrack.testCaseTriage(
                        result = self.getTCMapping(result = True)[caseName],
                        bugNo = self.getTCMapping(result = True)[caseName])
               else:
                  self.racetrack.testCaseEnd(ret)
               logger.info('Loading %s - %s' % (caseName, ret))
               ret = 'PASS'
               caseName = ''
               self.logFullName = []

            if eachLine.find('Entering test case ') > -1 or \
				   eachLine.find('[ RUN      ]') > -1:
               caseBegin = True
               # caseName = re.match('.*"(\w+)"', eachLine).group(1)
               # Use a unsafe trick
               caseName = eachLine.split(' ')[-1].strip()
               self.racetrack.testCaseBegin(caseName, self.title,
                                            None, self.machine)

               # Create log file for each case
               logPrefix = datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S")
               logDirName = os.path.dirname(filename)
               self.logFullName.append(os.path.join(logDirName,
                                       (logPrefix + '_log.txt')))
               flog = open(self.logFullName[0], 'wb')
               flog.write('Case Log: \n')
               continue

            if caseBegin:
               if (eachLine.find('[  FAILED  ]') > -1) or \
					   (eachLine.find('error') > -1 and eachLine.find('error code 0') <= -1) or \
                  (eachLine.find('F201') > -1) or \
                  (eachLine.find('E201') > -1):
                  ret = 'FAIL'

               flog.write(eachLine)

               if eachLine.find('.log') > -1:
                  m1 = re.search('cata_fwPlugin\w+pcoipTestServer.exe_\w+', eachLine)
                  m2 = re.search('\w+\.\w+\.\w+\.log', eachLine)
                  if m1 and m2:
                     self.logFullName.append(m1.group() + ' ' + m2.group())

      self.racetrackInfo.extend(self.racetrack.getResult())
      self.racetrackInfo.append(self.racetrack.geturl())
      self.racetrackInfo.append(self.racetrack.testSetID)


class UploadJSCDKLog():
   def __init__(self, logPath = r'', protocol=r'', infoFile = r'', ):
      self.logPath        = logPath
      self.protocol       = protocol
      self.infoFile       = infoFile
      self.logBaseName    = 'jscdk_debug.log'
      self.buildNo        = ''
      self.hostOS         = ''
      self.branch         = ''
      self.buildType      = ''
      self.machine        = ''
      self.role           = 'Agent'
      self.vOS            = ''
      self.setOS          = ''
      self.machineName    = ''
      self.setMachineName = ''
      # Parameters for function <parseLogFile>
      self.title          = 'API_TEST'
      self.caseBegin      = ''
      self.suiteBegin     = ''
      self.logFullName    = []
      self.parent         = ''
      self.racetrack      = Racetrack()
      # Parameters - Racerack related
      self.username       = 'SHD-API'
      self.product        = 'ViewAPI'
      self.description    = 'SHD-API Test'
      self.racetrackInfo  = []

   def __call__(self, server = 'dev'):
         # Upload process startup here
         logger.info('Upload process startup here...')
         self.parseEnvFile()
         if server == 'dev':
            self.racetrack.server = 'racetrack-dev.eng.vvvvvv.com'
            self.username = 'SHD-API-PRECHECKIN'
         else:
            self.racetrack.server = 'racetrack.eng.vvvvvv.com'

         self.racetrack.testSetBegin(self.buildNo, self.username, self.product,
                                     self.description, self.hostOS, None,
                                     self.branch, self.buildType, None, None)

         self.parseLogFile()
         self.racetrack.testSetEnd()
         return self.racetrackInfo

   def parseEnvFile(self):
      loadEnvFile = os.path.join(self.logPath, r'LoadEnv.bat')
      with open(loadEnvFile) as fp:
         for roleLine in fp:
            if roleLine.find('MYROLE') > -1:
               self.role = roleLine.split('=')[1].strip()
               logger.info('Role: %s' % self.role)
               self.vOS = '%s.Properties.OS' % self.role
               self.machineName = '%s.MachineName' % self.role
               self.setMachineName = 'set %s' % self.machineName
               break

         fp.seek(0)

         for eachLine in fp:
            if eachLine.find('set BuildNo') > -1:
               self.buildNo = eachLine.split('=')[1].strip()
               logger.info('BuildNo: %s' % self.buildNo)
               continue

            if eachLine.find('Build.Racetrack') > -1:
               self.buildNo = eachLine.split('=')[1].strip()
               logger.info('BuildNo: %s' % self.buildNo)
               continue

            if eachLine.find(self.vOS) > -1:
               self.hostOS = eachLine.split('=')[1].strip()
               logger.info('HostOS: %s' % self.hostOS)
               continue

            if eachLine.find('set Branch') > -1:
               self.branch = eachLine.split('=')[1].strip()
               logger.info('Branch: %s' % self.branch)
               continue

            if eachLine.find(self.machineName) > -1:
               self.machine = eachLine.split('=')[1].strip()
               logger.info('Machine: %s' % self.machine)
               continue

            if eachLine.find('BuildType') > -1:
               self.buildType = eachLine.split('=')[1].strip()
               logger.info('BuildType: %s' % self.buildType)
               continue

   def parseLogFile(self):
      caseName = ''
      ret = 'PASS'
      caseLog = None
      caseBegin = False
      flog = None
      if not os.path.exists(self.logPath):
            logger.error('Can not find %s.', self.logPath)
            sys.exit()

      file = open(os.path.join(self.logPath, self.logBaseName))
      line = file.readline()
      while(line):
         if line.find(r'#_#TestStart#_#') != -1:
            # Write the log.
            logPrefix = datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S")
            self.logFullName.append(os.path.join(self.logPath, logPrefix + '_log.txt'))
            flog = open(self.logFullName[0],'wb')
            # Extract the case name from the log.
            caseName = line.split(r'"testName":"')[1].split(r'","testResults":')[0].strip()
            featureName = ' '.join(caseName.split('/')[1:3])
            caseLog = []
            self.racetrack.testCaseBegin(caseName, featureName, "jscdk API test")

            while True:
                # Create log file for each case
                flog.write(line)
                line = file.readline()

                if line.find(r'#_#TestDone#_#') != -1:
                    flog.write(line)
                    flog.close()

                    #upload the log
                    try:
                        self.racetrack.uploadLog('Attachment', self.logFullName[0])
                        os.remove(self.logFullName[0])
                    except IOError, err:
                        logger.error(err)
                    #upload log info to racetrack, fail or pass
                    if line.find(caseName) != -1:
                        if line.find(r'"passed":false') != -1:
                            logger.info('%s:FAIL', caseName)
                            logger.info('Uploading log to racetrack.')
                            self.racetrack.testCaseEnd('FAIL')
                        elif line.find(r'"passed":true') != -1:
                            logger.info('%s:OK', caseName)
                            self.racetrack.testCaseEnd('PASS')
                        else:
                            logger.error('Incorrect log format: %s', line)
                            sys.exit()
                        break
                    else:
                        logger.error('Incorrect log format: %s', line)
                        sys.exit()

         line = file.readline()
      logger.info("=" * 50)
      logger.info("Racetrack: %s://%s/result.php?id=%s",
                  self.racetrack.htp,
                  self.racetrack.server,
                  self.racetrack.testSetID)
      logger.info("=" * 50)
      file.close()
      self.racetrackInfo.extend(self.racetrack.getResult())
      self.racetrackInfo.append(self.racetrack.geturl())
      self.racetrackInfo.append(self.racetrack.testSetID)

class UploadWebclientLog():
   def __init__(self, logPath = r'', protocol=r'', infoFile = r'', ):
      self.logPath        = logPath
      self.protocol       = protocol
      self.infoFile       = infoFile
      self.logBaseName    = 'test-results.xml'
      self.buildNo        = ''
      self.hostOS         = ''
      self.branch         = ''
      self.buildType      = ''
      self.machine        = ''
      self.role           = 'Agent'
      self.vOS            = ''
      self.setOS          = ''
      self.machineName    = ''
      self.setMachineName = ''
      # Parameters for function <parseLogFile>
      self.title          = 'API_TEST'
      self.caseBegin      = ''
      self.suiteBegin     = ''
      self.logFullName    = []
      self.parent         = ''
      self.racetrack      = Racetrack()
      # Parameters - Racerack related
      self.username       = 'SHD-API'
      self.product        = 'ViewAPI'
      self.description    = 'SHD-API Test'
      self.racetrackInfo  = []

   def __call__(self, server = 'dev'):
         # Upload process startup here
         logger.info('Upload process startup here...')
         self.parseEnvFile()
         if server == 'dev':
            self.racetrack.server = 'racetrack-dev.eng.vvvvvv.com'
            self.username = 'SHD-API-PRECHECKIN'
         else:
            self.racetrack.server = 'racetrack.eng.vvvvvv.com'

         self.racetrack.testSetBegin(self.buildNo, self.username, self.product,
                                     self.description, self.hostOS, None,
                                     self.branch, self.buildType, None, None)

         self.parseLogFile()
         self.racetrack.testSetEnd()
         return self.racetrackInfo

   def parseEnvFile(self):
      loadEnvFile = os.path.join(r'C:\tools\vlogs', r'LoadEnv.bat')
      with open(loadEnvFile) as fp:
         for roleLine in fp:
            if roleLine.find('MYROLE') > -1:
               self.role = roleLine.split('=')[1].strip()
               logger.info('Role: %s' % self.role)
               self.vOS = '%s.Properties.OS' % self.role
               self.machineName = '%s.MachineName' % self.role
               self.setMachineName = 'set %s' % self.machineName
               break

         fp.seek(0)

         for eachLine in fp:
            if eachLine.find('set BuildNo') > -1:
               self.buildNo = eachLine.split('=')[1].strip()
               logger.info('BuildNo: %s' % self.buildNo)
               continue

            if eachLine.find('Build.Racetrack') > -1:
               self.buildNo = eachLine.split('=')[1].strip()
               logger.info('BuildNo: %s' % self.buildNo)
               continue

            if eachLine.find(self.vOS) > -1:
               self.hostOS = eachLine.split('=')[1].strip()
               logger.info('HostOS: %s' % self.hostOS)
               continue

            if eachLine.find('set Branch') > -1:
               self.branch = eachLine.split('=')[1].strip()
               logger.info('Branch: %s' % self.branch)
               continue

            if eachLine.find(self.machineName) > -1:
               self.machine = eachLine.split('=')[1].strip()
               logger.info('Machine: %s' % self.machine)
               continue

            if eachLine.find('BuildType') > -1:
               self.buildType = eachLine.split('=')[1].strip()
               logger.info('BuildType: %s' % self.buildType)
               continue

   def parseLogFile(self):
      caseName = ''
      ret = 'PASS'
      caseLog = None
      caseBegin = False
      flog = None
      if not os.path.exists(self.logPath):
            logger.error('Can not find %s.', self.logPath)
            sys.exit()

      file = open(os.path.join(self.logPath, self.logBaseName))
      data = file.read()
      file.close()
      dom = parseString(data)
      testcaseList = dom.getElementsByTagName('testcase')
      for item in testcaseList:
         caseName = item.attributes['name'].value
         featureName = ""
         caseLog = []
         self.racetrack.testCaseBegin(caseName, featureName, "webclient API test")
         #process a successful test case
         if (len(item.childNodes) < 2):
            logger.info('%s:OK', caseName)
            self.racetrack.testCaseEnd('PASS')
         #process a failed test case
         else:
            logger.info('%s:FAIL', caseName)
            logger.info('Uploading log to racetrack.')
            node = item.childNodes[1]
            #get failure message
            if node.toxml().find(r'failure type=""') != -1:
               self.racetrack.comment(node.firstChild.data)
            self.racetrack.testCaseEnd('FAIL')
      logger.info("=" * 50)
      logger.info("Racetrack: %s://%s/result.php?id=%s",
                  self.racetrack.htp,
                  self.racetrack.server,
                  self.racetrack.testSetID)
      logger.info("=" * 50)

      self.racetrackInfo.extend(self.racetrack.getResult())
      self.racetrackInfo.append(self.racetrack.geturl())
      self.racetrackInfo.append(self.racetrack.testSetID)


class UploadXMLLog():
   def __init__(self, logPath = r'', protocol=r'', infoFile = r'', ):
      self.logPath        = logPath
      self.protocol       = protocol
      self.infoFile       = infoFile
      self.buildNo        = ''
      self.hostOS         = ''
      self.branch         = ''
      self.buildType      = ''
      self.machine        = ''
      self.role           = 'Agent'
      self.vOS            = ''
      self.setOS          = ''
      self.machineName    = ''
      self.setMachineName = ''
      # Parameters for function <parseLogFile>
      self.title          = 'API_TEST'
      self.caseBegin      = ''
      self.suiteBegin     = ''
      self.logFullName    = []
      self.parent         = ''
      self.racetrack      = Racetrack()
      # Parameters - Racerack related
      self.username       = 'SHD-API'
      self.product        = 'ViewAPI'
      self.description    = 'SHD-API Test'
      self.racetrackInfo  = []
      self.tcResult = 'PASS'
      self.inTC = False

   def __call__(self, server = 'dev0'):
         # Upload process startup here
         logger.info('Upload process startup here...')
         self.parseEnvFile()
         if server == 'dev':
            self.racetrack.server = 'racetrack-dev.eng.vvvvvv.com'
            self.username = 'SHD-API-PRECHECKIN'
         else:
            self.racetrack.server = 'racetrack.eng.vvvvvv.com'
            self.username = 'SHD-API-PRECHECKIN'

         self.racetrack.testSetBegin(self.buildNo, self.username, self.product,
                                     self.description, self.hostOS, None,
                                     self.branch, self.buildType, None, None)

         for parent, dirnames, filenames in os.walk(self.logPath):
            for filename in filenames:
               if filename.find('.xml') > -1 and filename.find('result.log') == -1 and filename.find('pcoipTestServer') == -1:
                  self.parseLogFile(os.path.join(parent, filename))

         self.racetrack.testSetEnd()
         return self.racetrackInfo

   def seHandler(self, name, attr):
      if not name: return
      name = name.lower()
      if name == 'testcase':
         self.racetrack.testCaseBegin(attr['name'], self.title, None, self.machine)
         self.inTC = True
      else:
         if name == 'failure': self.tcResult = 'FAIL'
         if self.inTC:
            self.racetrack.addComment(name)
            for key in attr.keys():
               self.racetrack.addComment(key); self.racetrack.addComment(attr[key])
      if attr and attr.has_key("result") and attr["result"].lower() != 'pass':
         self.tcResult = 'FAIL'

   def eeHandler(self, name):
      if not name: return
      name = name.lower()
      if name.lower() == 'testcase':
         self.racetrack.testCaseEnd(self.tcResult)
         self.tcResult = 'PASS'; self.inTC = False

   def dHandler(self, data):
      if not data: return
      if self.inTC:
         self.racetrack.addComment(data)

   def parseEnvFile(self):
      loadEnvFile = os.path.join(r'c:\\tools\\vlogs', r'LoadEnv.bat')
      with open(loadEnvFile) as fp:
         for roleLine in fp:
            if roleLine.find('MYROLE') > -1:
               self.role = roleLine.split('=')[1].strip()
               logger.info('Role: %s' % self.role)
               self.vOS = '%s.Properties.OS' % self.role
               self.machineName = '%s.MachineName' % self.role
               self.setMachineName = 'set %s' % self.machineName
               break
         fp.seek(0)
         for eachLine in fp:
            if eachLine.find('set BuildNo') > -1:
               self.buildNo = eachLine.split('=')[1].strip()
               logger.info('BuildNo: %s' % self.buildNo)
               continue

            if eachLine.find('Build.Racetrack') > -1:
               self.buildNo = eachLine.split('=')[1].strip()
               logger.info('BuildNo: %s' % self.buildNo)
               continue

            if eachLine.find(self.vOS) > -1:
               self.hostOS = eachLine.split('=')[1].strip()
               logger.info('HostOS: %s' % self.hostOS)
               continue

            if eachLine.find('set Branch') > -1:
               self.branch = eachLine.split('=')[1].strip()
               logger.info('Branch: %s' % self.branch)
               continue

            if eachLine.find(self.machineName) > -1:
               self.machine = eachLine.split('=')[1].strip()
               logger.info('Machine: %s' % self.machine)
               continue

            if eachLine.find('BuildType') > -1:
               self.buildType = eachLine.split('=')[1].strip()
               logger.info('BuildType: %s' % self.buildType)
               continue

   def getTCMapping(self, bug = False, result = False):
      '''
      Get the bug which blocks the test case and generate mapping
      '''
      rawMapping = r''
      tcDict = {}
      exData = []
      if bug:
         rawMapping = r'./utils/bug.csv'
      elif result:
         rawMapping = r'./utils/result.csv'
      with open(rawMapping, 'rb') as fp:
         content = csv.DictReader(fp)
         for item in content:
            exData.append(item)
         for item in exData:
            if bug:
               tcDict[item['testcase']] = str(item['bugid'])
            elif result:
               tcDict[item['testcase']] = str(item['result'])
      return tcDict

   def parseLogFile(self, filename):
      self.title = '[%s] - %s' % (self.protocol,
                                  os.path.splitext(os.path.basename(filename))[0])
      self.parent = os.path.dirname(filename)
      logger.info('Group name is: %s' % self.title)

      with open(filename) as fp:
         print filename
         lp = xml.parsers.expat.ParserCreate()
         lp.StartElementHandler = self.seHandler
         lp.EndElementHandler = self.eeHandler
         lp.CharacterDataHandler = self.dHandler
         lp.ParseFile(fp)

      self.racetrackInfo.extend(self.racetrack.getResult())
      self.racetrackInfo.append(self.racetrack.geturl())
      self.racetrackInfo.append(self.racetrack.testSetID)

if __name__ == '__main__':
   '''
   one = Racetrack()
   two = Racetrack()
   two.a = 123
   print(one.a)
   '''

   a = Racetrack(advanced = True)
   print '[Debug]: 00'
   b = UploadBoostLog(logPath = "c:\\racetrack\\smartcard", protocol="PCoIP")
   b()
