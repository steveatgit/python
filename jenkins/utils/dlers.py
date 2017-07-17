#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import re
import sys
import subprocess
import platform
import zipfile
import tarfile
import urllib
import urllib2

try:
   import simplejson as json
except ImportError:
   import json

# Import self modules
# import core


from urllib import urlopen, urlretrieve
from xml.parsers import expat
from log import logger


class Downloader():
   '''
   This class is super class to download binaries from buildweb.
   '''
   URLPREFIX    = 'http://buildapi.eng.vvvvvv.com'
   BINURLPREFIX = 'http://build-squid.eng.vvvvvv.com/build/mts/release'

   def __init__(self, buildNo, binName, binArch):
      self.buildNo = buildNo
      self.binName = binName
      self.binArch = binArch
      self.binPath = None
      self.product = None
      self.branch  = None

   def __call__(self, destDir):
      # Retrieve the build type: ob or sb
      if self.buildNo:
         buildTypeOBSB = self.getOBOrSB()
         assert buildTypeOBSB, 'buildTypeOBSB is None.'
      else:
         buildTypeOBSB = 'ob'
      if not self.buildNo:
         url = r'/%s/build/?product=%s&branch=%s&buildstate__in=succeeded,storing&buildtype__in=beta,release&_order_by=-id&_limit=1' % \
               (buildTypeOBSB, self.product, self.branch)
         self.buildNo = int(self.getLatestBuildNo(url))
      # Retrieve the build type: beta or release
      buildTypeBetaRelease = self.getBetaOrRelease(buildTypeOBSB)
      assert buildTypeBetaRelease, 'buildTypeBetaRelease is None.'
      # Retrieve the binary path, such as: /publish/release/[x86]/xxx.xxx
      self.getDeliverableUrl(buildTypeOBSB)
      assert self.binPath, 'Cannot retrieve the binary path.'
      if buildTypeOBSB == 'ob':
         url = '%s/bora-%s/%s' % (Downloader.BINURLPREFIX, self.buildNo, self.binPath)
      elif buildTypeOBSB == 'sb':
         url = '%s/sb-%s/%s' % (Downloader.BINURLPREFIX, self.buildNo, self.binPath)
      logger.info('Downloading %s build %s from %s' % (self.binName, self.buildNo, url))
      try:
         urllib.urlretrieve(url, os.path.join(destDir, self.binName))
         logger.info('[%s] - Download complete...' % self.binName)
      except Exception, err:
         logger.error(err)
      return self.binName

   def getResList(self, url):
      '''
      Retrieve information data
      '''
      url    = '%s%s' % (Downloader.URLPREFIX, url)
      ret    = urllib2.urlopen(url)
      status = int(ret.code)
      if status != 200:
         logger.error('HTTP status %d', status)
         raise Exception('HTTP status is not OK, Code: %s', status)
      else:
         content = ret.read()
         data = json.loads(content)
      return status, data

   def getOBOrSB(self):
      '''
      Retrieve the build type.
      '''
      buildTypes = []
      def func(buildType):
         try:
            myurl = '%s/%s/build/%d' % (Downloader.URLPREFIX, buildType, self.buildNo)
            logger.info('Determine build %s exists.', myurl)
            status = int(urllib2.urlopen(myurl).code)
            return status
         except:
            pass
      try:
         buildTypes = filter(lambda buildType: func(buildType) == 200, ['ob', 'sb'])
      except Exception, err:
         logger.error(err)
      if 'ob' in buildTypes:
         return 'ob'
      elif 'sb' in buildTypes:
         return 'sb'
      else:
         logger.error('Cannot find the related build.')
         raise Exception('Error: Network issue.')

   def getBetaOrRelease(self, obOrsb):
      '''
      Retrieve build type beta or release
      '''
      url = '/%s/build/%d' % (obOrsb, self.buildNo)
      status, build = self.getResList(url)
      if status == 200 and build.has_key('buildtype'):
         return build['buildtype']
      else:
         logger.error('Cannot retrieve the build type: beta or release.')
         raise Exception('Cannot retrieve the build type: beta or release.')

   def getDeliverableUrl(self, obOrsb):
      '''
      Get binary file path
      '''
      extName = 'tar.gz'
      if os.name == 'nt':
         extName = 'zip'
      if os.path.splitext(self.binName)[1]:
         if self.binArch:
            pattern = re.compile(r'.*%s.*' % '/'.join([self.binArch, self.binName]))
         else:
            pattern = re.compile(r'.*%s.*' % self.binName)
      else:
         if self.binArch:
            pattern = re.compile(r'.*%s.*%s.*' % ('/'.join([self.binArch, self.binName]), extName))
         else:
            pattern = re.compile(r'.*%s.*%s.*' % (self.binName, extName))
      url = '/%s/build/%d' % (obOrsb, self.buildNo)
      status, build = self.getResList(url)
      if status == 200 and build.has_key('_deliverables_url'):
         status, data = self.getResList(build['_deliverables_url'])
      else:
         logger.error('Cannot retrieve the deliverables url')
         raise Exception('Cannot retrieve the deliverables url')
      def func(status, data):
         if status == 200 and data.has_key('_list'):
            for d in data['_list']:
               m = pattern.match(d['path'])
               if m:
                  self.binName = m.group().split('/')[-1]
                  self.binPath = d['path']
                  return
         if data.has_key('_next_url'):
            if data['_next_url']:
               status, data = self.getResList(data['_next_url'])
               if status == 200:
                  func(status, data)
      func(status, data)

   def getLatestBuildNo(self, url):
      # This method is used to get latest build number
      status, data = self.getResList(url)
      if status == 200 and data.has_key('_list'):
         return data['_list'][0]['id']

   def getProductName(self, url):
      # This method is used to get the product name
      status, data = self.getResList(url)
      if status == 200 and data.has_key('product'):
         return data['product']


