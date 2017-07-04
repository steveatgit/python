#!/usr/bin/env python

import os
import subprocess

sikuliEnv = os.environ.copy()
sikuliEnv['sikuli_parent_image'] = r'C:\result\testAudioOut\common_sin_1Hz_0.2Vol_5s.png'
sikuliEnv['sikuli_sub_image'] = r'C:\result1\testAudioOut\common_sin_1Hz_0.2Vol_5s.png'
sikuliEnv['sikuli_action'] = 'find'
#os.environ['sikuli_parent_image'] = r'C:\result\testAudioOut\common_sin_1Hz_0.2Vol_5s'
#os.environ['sikuli_sub_image'] = r'C:\result1\testAudioOut\common_sin_1Hz_0.2Vol_5s'
#os.environ['sikuli_action'] = 'find'

cmd = r'runsikulix.cmd -r handleSubImage.sikuli'
p = subprocess.Popen(cmd,
			# cwd = os.getcwd(),
		    env = sikuliEnv,
		    stdout = subprocess.PIPE,
		    stderr = subprocess.PIPE,
		    shell = True)
output,err = p.communicate()
print output, err
if output.find("[info] Exit code: 0") != -1:
	print "the sub image is same as the parent one"
else:
	print "the sub image is differnt with the parent one"
