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
import wave
import win32api
import win32con
import xmlrpclib


from msvcrt import getch
from optparse import OptionParser
from xmlrpclib import ServerProxy


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
   proc = subprocess.Popen([cmd, '--file', fileName, '--int-16'],
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


def remotePlay(fileName):
   time.sleep(0.2)
   logger.info('remote audio play started.')
   actionProxy.audioPlay(fileName)
   logger.info('remote audio play completed.')
   win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)


def remotePlayAsyc(fileName):
   actionProxy.audioPlayAsync(fileName)


def remotePlayExtend(fileName, card, rate):
   actionProxy.audioPlayExtend(fileName, card, rate)


def remoteRecord(fileName):
   actionProxy.audioRecord(fileName)


def remoteWaveDuration(fileName):
   return actionProxy.getWaveDuration(fileName)


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


def Positive_ControlPlay():
   time.sleep(5)
   controlProxy.controlPlay(win32con.VK_SPACE)
   time.sleep(3)
   controlProxy.controlPlay(win32con.VK_SPACE)
   time.sleep(5)
   controlProxy.controlPlay(win32con.VK_ESCAPE)


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


   def testRemoteAudioInputDeviceProperties(self):
      propertyList = actionProxy.pa_get_default_input_device_info()
      self.assertEqual(propertyList['defaultHighOutputLatency'], 0.18)
      self.assertEqual(propertyList['maxOutputChannels'], 0)
      self.assertEqual(propertyList['defaultSampleRate'], 44100.0)
      self.assertEqual(propertyList['defaultHighInputLatency'], 0.18)
      self.assertEqual(propertyList['name'], 'Remote Audio Device')
      self.assertEqual(propertyList['defaultLowOutputLatency'], 0.09)
      self.assertEqual(propertyList['defaultLowInputLatency'], 0.09)
      self.assertEqual(propertyList['maxInputChannels'], 2)


   def testRemoteAudioOutputDeviceProperties(self):
      propertyList = actionProxy.pa_get_default_output_device_info()
      self.assertEqual(propertyList['defaultHighOutputLatency'], 0.18)
      self.assertEqual(propertyList['maxOutputChannels'], 2)
      self.assertEqual(propertyList['defaultSampleRate'], 44100.0)
      self.assertEqual(propertyList['defaultHighInputLatency'], 0.18)
      self.assertEqual(propertyList['name'], 'Remote Audio Device')
      self.assertEqual(propertyList['defaultLowOutputLatency'], 0.09)
      self.assertEqual(propertyList['defaultLowInputLatency'], 0.09)
      self.assertEqual(propertyList['maxInputChannels'], 0)


   def testAudioIn(self):
      caseName = r'testAudioIn'
      logger.info('Entering test case %s', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      self.assertFalse(isEmptyFolder(r'RtavTestFiles'))
      for fileName in listTestFiles(): 
         threads = []
         t1 = threading.Thread(target=remoteRecord, args=(os.path.join(AgentRecordFilesPath, fileName),))
         t1.setDaemon(True)
         t1.start()
         threads.append(t1)
         t2 = threading.Thread(target=playToVBInput, args=(os.path.join(r'RtavTestFiles', fileName),))
         t2.setDaemon(True)
         t2.start()
         threads.append(t2)
         for t in threads:
            t.join()
         receiveFile(AgentRecordFilesPath, caseName)
         self.assertFalse(isEmptyFolder(caseName))
         generateWavForm(os.path.join(caseName, fileName))
         generateSpectrumPic(os.path.join(caseName, fileName))
         time.sleep(5)
      logger.info('Leaving test case %s', caseName)


   def testAudioOut(self):
      caseName = r'testAudioOut'
      logger.info('Entering test case %s', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      self.assertFalse(actionProxy.isEmptyFolder(AgentTestFilesPath))
      for fileName in listRemoteTestFiles():  
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
         self.assertFalse(isEmptyFolder(caseName))
         generateWavForm(os.path.join(caseName, fileName))
         generateSpectrumPic(os.path.join(caseName, fileName))
         time.sleep(5)
      logger.info('Leaving test case %s', caseName)


   def testAudioOutMultiFiles(self):
      caseName = r'testAudioOutMultiFiles'
      logger.info('Entering test case %s', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      fileNames = listRemoteTestFiles()
      fileName = r'multi.wav'
      self.assertFalse(actionProxy.isEmptyFolder(AgentTestFilesPath))
      remotePlayAsyc(os.path.join(AgentTestFilesPath, fileNames[0]))
      threads = []
      t1 = threading.Thread(target=loopbackCapture, args=(os.path.join(caseName, fileName),))
      t1.setDaemon(True)
      t1.start()
      threads.append(t1)
      t2 = threading.Thread(target=remotePlay, args=(os.path.join(AgentTestFilesPath, fileNames[1]),))
      t2.setDaemon(True)
      t2.start()
      threads.append(t2)
      for t in threads:
         t.join()
      self.assertFalse(isEmptyFolder(caseName))
      generateWavForm(os.path.join(caseName, fileName))
      generateSpectrumPic(os.path.join(caseName, fileName))
      time.sleep(5)
      logger.info('Leaving test case %s', caseName)


   def testAudioOutLatency(self):
      caseName = r'testAudioOutLatency'
      logger.info('Entering test case %s', caseName)
      latencyList = []
      fileNames = listRemoteTestFiles()
      fileName = fileNames[0]
      for i in range(5):
         delta = datetime.datetime.now()
         actionProxy.nullFunc()
         delta = datetime.datetime.now() - delta
         remotePlayAsyc(os.path.join(AgentTestFilesPath, fileName))
         threads = []
         t1 = threading.Thread(target=loopbackCaptureAgent, args=(os.path.join(AgentRecordFilesPath, fileName),))
         t1.setDaemon(True)
         t1.start()
         threads.append(t1)
         t2 = threading.Thread(target=loopbackCaptureClient, args=(os.path.join('ClientRecordFiles', fileName),))
         t2.setDaemon(True)
         t2.start()
         threads.append(t2)
         for t in threads:
            t.join()
         latency = timeClient - timeAgent - delta
         latencyList.append(latency)
         avgLatency= reduce(lambda x,y: x+y, latencyList)/len(latencyList)
         self.assertTrue(latency < delta + datetime.timedelta(seconds=0.5))
         self.assertTrue(latency < avgLatency * 3)
         logger.info('Latency: %s, %s, %s, %s', latency, timeClient, timeAgent, delta)
         time.sleep(10)
      for i in range(len(latencyList)):
         logger.info('Latency %d : %s', i, latencyList[i])
      logger.info('Leaving test case %s', caseName)


   def testSetMaxVol(self):
      caseName = r'testSetMaxVol'
      logger.info('Entering test case %s', caseName)
      vmin, vmax, vinc = controlProxy.getMasterVolRange()
      volOrig = controlProxy.getMasterVolLevel()
      print 'Volume Range : %0.4f, %0.4f, %0.4f' % (vmin, vmax, vinc)
      print 'Master Volume: %0.4f' % volOrig
      controlProxy.setMasterVolLevel(vmax)
      vol = controlProxy.getMasterVolLevel()
      self.assertEqual(vol, vmax)
      controlProxy.setMasterVolLevel(volOrig)
      logger.info('Leaving test case %s', caseName)


   def testSetMinVol(self):
      caseName = r'testSetMaxVol'
      logger.info('Entering test case %s', caseName)  
      vmin, vmax, vinc = controlProxy.getMasterVolRange()
      volOrig = controlProxy.getMasterVolLevel()
      print 'Volume Range : %0.4f, %0.4f, %0.4f' % (vmin, vmax, vinc)
      print 'Master Volume: %0.4f' % volOrig
      controlProxy.setMasterVolLevel(vmin)
      vol = controlProxy.getMasterVolLevel()
      self.assertEqual(vol, vmin)
      controlProxy.setMasterVolLevel(volOrig)
      logger.info('Leaving test case %s', caseName)


   def testAudioOutSetVol10(self):
      caseName = r'testSetVol10AudioOut'
      logger.info('Entering test case %s', caseName)
      if not os.path.exists(caseName):
         os.mkdir(caseName)
      else:
         deleteFiles(caseName)
      vmin, vmax, vinc = controlProxy.getMasterVolRange()
      volOrig = controlProxy.getMasterVolLevel()
      print 'Volume Range : %0.4f, %0.4f, %0.4f' % (vmin, vmax, vinc)
      volObj = vmin + (vmax - vmin) * 0.10
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
      logger.info('Leaving test case %s', caseName)


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