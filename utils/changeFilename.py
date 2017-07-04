# 将文件夹下的所有图片名称加上‘_fc’
# http://www.cnblogs.com/rollenholt/archive/2012/04/23/2466179.html

#!/usr/bin/env python
# -*-.coding:utf-8 -*-

import os
import re
import replace

def change_name(path):
	global i
	if not os.path.isdir(path) and not os.path.isfile(path):
		return False
	if os.path.isfile(path):
		file_path = os.path.split(path)
		file_list = file_path[1].split('.')
		file_ext = file_list[-1]
		image_ext = ["bmp", "jpeg", "gif", "psd", "png", "jpg"]
		if file_ext in image_ext:
			os.rename(path, file_path[0]+'/'+file_list[0]+'_fc.'+file_ext)
			i+=1
	elif os.path.isdir(path):
		for one_file in os.listdir(path):
			change_name(os.path.join(path, one_file))

if __name__ == '__main__':
	imag_dir = 'D:\\x\\x\\images'
	imag_dir = imag_dir.replace('\\', '/')
	start = time.time()
	i=0
	change_name(imag_dir)
	c = time.time() - start
	print 'program last {}'.format(c)
	print 'all process {} images'.format(i)