class DownloadRdesdk(Downloader):
   '''
   [rdesdk Downloader]
   This class is used to download rdesdk binary.
   '''
   def __init__(self, buildNo, binName, binArch):
      self.buildNo = buildNo
      self.binName = binName
      self.binArch = binArch


class DownloadTestE2E(Downloader):
   '''
   [TestE2E Downloader]
   This class is used to download TestE2E zip file.
   '''
   def __init__(self, buildNo):
      self.buildNo = buildNo
      self.binArch = ''
      if platform.system() == 'Windows':
         self.binName = 'testE2E-VMware-wwww-client-Windows'
      elif platform.system() == 'Linux':
         self.binName = 'testE2E-VMware-wwww-client-Linux'
      else:
         self.binName = 'testE2E-VMware-wwww-client-Mac'
      self.product = 'wwwwcrt'
      self.branch  = 'crt-main'


class DownloadViewHtmlAccess(Downloader):
   '''
   [View HTML Acces Downloader]
   This class is used to download View HTML Access.
   '''
   def __init__(self):
      self.buildNo = None
      self.binArch = ''
      self.binName = 'VMware-Horizon-View-HTML-Access'
      self.product = 'wwwwclientweb'
      self.branch  = 'crt-main'


class DownloadTestWebClient(Downloader):
   '''
   [Web Test Client Downloader]
   This class is used to download web test client.
   '''
   def __init__(self, buildNo):
      self.buildNo = buildNo
      self.product = 'wwwwclientweb'
      self.binArch = ''
      self.binName = 'testwebclient.war'
      self.branch  = 'crt-main'


class DownloadMFW(Downloader):
   '''
   [MFW Downloader]
   '''
   def __init__(self, buildNo):
      self.buildNo = buildNo
      if platform.system() == 'Windows':
         self.binArch = 'windows-2008'
      elif platform.system() == 'Linux':
         self.binArch = 'linux'
      else:
         self.binArch = 'macosx'
      self.binName = 'mfw.zip'
      self.product = 'mfw'
      self.branch  = 'wwww-dev'


class DownloadRDS(Downloader):
   '''
   [RDS Downloader]
   '''
   def __init__(self):
      self.buildNo = None
      if platform.system() == 'Windows':
         self.binArch = 'windows-2008'
      self.binName = 'rdsh_test_fw.zip'
      self.product = 'rdsh_test_fw'
      self.branch  = 'wwww-dev'


# Test
if __name__ == '__main__':
   DownloadViewHtmlAccess()(r'C:\boshil')
