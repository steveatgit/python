sikuliX folder is too big, so check it in baidu cloud disk or U flash disk
sikuliX1.11-windows can be used to compare two images to see if they are the same, if you start a cmd, you can just use as:
set sikuli_parent_image = c:\test1.png
set sikuli_sub_image = c:\test2.png
set sikuli_action = find

runsikulix.cmd -r handleSubImage.sikuli
exit code 0 means success.

in Linux, you can also use:
export sikuli_parent_image = ..
..
..

runsikulix -r handleSubImage.sikuli

before run it, you need to setup env, for windows, you can just set JAVA_HOME and other environment variables

Preparation for Linux (RHEL/CentOS 7)

Java
No need install Java and built-in OpenJDK 7/8 is enough
Install Dependency: opencv 2.4
Install dependency packages required by compiling
yum groupinstall 'Development Tools'
yum install cmake git pkgconfig
yum install gtk2-devel
Install epel repository (https://fedoraproject.org/wiki/EPEL) of RHEL/CentOS 7 :
wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
rpm -ivh epel-release-latest-7.noarch.rpm
Install epel repository (https://fedoraproject.org/wiki/EPEL) of RHEL/CentOS 6 :
wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm
rpm -ivh epel-release-latest-6.noarch.rpm
yum install python-pip
pip install numpy (or yum install numpy)
yum install python-devel
yum install libjpeg-devel libtiff-devel libpng-devel
Build and Install opencv-2.4
cp /smb/exch/tiddy/opencv-2.4.9.zip ./
unzip opencv-2.4.9.zip
cd opencv-2.4.9
mkdir release
cd release
cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local ..
make
make install
Create sympol link for SikuliX 1.1.1
ln -s /usr/local/lib/libopencv_core.so.2.4 /usr/lib64/libopencv_core.so.2.4
ln -s /usr/local/lib/libopencv_highgui.so.2.4 /usr/lib64/libopencv_highgui.so.2.4
ln -s /usr/local/lib/libopencv_imgproc.so.2.4 /usr/lib64/libopencv_imgproc.so.2.4
Install Dependency: tesseract
yum install tesseract


Preparation for Windows

Install Java 7 or Java 8 from https://www.java.com/en/
==Use SikuliX1.1.1 from Command Line ==
Download  or  and unzip it to your Windows on Linux machine, which includes:
SikuliX 1.1.1: jar files, runsikulix, and runsikulix.cmd
Sikuli script handleImage.sikuli
Launch Terminal
Set environment variables to sepcify the image and action you wants to do (action can be find, click, doubleClick, rightclick, hoever, ...)
Linux Example:
export sikuli_action=doubleClick
export sikuli_image=/home/tiddy/test.png
Windows Example
export sikuli_action=click
export sikuli_image=C:\test\test.png
Run sikuli script from command line
Linux: runsikulix -r handleImage.sikuli
Windows: runsikulix.cmd -r handleImage.sikuli
Here are recorded videos for your reference:


More Information

If you want to download latest SikuliX1.1.1, you need:
Finish Preparation for Linux (RHEL/CentOS 7) or Preparation for Windows
Download setup jar sikulixsetup-1.1.1.jar from https://launchpad.net/sikuli/sikulix/1.1.1
Run: java -jar sikulixsetup-1.1.1.jar, and a Java GUI will pop up to proceed the downloading
Sikuli script  is a demo script I worked out to search an image on screen, and you can develop your own script. Here is the source code for reference:
import os
' ' '
Before run the sikuli script, you need set two environment variables:
  - sikuli_action: find, wait, waitVanish, exists, click, doubleClick, rightClick, hover
  - sikuli_image: full path to the image
For example:
  export sikuli_action=find
  export sikuli_image=/home/tiddy/test.png
' ' '
print '*' * 80
needExit = False
if os.environ.has_key('sikuli_action'):
    action = os.environ['sikuli_action']
else:
    needExit = True
    print 'please set environment variable: sikuli_action'
if os.environ.has_key('sikuli_image'):
    image = os.environ['sikuli_image']
else:
    needExit = True
    print 'please set environment variable: sikuli_image'
if needExit:
    exit(-1)

if action.lower() == 'find':
    print find(image)
    exit()
if action.lower() == 'click':
    print click(image)
    exit()
if action.lower() == 'doubleclick':
    print doubleClick(image)
    exit()
if action.lower() == 'rightclick':
    print rightClick(image)
    exit()
if action.lower() == 'hover':
    print hover(image)
    exit()
if action.lower() == 'wait':
    print wait(image)
    exit()
if action.lower() == 'waitvanish':
    print waitVanish(image)
    exit()
Sikuli script  is another demo script to search sub-image on parent-image, and do action on screen.
import os

On Linux host, sikuli will capture H.264 desktop as black area. 

This script is to bypass the limitation: 
1. parent image: capture client host screen shot with other tool, such as ldtp
2. sub image: capture remote desktop screen shot with ldtp

Before run the sikuli script, you need set two environment variables:
  - sikuli_action: find, click, doubleClick, rightClick, hover
  - sikuli_parent_image: full path to the parent image
  - sikuli_sub_image: full path to the child image
For example:
  export sikuli_action=find
  export sikuli_parent_image=/home/tiddy/test1.png
  export sikuli_sub_image=/home/tiddy/test2.png

print '*' * 80
needExit = False
if os.environ.has_key('sikuli_action'):
    action = os.environ['sikuli_action']
else:
    needExit = True
    print 'please set environment variable: sikuli_action'
if os.environ.has_key('sikuli_parent_image'):
    parentImage = os.environ['sikuli_parent_image']
else:
    needExit = True
    print 'please set environment variable: sikuli_parent_image'
if os.environ.has_key('sikuli_sub_image'):
    subImage = os.environ['sikuli_sub_image']
else:
    needExit = True
    print 'please set environment variable: sikuli_sub_image'

if needExit:
   exit(-1)
#Settings.MinSimilarity = 0.7
f = Finder(parentImage)
f.find(subImage)
location = f.next()
if location == None:
    print 'Failed to find "%s" in "%s"' %(subImage, parentImage)
    exit(-1)
if action.lower() == 'find':
    print location
    exit()
if action.lower() == 'click':
    print click(location)
    exit()
if action.lower() == 'doubleclick':
    print doubleClick(location)
    exit()
if action.lower() == 'rightclick':
    print rightClick(location)
    exit()
if action.lower() == 'hover':
    print hover(location)
    exit()
print '*' * 80
References

Sikuli Guide: How to run SikuliX from Command Line
Opencv 2.4 Guide: Installation in Linux
Youbut Video: Configuring OpenCV (2.4.9) on Centos 6.5 with default packages
ComputerVision Blog: Install OpenCV 3.1 and Python 2.7 on CentOS 7
