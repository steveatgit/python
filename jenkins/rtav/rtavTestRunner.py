#!/usr/lib/python


import argparse
import ConfigParser
import datetime
import logging
import matplotlib.pyplot as plt
import numpy as np
import os
import pyaudio
import subprocess
import sys
import threading
import time
import unittest
import urllib2
import wave
import win32api
import win32con
import win32gui
import xmlrpclib


from msvcrt import getch
from optparse import OptionParser
from xmlrpclib import ServerProxy
from _winreg import *


logger = logging.getLogger('RX-API')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('rtav.log')
fh.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)


cfgFileHandler = ConfigParser.ConfigParser()
cfgFileHandler.read(r'c:\tools\config.ini')
defaultConfig = dict(cfgFileHandler.items('Default'))


def activateScreenSaver():
   time.sleep(2)
   controlProxy.activateScreenSaver()
   time.sleep(5)
   controlProxy.resumeVM()


def activeWindow(windowName):
   windowHandle = win32gui.FindWindow(None, windowName)
   win32gui.SetForegroundWindow(windowHandle)
   win32api.keybd_event(win32con.VK_SPACE, 0, win32con.KEYEVENTF_KEYUP, 0)


def connectRPCServer(agentIp, agentPort):
   logger.info('Connecting RPC server in agent %s:%d' % (agentIp, agentPort))
   timeout = 600
   startTime = time.time()
   while True:
      try:
         agentProxy = ServerProxy(('http://%s:%d' % (agentIp, agentPort)),
                                   allow_none = True)
         agentProxy.connected()
         break;
      except Exception, err:
         if time.time() - startTime < timeout:
            time.sleep(60)
            continue
         else:
            logger.error('Connect to RPC Server timeout...')
            return None
   return agentProxy
   

def disconnectConnectNetDrive():
   time.sleep(3)
   controlProxy.disconnectNetworkDrive()

   
def disableUSBDevice():
   time.sleep(3)
   controlProxy.disableUSBDevice()
   logger.info('disabled USB device')


def generateWavForm(fileName):
   time.sleep(0.2)
   logger.info('Generating wave form pic.')
   cmd = 'ffmpeg.exe -i %s -filter_complex "showwavespic=s=2560x600:split_channels=1" -frames:v 1 %s.png -y' % (fileName, fileName.split('.wav')[0])
   proc = subprocess.call(cmd, shell=True)


def generateSpectrumPic(fileName):
   time.sleep(0.2)
   print 'Generating wave form pic.'
   cmd = 'ffmpeg.exe -i %s -lavfi showspectrumpic=s=hd720 %s.jpg -y' % (fileName, fileName.split('.wav')[0])
   proc = subprocess.call(cmd, shell=True)


def getDeviceIndexByName(name):
   p = pyaudio.PyAudio()
   for i in range(p.get_device_count()):
      if p.get_device_info_by_index(i)['name'].startswith(name):
         return i
   return -1


