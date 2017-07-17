#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import os.path
import sys
import csv
import time
import re
import codecs


from log import logger
from xml.etree.ElementTree import \
      ElementTree,\
      Element,\
      SubElement,\
      Comment,\
      tostring

class Reporter():
   '''
   This is class is used to handle result log.
   1. Add JUnit format support
   '''
   def __init__(self, testsuite = '', logPath = r''):
      self.testsuite = testsuite
      self.logPath = logPath

   def __call__(self):
      self.resultToJUnit()

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

   def resultToJUnit(self):
      caseName   = ''
      ret        = 'PASS'
      errorMsg   = ''
      caseLog    = None
      caseBegin  = False
      flog       = None
      testsuites = Element('testsuites')
      testsuite  = SubElement(testsuites, 'testsuite')
      testcase   = None
      vlogPath   = r''
      fileSuffix = '.xml'
      testsuite.set('name', self.testsuite)
      logger.info('Group name is: %s' % self.testsuite)
      with codecs.open(self.logPath, 'r', encoding='latin-1') as fp:
         for eachLine in fp:
            if ((eachLine.find('[       OK ]') > -1 or \
                eachLine.find('[  FAILED  ]') > -1) or \
               (eachLine.find('Leaving test case ') > -1 or \
                eachLine.find('Entering test case ') > -1)) and caseBegin:
               caseBegin = False
               if (ret == 'FAIL' and
                   caseName in self.getTCMapping(result = True) and
                   caseName in self.getTCMapping(bug = True)):
                  result = self.getTCMapping(result = True)[caseName]
                  bugNo = self.getTCMapping(result = True)[caseName]
                  bugset = SubElement(testcase, 'bug')
                  bugset.set('Bug', bugNo)
               testcase = SubElement(testsuite, 'testcase')
               testcase.set('name', caseName)
               testcase.set('result', ret)
               if ret == 'FAIL':
                  errNode = SubElement(testcase, 'error')
                  errNode.text = errorMsg
               errorMsg = ''
               ret = 'PASS'
               caseName = ''
            if eachLine.find('[ RUN      ]') > -1:
               caseBegin = True
               # caseName = re.match('.*"(\w+)"', eachLine).group(1)
               # Use a unsafe trick
               caseName = eachLine.split(' ')[-1].strip()[0:-1]
               continue
            if eachLine.find('Entering test case') > -1:
               caseBegin = True
               # caseName = re.match('.*"(\w+)"', eachLine).group(1)
               # Use a unsafe trick
               caseName = eachLine.split(' ')[-1].strip()[1:-1]
               continue
            if caseBegin:
               if (eachLine.find('[  FAILED  ]') > -1) or \
                  (eachLine.find('error') > -1 and eachLine.find('error code 0') <= -1):
                  ret = 'FAIL'
               try:
                  errorMsg += eachLine.encode('ascii', 'replace') + '\n'
               except:
                  pass

      print tostring(testsuites, encoding="UTF-8")
      tree = ElementTree(testsuites)
      if os.name == 'nt':
         vlogPath = r'c:\tools\vlogs'
      elif sys.platform.startswith('linux'):
         vlogPath = r'/home/tools/vlogs'
      elif sys.platform.startswith('darwin'):
         vlogPath = r'/jenkins/tools/vlogs'
      xmlFile = os.path.join(vlogPath, self.testsuite + fileSuffix)
      tree.write(xmlFile)


class xmlGenerator():
   '''s
    This is class is used to handle result log.
    1. Add xml format support
   '''
   def __init__(self, testsuite = '', logPath = r''):
      self.testsuite = testsuite
      self.logPath = logPath

   def __call__(self):
      self.resultToXml()

   def resultToXml(self):
      caseName   = ''
      ret        = 'PASS'
      errorMsg   = ''
      caseLog    = None
      caseBegin  = False
      flog       = None
      testsuites = Element('testsuites')
      testsuite  = SubElement(testsuites, 'testsuite')
      testcase   = None
      vlogPath   = r''
      fileSuffix = '.xml'
      testsuite.set('name', self.testsuite)
      logger.info('Group name is: %s' % self.testsuite)
      with open(self.logPath) as fp:
         for line in fp:
            if 'OK' in line[line.find(':'):]:
               result = 'PASS'
               caseName = line.split(':')[0]   
               testcase = SubElement(testsuite,'testcase')
               testcase.set('name', caseName)
               testcase.set('result', result)
            else:
               result = 'FAIL'
               errNode = SubElement(testcase, 'FAIL')
      tree = ElementTree(testsuites) 
      if os.name == 'nt':
         vlogPath = r'c:\tools\vlogs'
      elif sys.platform.startswith('linux'):
         vlogPath = r'/home/tools/vlogs'
      elif sys.platform.startswith('darwin'):
         vlogPath = r'/jenkins/tools/vlogs'
      xmlFile = os.path.join(vlogPath, self.testsuite + fileSuffix)
      tree.write(xmlFile)

# Test
if __name__ == '__main__':
   a= Reporter('smartcard_linux_vdi', r'/home/tools/workspace/rxapi-linux-all/vlogs/smartcard_linvdi_test.log')
   a()
