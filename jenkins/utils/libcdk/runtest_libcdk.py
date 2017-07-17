#!/build/toolchain/lin32/python-2.7.1/bin/python2.7

from runtest import *

def runtest_libcdk(buildId, extPath, caseNameFile=None):
      myBuildInfo = BuildInfo(buildId)
      myGetTestBin = GetTestBin(aBuildInfo=myBuildInfo, extPath=extPath)
      myGetTestBin.waitBuildComplete()
      myGetTestBin.downloadTestLibcdkBinaries()
      myGetTestBin.extractTestLibcdkBinaries()
      myRunTestView = RunTestView(myGetTestBin.bi, myGetTestBin.extPath)
      myRunTestView.generateTestCert()
      if caseNameFile:
         myRunTestView.caseNameFile = caseNameFile
         myRunTestView.runTestCasesFromFile()
      else:
         myRunTestView.runTestCasesAll()
      return myRunTestView.racetrackInfo

if __name__ == '__main__':
   try:
      options = getCommandLine()
      runtest_libcdk(options.buildId, options.extPath, options.caseNameFile)
   except KeyboardInterrupt:
      print >> sys.stderr, '%s: interrupted' % _SCRIPT_NAME
      sys.exit(130)

