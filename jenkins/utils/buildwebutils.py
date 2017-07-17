#!/usr/bin/env python
# Please contact Zhi Lin(zlin@vvvvvv.com) if any problem.

import urllib2
try:
   import simplejson as json
except ImportError:
   try:
      import json
   except ImportError:
      json = False

class Buildweb:
   """Interact with buildweb."""
   def __init__(self):
      self.delimiter = '#'*80
      self.lineSep = '\r\n'

   def GetLatestAvailableBuild(self, product, branch, buildType):
      '''Get the latest available build from buildweb.'''
      print 'Get the latest available build from buildweb.\r\n'
      url = '/ob/build/?product=%s&branch=%s&buildstate__in=succeeded,storing&buildtype=%s&_limit=1&_order_by=-id' % \
            (product, branch, buildType)
      data = self.GetResourceList(url)
      build = data['_list'][0]
      print 'The latest available build:%i.\r\n\r\n' % int(build['id'])
      return int(build['id'])

   def GetLatestRecommendedBuild(self, product, branch, buildType):
      '''Get the latest recommended build from buildweb base on the tap "Tests"'''
      #print 'Get the latest recommended build from buildweb base on the tap "Tests".\r\n'
      url = '/ob/build/?product=%s&branch=%s&buildstate__in=succeeded,storing&buildtype=%s&_limit=50&_order_by=-id' % \
            (product, branch, buildType)
      data = self.GetResourceList(url)
      builds = data['_list']
      for build in builds:
          qatestresulturl = build['_qatestresults_url']
          qatestresults = self.GetResourceList(qatestresulturl)
          #count = qatestresults['_total_count']
          count = len(qatestresults)
          if count != 0:
            for i in (0, count-1):
               data = qatestresults['_list'][i]
               if (data['qatest'] == 'bat-wwww-win' and
                  (data['qaresult'] == 'recommended' or data['qaresult'] == 'recommended-with-exceptions')):
                  print 'The latest recommended build:%i.\r\n\r\n' % int(build['id'])
                  return int(build['id'])
      print 'No recommended build.\r\n'

   def GetBuildInfo(self, build):
      '''Get the test result of the build.'''
      print 'Get the test result of the build: %s' % build
      url = '/ob/qatestresult/?build=%s' % build
      data = self.GetResourceList(url)
      info = data['_list'][0]
      createTime = info['createtime']
      note = info['note']
      qeResult = info['qaresult']
      qeTest = info['qatest']
      body = 'Build %s Info:%s%s' % (build, self.lineSep, self.delimiter)
      body = '%s%screateTime: %s%snote: %s%sqeResult: %s%sqeTest: %s%s' % \
             (body, self.lineSep,
             createTime, self.lineSep,
             note, self.lineSep,
             qeResult, self.lineSep,
             qeTest, self.lineSep)
      return body

   def GetResourceList(self, url):
      Buildweb = 'http://buildapi.eng.vvvvvv.com'
      url = '%s%s' % (Buildweb, url)
      #print 'Fetching %s ...\r\n' % url
      ret = urllib2.urlopen(url)
      status = int(ret.code)
      if status != 200:
         print '[HTTP status %d]\r\n' % status
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

   def IsValidBuild(self, build, product="wwwwcrt"):
      url = 'http://buildapi.eng.vvvvvv.com/ob/build/%s'% build
      ret = urllib2.urlopen(url)
      status = int(ret.code)
      if status != 200:
         print '[HTTP status %d]\r\n' % status
         raise Exception('Error: %s' % data['http_response_code']['message'])
      content = ret.read()
      if json:
         data = json.loads(content)
      else:
         dataDict = {}
         content = content.replace(' ','').split('\r\n')[0].split('{')[1].split('}')[0]
         for j in content.split(','):
            dataDict[j.split(':')[0].strip().strip('"')] = j.split(':')[1].strip().strip('"')
      buildproduct = dataDict["product"]
      if buildproduct.lower() == product.lower():
         return True
      else:
         return False
# Test code
#buildweb = Buildweb()
#build = buildweb.GetLatestAvailableBuild('wwwwcrt','crt-dev','beta')
#print build
#rBuild = buildweb.GetLatestRecommendedBuild('wwww','bfg-main','beta')
#print rBuild
#buildInfo = buildweb.GetBuildInfo(rBuild)
#print buildInfo
