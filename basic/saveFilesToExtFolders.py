# 某路径下不同的文件存放不同路径下 a.cpp 存放在cpp文件夹下
# 自己写的，难免可能哪里有问题
#!/usr/bin/env python
import os
import shutil

def saveFilesToExtFolders(path):
	for file in os.listdir(path):
		fileName = file.split('.')
		if len(fileName) == 1:
			continue		
		filePath = os.path.join(path, fileName[1])
		if not os.path.exists(filePath):
			os.mkdir(filePath)
		shutil.move(file, filePath)
		
if __name__ == '__main__':
	saveFilesToExtFolders(os.getcwd())
	
			
				
