#!/usr/bin/python


import contextlib
import ctypes
import datetime
import logging
import masterVol
import os
import psutil
import pyaudio
# import pymedia.audio.acodec as acodec
# import pymedia.audio.sound as sound
# import pymedia.muxer as muxer
import subprocess
import sys
import threading
import time
import wave
import win32api
import win32con
import xmlrpclib


from SimpleXMLRPCServer import SimpleXMLRPCServer
from _winreg import *


logger = logging.getLogger('RX-API')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler(r'c:\tools\rtav\rtav.log')
fh.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)


class AudioControl():

   def __init__(self):
      pass


   def activateScreenSaver(self):
      logger.info(r'active screen saver')
      cmd = r'c:\Windows\System32\Mystify.scr /y'
      subprocess.Popen(cmd, shell=True)

      
   def connected(self):
      toolsFolder = r'c:\tools'
      if not os.path.exists(toolsFolder):
         os.mkdir(toolsFolder)
      return True


   def connectNetworkDrive(self):
      logger.info(r'map network driver')
      cmd = r'net use v: \\10.117.41.125\share vvvvvv /user:administrator'
      subprocess.call(cmd, shell=True)


   def controlPlay(self, key):
      if key == win32con.VK_SPACE and playStream.is_active():
         playStream.stop_stream()
         key = None
      elif key == win32con.VK_SPACE and playStream.is_stopped():
         playStream.start_stream()
         key = None
      elif key == win32con.VK_ESCAPE:
         playStream.stop_stream()
         playStream.close()
         playWf.close()
         playP.terminate()


   def disconnectNetworkDrive(self):
      logger.info(r'disconnect network driver')
      cmd = r'net use /del v: /y'
      subprocess.call(cmd, shell=True)


   def disableUSBDevice(self):
      logger.info(r'disable USB device')
      cmd = r'RemoveDrive.exe e: -l /e'
      subprocess.call(cmd, shell=True)
      

   def enableUSBDevice(self):
      logger.info(r'enable USB device')
      cmd = r'RestartSrDev.exe *'
      subprocess.call(cmd, shell=True)


   def getCPUUsage(self, overhead):
      logger.info(r'get cpu percent')
      for i in range(3):
         p = psutil.cpu_percent()
         logger.info(r'current cpu usage %d', p)
         if p > overhead:
            return False
         time.sleep(2)
      return True
      
   
   def getMasterVolRange(self):
      return masterVol.get_volume_range()


   def getMasterVolLevel(self):
      return masterVol.get_master_volume_level()
   

   def getScreenResolution(self):
      user32 = ctypes.windll.user32
      screenSize = (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
      return screenSize

   
   def resumeVM(self):
      logger.info(r'resume vm')
      subprocess.call(r'start notepad', shell=True)
      subprocess.Popen(r'taskkill /F /IM notepad.exe', shell=True)

      
   def setMasterVolLevel(self, volLevel):
      return masterVol.set_master_volume_level(volLevel)


class AudioAction():

   def __init__(self):
      self.p = pyaudio.PyAudio()


   def getWaveDuration(self, fileName):
      with contextlib.closing(wave.open(fileName, 'r')) as f:
         frames = f.getnframes()
         rate = f.getframerate()
         duration = frames / float(rate)
         logger.info('%s length is %d' % (fileName, duration))
         return duration


   def audioPlay(self, fileName):
      logger.info('ffplay %s started.', fileName)
      proc = subprocess.call([r'c:\tools\rtav\ffplay.exe', fileName, '-hide_banner', '-nodisp', '-autoexit'], shell=True)
      logger.info('ffplay %s stopped.', fileName)


   def audioPlayMPCPlayer(self, fileName):
      logger.info('mpcPlayer %s started', fileName)
      proc = subprocess.call([r'mpc-hc.exe', '/play', '/close', fileName], shell=True)   
      logger.info('mpcPlayer %s stopped', fileName)


   def audioPlayAsync(self, fileName):
      logger.info('ffplay %s started.', fileName)
      proc = subprocess.Popen([r'c:\tools\rtav\ffplay.exe', fileName, '-hide_banner', '-nodisp', '-autoexit'])
      return 0


   def audioPlayPyaudio(self, fileName, timeout=300):
      CHUNK = 1024
      wf = wave.open(fileName, 'rb')
      stream = self.p.open(format=self.p.get_format_from_width(wf.getsampwidth()),
                           channels=wf.getnchannels(),
                           rate=wf.getframerate(),
                           output=True)
      data = wf.readframes(CHUNK)
      while data != '':
         stream.write(data)
         data = wf.readframes(CHUNK)
      stream.stop_stream()
      stream.close()
      self.p.terminate()


   def audioPlayAsyncPyaudio(self, fileName):
      '''only play wav file'''

      global playStream
      global playWf
      global playP

      playWf = wave.open(fileName, 'rb')
      playP = pyaudio.PyAudio()

      def callback(in_data, frame_count, time_info, status):
         data = playWf.readframes(frame_count)
         return (data, pyaudio.paContinue)

      playStream = playP.open(format=playP.get_format_from_width(playWf.getsampwidth()),
                              channels=playWf.getnchannels(),
                              rate=playWf.getframerate(),
                              output=True,
                              stream_callback=callback)
      playStream.start_stream()
      while playStream.is_active():
         time.sleep(0.1)


   def audioRecord(self, fileName):
      '''only record wav file'''

      CHUNK = 1024
      FORMAT = pyaudio.paInt16
      CHANNELS = 2
      RATE = 44100
      RECORD_SECONDS = 10
      WAVE_OUTPUT_FILENAME = fileName

      recordP = pyaudio.PyAudio()

      recordStream = recordP.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK)

      logger.info("%s is recording" % fileName)

      frames = []
      for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
         data = recordStream.read(CHUNK)
         frames.append(data)

      logger.info("%s done recording" % fileName)

      recordStream.stop_stream()
      recordStream.close()
      recordP.terminate()

      recordWf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
      recordWf.setnchannels(CHANNELS)
      recordWf.setsampwidth(recordP.get_sample_size(FORMAT))
      recordWf.setframerate(RATE)
      recordWf.writeframes(b''.join(frames))
      recordWf.close()


   # def audioPlayExtend(self, fileName, card, rate):
      # '''play wav, mp3, wma and others file'''

      # dm = muxer.Demuxer(str.split(fileName, '.')[-1].lower())
      # snds = sound.getODevices()
      # if card not in range(len(snds)):
         # logger.error('Cannot play sound to non existent device %d out of %d' % (card+1, len(snds)))
      # f = open(fileName, 'rb')
      # global snd
      # snd = resampler = dec = None
      # s = f.read(32000)
      # while len(s):
         # frames = dm.parse(s)
         # if frames:
            # for fr in frames:
               # # Assume for now only audio streams
               # if dec == None:
                  # logger.info('getInfo %s %s' % (dm.getInfo(), dm.streams))
                  # dec = acodec.Decoder(dm.streams[fr[0]])
                  
               # r = dec.decode(fr[1])
               # if r and r.data:
                  # if snd == None:
                     # logger.info('Opening sound with %d channels -> %s' % (r.channels, snds[card]['name']))
                     # snd = sound.Output(int(r.sample_rate*rate), r.channels, sound.AFMT_S16_LE, card)
                     # if rate < 1 or rate > 1:
                        # resampler = sound.Resampler((r.sample_rate, r.channels), (int(r.sample_rate/rate), r.channels))
                        # logger.info('Sound resampling %d->%d' % (r.sample_rate, r.sample_rate/rate))
                  # data = r.data
                  # if resampler:
                     # data = resampler.resample(data)
                  # snd.play(data)
         # s = f.read(512)
      # # The biggest trick for newbies is that snd.play() will return before playing of the chunk ends. 
      # # It is so called 'asynchronous' mode of playing audio. 
      # # If you want to wait until everything is finished, add this line:
      # while snd.isPlaying():         
         # time.sleep(.05)

   def connected(self):
      toolsFolder = r'c:\tools'
      if not os.path.exists(toolsFolder):
         os.mkdir(toolsFolder)
      return True


   def increaseVolExtend(self):
      '''increase volume'''

      vol = snd.getVolume()
      snd.setVolume(vol + 10)


   def decreaseVolExtend(self):
      '''decrease volume'''

      vol = snd.getVolume()
      snd.setVolume(vol - 10)


   def nullFunc(self):
      pass


   def sendFile(self, fileName):
      '''send log to remote'''

      with open(fileName, 'rb') as fp:
         return xmlrpclib.Binary(fp.read())


   def listFilesInDir(self, dir):
      '''list files in dir'''

      return os.listdir(dir)  


   def deleteFiles(self, dir):
      files = os.listdir(dir)
      for file in files:
         os.remove(os.path.join(dir, file))
         
         
   def isEmptyFolder(self, folder):
      if os.listdir(folder) == []:
         return True
      else:
         return False
      

   def loopbackCapture(self, fileName):
      cmd = 'loopback-capture.exe'
      logger.info('Agent loopback capture started.')
      proc = subprocess.Popen([cmd, '--file', fileName, '--int-16', '--quit-on-receive'],
                              shell=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
      proc.communicate()
      logger.info('Agent loopback capture stopped.')
      caseOutput = proc.stdout.readlines()
      caseErr =  proc.stderr.readlines()
      logger.info('caseOutput is %s, err is %s' % (caseOutput, caseErr))
      return True


   def pa_get_default_input_device_info(self):
      return self.p.get_default_input_device_info()


   def pa_get_default_output_device_info(self):
      return self.p.get_default_output_device_info()


   def pa_get_device_info_by_index(self, device_index):
      return self.p.get_device_info_by_index(device_index)


   def disableVirtualAudio(self, devcon, audioHDId):
      subprocess.call(r'%s disable %s' % (devcon, audioHDId), shell=True)


   def enableVirtualAudio(self, devcon, audioHDId):
      subprocess.call(r'%s enable %s' % (devcon, audioHDId), shell=True)

      
   def virtualAudioStatus(self):
      if (subprocess.call('python masterVol.py', shell=True)):
         return 1
      else:
         return 0


def audioActionServer():
   s = SimpleXMLRPCServer(('0.0.0.0', 8001), allow_none=True)
   logger.info('Listening on port 8001...')
   s.register_instance(AudioAction())
   s.serve_forever()


def audioControlServer():
   s1 = SimpleXMLRPCServer(('0.0.0.0', 8002), allow_none=True)
   logger.info('Listening on port 8002...')
   s1.register_instance(AudioControl())
   s1.serve_forever()


if __name__ == '__main__':
   threads = []
   t1 = threading.Thread(target=audioActionServer, args=())
   t1.setDaemon(True)
   t1.start()
   threads.append(t1)
   t2 = threading.Thread(target=audioControlServer, args=())
   t2.setDaemon(True)
   t2.start()
   threads.append(t2)
   for t in threads:
      t.join()