def loopbackCapture(fileName):
   cmd = 'loopback-capture.exe'
   logger.info('client loopback capture started.')
   proc = subprocess.Popen(['start', cmd, '--file', fileName, '--int-16'],
                           shell=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
   proc.communicate()
   logger.info('client loopback capture stopped.')
   caseOutput = proc.stdout.readlines()
   caseErr =  proc.stderr.readlines()
   logger.info('caseOutput is %s, err is %s' % (caseOutput, caseErr))


def loopbackCaptureAgent(fileName):
   global timeAgent
   logger.info('Agent loopback capture started.')
   actionProxy.loopbackCapture(fileName)
   timeAgent = datetime.datetime.now()
   logger.info('Agent loopback capture stopped.')


def loopbackCaptureClient(fileName):
   global timeClient
   cmd = 'loopback-capture.exe --quit-on-receive'
   logger.info('client loopback capture started.')
   proc = subprocess.call(cmd, stdout=None, stderr=None, shell=False)
   timeClient = datetime.datetime.now()
   logger.info('client loopback capture stopped.')


def receiveFile(srcDir, dstDir):
   remoteFiles = actionProxy.listFilesInDir(srcDir)
   for fileName in remoteFiles:
      remoteFileName = os.path.join(srcDir, fileName)
      localFileName = os.path.join(dstDir, fileName)
      with open(localFileName, 'wb') as fp:
         data = actionProxy.sendFile(remoteFileName).data
         fp.write(data)
   actionProxy.deleteFiles(srcDir)


def listRemoteTestFiles():
   return actionProxy.listFilesInDir(AgentTestFilesPath)


def listTestFiles():
   return os.listdir(r'RtavTestFiles')


def remoteControlPlay():
   key = None
   while key != win32con.VK_ESCAPE:
      key = ord(getch())
      controlProxy.controlPlay(key)


def remoteControlVol(volLow, volHigh):
   time.sleep(1)
   logger.info('Higher the volume')
   controlProxy.setMasterVolLevel(volHigh)
   time.sleep(2)
   logger.info('lower the volume')
   controlProxy.setMasterVolLevel(volLow)


def remotePlay(fileName):
   time.sleep(0.2)
   logger.info('remote audio play started.')
   actionProxy.audioPlay(fileName)
   logger.info('remote audio play completed.')
   windowName = os.path.join(os.getcwd(), r'loopback-capture.exe')
   activeWindow(windowName)


def remotePlayMPCPlayer(fileName):
   time.sleep(0.2)
   logger.info('remote audio paly started')
   actionProxy.audioPlayMPCPlayer(fileName)
   logger.info('remote audio play completed.')
   windowName = os.path.join(os.getcwd(), r'loopback-capture.exe')
   activeWindow(windowName)


def remotePlayPyaudio(fileName):
   time.sleep(0.2)
   logger.info('remote audio play started')
   actionProxy.audioPlayPyaudio(fileName)
   logger.info('remote audio play completed.')
   windowName = os.path.join(os.getcwd(), r'loopback-capture.exe')
   activeWindow(windowName)


def remotePlayAsync(fileName):
   actionProxy.audioPlayAsync(fileName)


def remotePlayAsyncPyaudio(fileName):
   logger.info('remote audio play started')
   actionProxy.audioPlayAsyncPyaudio(fileName)
   time.sleep(8)
   controlProxy.controlPlay(win32con.VK_ESCAPE)
   logger.info('remote audio play completed.')
   windowName = os.path.join(os.getcwd(), r'loopback-capture.exe')
   activeWindow(windowName)


def remotePlayExtend(fileName, card, rate):
   actionProxy.audioPlayExtend(fileName, card, rate)


def remotePlaySuspendResume():
   time.sleep(1)
   logger.info('Suspend the audio')
   controlProxy.controlPlay(win32con.VK_SPACE)
   time.sleep(3)
   logger.info('Resume the audio')
   controlProxy.controlPlay(win32con.VK_SPACE)


def remoteRecord(fileName):
   actionProxy.audioRecord(fileName)


def remoteWaveDuration(fileName):
   return actionProxy.getWaveDuration(fileName)


def requestWebCommander(url, expectedReturnCode=4488):
   logger.info(url)
   ret = urllib2.urlopen(url)
   resp = ret.read()
   logger.info(resp)
   returnCode =resp.split(r'</returnCode>')[0].split('<returnCode>')[1]
   if ret.getcode() != 200:
      logger.info('http return code: %s != 200', ret.getcode())
      sys.exit(-1)
   if expectedReturnCode != -1:
      if returnCode  != str(expectedReturnCode):
         logger.info('webCommander return code: %s != %d', returnCode, expectedReturnCode)
   return int(returnCode)

   
def showPlot(fileName):
   spf = wave.open(fileName,'r')
   #Extract Raw Audio from Wav File
   signal = spf.readframes(-1)
   signal = np.fromstring(signal, 'Int16')
   fs = spf.getframerate()
   #If Stereo
   if spf.getnchannels() == 2:
       logger.info('Just mono files')
       sys.exit(0)
   Time=np.linspace(0, len(signal)/fs, num=len(signal))
   plt.figure(1)
   plt.title('Signal Wave...')
   plt.plot(Time,signal)
   plt.show()


def playToVBInput(fileName, timeout=10):
   CHUNK = 1024
   wf = wave.open(fileName, 'rb')
   p = pyaudio.PyAudio()
   index = getDeviceIndexByName(u'CABLE Input')
   stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                   channels=wf.getnchannels(),
                   rate=wf.getframerate(),
                   output_device_index=index,
                   output=True)
   logger.info('Play %s to %s device started.', fileName, p.get_device_info_by_index(index)['name'])
   data = wf.readframes(CHUNK)
   start_time = time.time()
   while data != '' and time.time() - start_time < timeout:
      stream.write(data)
      data = wf.readframes(CHUNK)
   stream.stop_stream()
   stream.close()
   p.terminate()
   logger.info('Play %s to %s device stopped.', fileName, p.get_device_info_by_index(index)['name'])


def deleteFiles(folder):
   files = os.listdir(folder)
   for file in files:
      os.remove(os.path.join(folder, file))
      

def isEmptyFolder(folder):
   if os.listdir(folder) == []:
      return True
   else:
      return False


class RtavTest(unittest.TestCase):

   def setUp(self):
      global actionProxy
      actionProxy = connectRPCServer(args.agentIp, 8001)
      if actionProxy is None:
         sys.exit(2)
      logger.info('action server connected')
      global controlProxy
      controlProxy = connectRPCServer(args.agentIp, 8002)
      if controlProxy is None:
         sys.exit(2)
      logger.info('control server connected')
      global AgentTestFilesPath
      global AgentRecordFilesPath
      AgentTestFilesPath = r'c:\tools\rtav\RtavTestFiles'
      AgentRecordFilesPath = r'c:\tools\rtav\AgentRecordFiles'

   def tearDown(self):
      pass


   # def testAudioIn(self):
      # caseName = r'testAudioIn'
      # logger.info('Entering test case "%s"', caseName)
      # if not os.path.exists(caseName):
         # os.mkdir(caseName)
      # else:
         # deleteFiles(caseName)
      # fileExist = False
      # for fileName in listTestFiles():
         # if fileName.startswith('in'):
            # fileExist = True
            # threads = []
            # t1 = threading.Thread(target=remoteRecord, args=(os.path.join(AgentRecordFilesPath, fileName),))
            # t1.setDaemon(True)
            # t1.start()
            # threads.append(t1)
            # t2 = threading.Thread(target=playToVBInput, args=(os.path.join(r'RtavTestFiles', fileName),))
            # t2.setDaemon(True)
            # t2.start()
            # threads.append(t2)
            # for t in threads:
               # t.join()
            # receiveFile(AgentRecordFilesPath, caseName)
            # self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
            # generateWavForm(os.path.join(caseName, fileName))
            # generateSpectrumPic(os.path.join(caseName, fileName))
            # time.sleep(5)
      # self.assertTrue(fileExist, 'error: audio file doesn\'t exist')
      # logger.info('Leaving test case "%s"', caseName)


   def testAudioOut(self):
      caseName = r'testAudioOut'
      logger.info('Entering test case "%s"', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      fileExist = False
      for fileName in listRemoteTestFiles():
         if fileName.startswith('common'):
            fileExist = True
            threads = []
            t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
            t1.setDaemon(True)
            t1.start()
            threads.append(t1)
            t2 = threading.Thread(target=remotePlay, args=(os.path.join(AgentTestFilesPath, fileName),))
            t2.setDaemon(True)
            t2.start()
            threads.append(t2)
            for t in threads:
               t.join()
            self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
            generateWavForm(os.path.join(caseName, fileName))
            generateSpectrumPic(os.path.join(caseName, fileName))
            time.sleep(5)
      self.assertTrue(fileExist, 'error: audio file doesn\'t exist')
      logger.info('Leaving test case "%s"', caseName)
      
      
   def testAudioOut192kbpsmp3(self):
      caseName = r'testAudioOut192kbpsmp3'
      logger.info('Entering test case "%s"', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      fileExist = False
      for fileName in listRemoteTestFiles():
         if fileName.startswith('192kbps'):
            fileExist = True
            threads = []
            t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
            t1.setDaemon(True)
            t1.start()
            threads.append(t1)
            t2 = threading.Thread(target=remotePlay, args=(os.path.join(AgentTestFilesPath, fileName),))
            t2.setDaemon(True)
            t2.start()
            threads.append(t2)
            for t in threads:
               t.join()
            self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
            generateWavForm(os.path.join(caseName, fileName))
            generateSpectrumPic(os.path.join(caseName, fileName))
            time.sleep(5)
      self.assertTrue(fileExist, 'error: audio file doesn\'t exist')
      logger.info('Leaving test case "%s"', caseName)
      
      
   def testAudioOutStereoModeLRSame(self):
      caseName = r'testAudioOutStereoModeLRSame'
      logger.info('Entering test case "%s"', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      fileExist = False
      for fileName in listRemoteTestFiles():
         if fileName.startswith('stereoS'):
            fileExist = True
            threads = []
            t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
            t1.setDaemon(True)
            t1.start()
            threads.append(t1)
            t2 = threading.Thread(target=remotePlay, args=(os.path.join(AgentTestFilesPath, fileName),))
            t2.setDaemon(True)
            t2.start()
            threads.append(t2)
            for t in threads:
               t.join()
            self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
            generateWavForm(os.path.join(caseName, fileName))
            generateSpectrumPic(os.path.join(caseName, fileName))
            time.sleep(5)
      self.assertTrue(fileExist, 'error: audio file doesn\'t exist')
      logger.info('Leaving test case "%s"', caseName)
      
      
   def testAudioOutStereoModeLRDiff(self):
      caseName = r'testAudioOutStereoModeLRDiff'
      logger.info('Entering test case "%s"', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      fileExist = False
      for fileName in listRemoteTestFiles():
         if fileName.startswith('stereoD'):
            fileExist = True
            threads = []
            t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
            t1.setDaemon(True)
            t1.start()
            threads.append(t1)
            t2 = threading.Thread(target=remotePlay, args=(os.path.join(AgentTestFilesPath, fileName),))
            t2.setDaemon(True)
            t2.start()
            threads.append(t2)
            for t in threads:
               t.join()
            self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
            generateWavForm(os.path.join(caseName, fileName))
            generateSpectrumPic(os.path.join(caseName, fileName))
            time.sleep(5)
      self.assertTrue(fileExist, 'error: audio file doesn\'t exist')
      logger.info('Leaving test case "%s"', caseName)

 
   def testAudioOutSharedNetworkDrive(self):
      caseName = r'testAudioOutSharedNetworkDrive'
      logger.info('Entering test case %s', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      controlProxy.connectNetworkDrive()
      time.sleep(5)
      netFolder = r'v:\jenkins\TestFiles\RtavTestFiles'
      fileExist = False
      for fileName in actionProxy.listFilesInDir(netFolder):
         if fileName.startswith('net'):
            fileExist = True
            threads = []
            t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
            t1.setDaemon(True)
            t1.start()
            threads.append(t1)
            t2 = threading.Thread(target=remotePlay, args=(os.path.join(netFolder, fileName),))
            t2.setDaemon(True)
            t2.start()
            threads.append(t2)
            for t in threads:
               t.join()
            self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
            generateWavForm(os.path.join(caseName, fileName))
            generateSpectrumPic(os.path.join(caseName, fileName))
            time.sleep(5)
      controlProxy.disconnectNetworkDrive()
      self.assertTrue(fileExist, 'error: audio file doesn\'t exist')
      logger.info('Leaving test case %s', caseName)

      
   # def testAudioOutUSBDevice(self):
      # caseName = r'testAudioOutUSBDevice'
      # logger.info('Entering test case %s', caseName)
      # if not os.path.exists(caseName):
         # os.mkdir(caseName)
      # else:
         # deleteFiles(caseName)
      # controlProxy.enableUSBDevice()
      # time.sleep(5)
      # usbFolder = r'e:\\'
      # fileExist = False
      # for fileName in actionProxy.listFilesInDir(usbFolder):
         # if fileName.startswith('10s'):
            # fileExist = True
            # threads = []
            # t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
            # t1.setDaemon(True)
            # t1.start()
            # threads.append(t1)
            # t2 = threading.Thread(target=remotePlay, args=(os.path.join(usbFolder, fileName),))
            # t2.setDaemon(True)
            # t2.start()
            # threads.append(t2)
            # for t in threads:
               # t.join()
            # self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
            # generateWavForm(os.path.join(caseName, fileName))
            # generateSpectrumPic(os.path.join(caseName, fileName))
            # time.sleep(5)
      # controlProxy.disableUSBDevice()
      # self.assertTrue(fileExist, 'error: audio file doesn\'t exist')
      # logger.info('Leaving test case %s', caseName)
      
      
   def testAudioOutGetCPUUsage(self):
      caseName = r'testAudioOutGetCPUUsage'
      logger.info('Entering test case "%s"', caseName)
      fileExist = False
      for fileName in listRemoteTestFiles():
         if fileName.startswith('10s'):
            fileExist = True
            remotePlayAsync(os.path.join(AgentTestFilesPath, fileName))
      self.assertTrue(fileExist, 'error: audio file doesn\'t exist')
      self.assertTrue(controlProxy.getCPUUsage(30), 'error: agent CPU usage over 30%')
      logger.info('Leaving test case "%s"', caseName)
      
      
   def testAudioOutSuspendResumeScreenSaver(self):
      caseName = r'testAudioOutSuspendResumeScreenSaver'
      logger.info('Entering test case "%s"', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      fileExist = False
      for fileName in actionProxy.listFilesInDir(AgentTestFilesPath):
         if fileName.startswith('10s'):
            fileExist = True
            threads = []
            t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
            t1.setDaemon(True)
            t1.start()
            threads.append(t1)
            t2 = threading.Thread(target=remotePlay, args=(os.path.join(AgentTestFilesPath, fileName),))
            t2.setDaemon(True)
            t2.start()
            threads.append(t2)
            t3 = threading.Thread(target=activateScreenSaver, args=())
            t3.setDaemon(True)
            t3.start()
            threads.append(t3)
            for t in threads:
               t.join()
            self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
            generateWavForm(os.path.join(caseName, fileName))
            generateSpectrumPic(os.path.join(caseName, fileName))
            time.sleep(5)
      self.assertTrue(fileExist, 'error: audio file doesn\'t exist')
      logger.info('Leaving test case "%s"', caseName)
      
      
   def testAudioOutMultiFiles(self):
      caseName = r'testAudioOutMultiFiles'
      logger.info('Entering test case "%s"', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      fileNames = listRemoteTestFiles()
      fileName = r'mix.wav'
      self.assertFalse(actionProxy.isEmptyFolder(AgentTestFilesPath), 'error: source folder is empty')
      remotePlayAsync(os.path.join(AgentTestFilesPath, 'common_piano2.wav'))
      threads = []
      t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
      t1.setDaemon(True)
      t1.start()
      threads.append(t1)
      t2 = threading.Thread(target=remotePlay, args=(os.path.join(AgentTestFilesPath, fileNames[0]),))
      t2.setDaemon(True)
      t2.start()
      threads.append(t2)
      for t in threads:
         t.join()
      self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
      generateWavForm(os.path.join(caseName, fileName))
      generateSpectrumPic(os.path.join(caseName, fileName))
      time.sleep(5)
      logger.info('Leaving test case "%s"', caseName)

      
   def testAudioOutStress(self):
      caseName = r'testAudioOutStress'
      logger.info('Entering test case "%s"', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      fileExist = False
      for fileName in actionProxy.listFilesInDir(AgentTestFilesPath):
         if fileName.startswith('story'):
            fileExist = True
            threads = []
            t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
            t1.setDaemon(True)
            t1.start()
            threads.append(t1)
            t2 = threading.Thread(target=remotePlay, args=(os.path.join(AgentTestFilesPath, fileName),))
            t2.setDaemon(True)
            t2.start()
            threads.append(t2)
            for t in threads:
               t.join()
            self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
            generateWavForm(os.path.join(caseName, fileName))
            generateSpectrumPic(os.path.join(caseName, fileName))
            time.sleep(5)
      self.assertTrue(fileExist, 'error: audio file doesn\'t exist')
      logger.info('Leaving test case "%s"', caseName)


   def testAudioOutWith1024x768Stress(self):
      caseName = r'testAudioOutWith1024x768Stress'
      logger.info('Entering test case "%s"', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      fileExist = False
      hWnd = win32gui.FindWindow(None, defaultConfig['poolname'])
      win32gui.MoveWindow(hWnd, 0, 0, 1024, 768, True)
      for fileName in actionProxy.listFilesInDir(AgentTestFilesPath):
         if fileName.startswith('story'):
            fileExist = True
            threads = []
            t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
            t1.setDaemon(True)
            t1.start()
            threads.append(t1)
            t2 = threading.Thread(target=remotePlay, args=(os.path.join(AgentTestFilesPath, fileName),))
            t2.setDaemon(True)
            t2.start()
            threads.append(t2)
            for t in threads:
               t.join()
            self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
            generateWavForm(os.path.join(caseName, fileName))
            generateSpectrumPic(os.path.join(caseName, fileName))
            time.sleep(5)
      self.assertTrue(fileExist, 'error: audio file doesn\'t exist')
      logger.info('Leaving test case "%s"', caseName)


   def testSetMaxVol(self):
      caseName = r'testSetMaxVol'
      logger.info('Entering test case "%s"', caseName)
      vmin, vmax, vinc = controlProxy.getMasterVolRange()
      volOrig = controlProxy.getMasterVolLevel()
      print 'Volume Range : %0.4f, %0.4f, %0.4f' % (vmin, vmax, vinc)
      print 'Master Volume: %0.4f' % volOrig
      controlProxy.setMasterVolLevel(vmax)
      vol = controlProxy.getMasterVolLevel()
      self.assertEqual(vol, vmax, 'error: failed to set max vol')
      controlProxy.setMasterVolLevel(volOrig)
      logger.info('Leaving test case "%s"', caseName)


   def testSetMinVol(self):
      caseName = r'testSetMaxVol'
      logger.info('Entering test case "%s"', caseName)  
      vmin, vmax, vinc = controlProxy.getMasterVolRange()
      volOrig = controlProxy.getMasterVolLevel()
      print 'Volume Range : %0.4f, %0.4f, %0.4f' % (vmin, vmax, vinc)
      print 'Master Volume: %0.4f' % volOrig
      controlProxy.setMasterVolLevel(vmin)
      vol = controlProxy.getMasterVolLevel()
      self.assertEqual(vol, vmin, 'error: failed to set min vol')
      controlProxy.setMasterVolLevel(volOrig)
      logger.info('Leaving test case "%s"', caseName)

      
   def testAudioOutMute(self):
      caseName = r'testAudioOutMute'
      logger.info('Entering test case "%s"', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      vmin, vmax, vinc = controlProxy.getMasterVolRange()
      volOrig = controlProxy.getMasterVolLevel()
      controlProxy.setMasterVolLevel(vmin)
      fileExist = False
      for fileName in listRemoteTestFiles():
         if fileName.startswith('common'):
            fileExist = True
            threads = []
            t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
            t1.setDaemon(True)
            t1.start()
            threads.append(t1)
            t2 = threading.Thread(target=remotePlay, args=(os.path.join(AgentTestFilesPath, fileName),))
            t2.setDaemon(True)
            t2.start()
            threads.append(t2)
            for t in threads:
               t.join()
            self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
            generateWavForm(os.path.join(caseName, fileName))
            generateSpectrumPic(os.path.join(caseName, fileName))
            time.sleep(5)
      controlProxy.setMasterVolLevel(volOrig)
      self.assertTrue(fileExist, 'error: audio file doesn\'t exist')
      logger.info('Leaving test case "%s"', caseName)


   def testAudioOutSetVol10(self):
      caseName = r'testAudioOutSetVol10'
      logger.info('Entering test case "%s"', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      vmin, vmax, vinc = controlProxy.getMasterVolRange()
      volOrig = controlProxy.getMasterVolLevel()
      logger.info('Volume Range : %0.4f, %0.4f, %0.4f' % (vmin, vmax, vinc)) # Max Volume is normalized to 0dB
      volObj = -34.75
      controlProxy.setMasterVolLevel(volObj)
      fileNames = listRemoteTestFiles()
      fileName = fileNames[0]
      threads = []
      t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
      t1.setDaemon(True)
      t1.start()
      threads.append(t1)
      t2 = threading.Thread(target=remotePlay, args=(os.path.join(AgentTestFilesPath, fileName),))
      t2.setDaemon(True)
      t2.start()
      threads.append(t2)
      for t in threads:
         t.join()
      generateWavForm(os.path.join(caseName, fileName))
      generateSpectrumPic(os.path.join(caseName, fileName))
      controlProxy.setMasterVolLevel(volOrig)
      time.sleep(5)
      self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
      logger.info('Leaving test case "%s"', caseName)


   def testAudioOutChangeVol(self):
      caseName = r'testAudioOutChangeVol'
      logger.info('Entering test case "%s"', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      vmin, vmax, vinc = controlProxy.getMasterVolRange()
      logger.info('Volume Range : %0.4f, %0.4f, %0.4f' % (vmin, vmax, vinc))
      volLow = -10.51  # 50% volume
      volHigh = 0 # 100% volume
      controlProxy.setMasterVolLevel(volLow)
      logger.info('Current volume %0.4f' % controlProxy.getMasterVolLevel())
      fileNames = listRemoteTestFiles()
      fileName = fileNames[0]
      threads = []
      t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
      t1.setDaemon(True)
      t1.start()
      threads.append(t1)
      t2 = threading.Thread(target=remotePlay, args=(os.path.join(AgentTestFilesPath, fileName),))
      t2.setDaemon(True)
      t2.start()
      threads.append(t2)
      t3 = threading.Thread(target=remoteControlVol, args=(volLow, volHigh,))
      t3.setDaemon(True)
      t3.start()
      threads.append(t3)
      for t in threads:
         t.join()
      generateWavForm(os.path.join(caseName, fileName))
      generateSpectrumPic(os.path.join(caseName, fileName))
      controlProxy.setMasterVolLevel(volHigh)
      time.sleep(5)
      self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
      logger.info('Leaving test case "%s"', caseName)
      

   def testAudioOutControlPlay(self):
      caseName = r'testAudioOutControlPlay'
      logger.info('Entering test case "%s"', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      controlProxy.setMasterVolLevel(0)
      fileNames = listRemoteTestFiles()
      fileName = fileNames[0]
      threads = []
      t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
      t1.setDaemon(True)
      t1.start()
      threads.append(t1)
      t2 = threading.Thread(target=remotePlayAsyncPyaudio, args=(os.path.join(AgentTestFilesPath, fileName),))
      t2.setDaemon(True)
      t2.start()
      threads.append(t2)
      t3 = threading.Thread(target=remotePlaySuspendResume, args=())
      t3.setDaemon(True)
      t3.start()
      threads.append(t3)
      for t in threads:
         t.join()
      generateWavForm(os.path.join(caseName, fileName))
      generateSpectrumPic(os.path.join(caseName, fileName))
      time.sleep(5)
      self.assertFalse(isEmptyFolder(caseName), 'error: result folder is empty')
      logger.info('Leaving test case "%s"', caseName)


   # def testClientInstallDefaultFolder(self):
      # caseName = r'testClientInstallDefaultFolder'
      # logger.info('Entering test case "%s"', caseName)
      # dll = r'ViewMMDevRedir.dll'
      # if "PROGRAMFILES(x86)" not in os.environ:
         # defaultFolder = r'C:\Program Files\VMware\VMware Horizon View Client'
         # keyToRead = r'SOFTWARE\Teradici\Client\VChan\Plugins\ViewMMDevRedir'
      # else:
         # defaultFolder = r'C:\Program Files (x86)\VMware\VMware Horizon View Client'
         # keyToRead = r'SOFTWARE\Wow6432Node\Teradici\Client\VChan\Plugins\ViewMMDevRedir'
      # self.assertTrue(os.path.isfile(os.path.join(defaultFolder, dll)), \
                                     # 'error: ViewMMDevRedir.dll doesn\'t exist in default folder')
      # exists = True
      # try:
         # reg = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
         # k = OpenKey(reg, keyToRead)
         # val = QueryValueEx(k, "dll")
         # self.assertEqual(val[0], os.path.join(defaultFolder, dll), \
                          # 'error: ViewMMDevRedir.dll doesn\'t been registered')
      # except WindowsError:
         # exists = False
      # CloseKey(k)
      # CloseKey(reg)
      # self.assertTrue(exists, 'error: ViewMMDevRedir.dll doesn\'t been registered')
      # logger.info('Leaving test case "%s"', caseName)


   # def testAgentInstallDefaultFolder(self):
      # caseName = r'testAgentInstallDefaultFolder'
      # logger.info('Entering test case "%s"', caseName)
      # self.assertTrue(actionProxy.agentInstallDefaultFolder(), \
                      # 'error: ViewMMDevRedir.dll doesn\'t exist in default folder')
      # logger.info('Leaving test case "%s"', caseName)


   # def testAudioOutLatency(self):
      # caseName = r'testAudioOutLatency'
      # logger.info('Entering test case "%s"', caseName)
      # latencyList = []
      # fileNames = listRemoteTestFiles()
      # fileName = fileNames[0]
      # for i in range(5):
         # delta = datetime.datetime.now()
         # actionProxy.nullFunc()
         # delta = (datetime.datetime.now() - delta) / 2
         # remotePlayAsync(os.path.join(AgentTestFilesPath, fileName))
         # threads = []
         # t1 = threading.Thread(target=loopbackCaptureAgent, args=(os.path.join(AgentRecordFilesPath, fileName),))
         # t1.setDaemon(True)
         # t1.start()
         # threads.append(t1)
         # t2 = threading.Thread(target=loopbackCaptureClient, args=(os.path.join('ClientRecordFiles', fileName),))
         # t2.setDaemon(True)
         # t2.start()
         # threads.append(t2)
         # for t in threads:
            # t.join()
         # latency = timeClient - timeAgent + delta
         # latencyList.append(latency)
         # avgLatency= reduce(lambda x,y: x+y, latencyList)/len(latencyList)
         # self.assertTrue(latency < delta + datetime.timedelta(seconds=0.5), 'error: latency is too big')
         # self.assertTrue(latency < avgLatency * 3, 'error: latency should be less than avg * 3')
         # logger.info('Latency: %s, %s, %s, %s', latency, timeClient, timeAgent, delta)
         # time.sleep(10)
      # for i in range(len(latencyList)):
         # logger.info('Latency %d : %s', i, latencyList[i])
      # logger.info('Leaving test case "%s"', caseName)


class RtavTestVDI(unittest.TestCase):

   def setUp(self):
      global actionProxy
      actionProxy = connectRPCServer(args.agentIp, 8001)
      if actionProxy is None:
         sys.exit(2)
      logger.info('action server connected')
      global controlProxy
      controlProxy = connectRPCServer(args.agentIp, 8002)
      if controlProxy is None:
         sys.exit(2)
      logger.info('control server connected')
      global rtavFolder
      rtavFolder = r'c:\tools\rtav'

   def tearDown(self):
      pass


   # def testAudioDeviceEnableDisable(self):
      # caseName = r'testAudioDeviceEnableDisable'
      # logger.info('Entering test case "%s"', caseName)
      # devcon = os.path.join(rtavFolder, 'devcon.exe')
      # audioHDId = r'PNPB009'
      # actionProxy.disableVirtualAudio(devcon, audioHDId)
      # time.sleep(1)
      # logger.info('disable virtual audio')
      # self.assertFalse(actionProxy.virtualAudioStatus(), 'error: audio device should be disabled')
      # actionProxy.enableVirtualAudio(devcon, audioHDId)
      # time.sleep(1)
      # logger.info('enable virtual audio')
      # self.assertTrue(actionProxy.virtualAudioStatus(), 'error: audio device should be enabled')
      # logger.info('Leaving test case "%s"', caseName)
      
      
class RtavTestRDS(unittest.TestCase):

   def setUp(self):
      global actionProxy
      actionProxy = connectRPCServer(args.agentIp, 8001)
      if actionProxy is None:
         sys.exit(2)
      logger.info('action server connected')
      global controlProxy
      controlProxy = connectRPCServer(args.agentIp, 8002)
      if controlProxy is None:
         sys.exit(2)
      logger.info('control server connected')


   def tearDown(self):
      pass


if __name__ == '__main__':
   parser = argparse.ArgumentParser()
   parser.add_argument('-a', '--agentIp', dest='agentIp',
                       default = 'localhost',
                       help='agent Ip')
   parser.add_argument('-p', '--playFile', dest='playFile',
                       default = r'c:\RTAV\story.wav',
                       help='file will play')
   parser.add_argument('-r', '--recordFile', dest='recordFile',
                       default = 'out.wav',
                       help='file will record')
   parser.add_argument('unittest_args', nargs='*')
   args = parser.parse_args()
   sys.argv[1:] = args.unittest_args
   unittest.main()
