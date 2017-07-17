'''
Mail Module
   This module is used for sending mail
'''
# Import built-in modules
import os
import re
import sys
import smtplib
import datetime


from email.mime.text import MIMEText

# Import self-modules
from log import logger

# Predefine parameters for mail

receiverTest    = ['boshil@vvvvvv.com']

receiverQeTeam  = ['yangliu@vvvvvv.com',
                   'linali@vvvvvv.com',
                   'xshen@vvvvvv.com',
                   'boshil@vvvvvv.com',
                   'hren@vvvvvv.com',
                   'zhifac@vvvvvv.com',
                   'lbao@vvvvvv.com',
                   'wqu@vvvvvv.com',]

receiverDevTeam = ['peterb@vvvvvv.com',
                   'leep@vvvvvv.com',
                   'hansc@vvvvvv.com',
                   'phils@vvvvvv.com',
                   'pbarber@vvvvvv.com',]

receiverGroup   = ['shd-dev-bj-team@vvvvvv.com',
                   'qe-linali-all@vvvvvv.com',]

# Predefine parameters for branch list

crtBranchList  = ['crt-main', 'crt-root']
wwwwBranchList = ['pascadia']
wakeBranchList = ['wwww-rel', 'cart-main']

HTMLBODY =\
'''
<!DOCTYPE html>
<html>
<head>
<style>
table {
    width:100%;
}
table, th, td {
    border: 1px solid black;
    border-cellspacing: 3px
    border-cellpadding: 0
    border-collapse: collapse;
}
th, td {
    padding: 5px;
    text-align: center;
}
</style>
</head>
<body>

<h2>Pre check-in test result</h2>
<table border="1" bgcolor="white">
   <tr bgcolor="#eee">
      <th bgcolor="#A9A9A9"><strong>Test Name</strong></th>
      <th bgcolor="#A9A9A9"><strong>Result</strong></th>
      <th bgcolor="#A9A9A9"><strong>Product Name</strong></th>
      <th bgcolor="#A9A9A9"><strong>Build Number</strong></th>
      <th bgcolor="#A9A9A9"><strong>Racetrack Link</strong></th>
   </tr>
'''

HTMLCDRBODY =\
'''
<!DOCTYPE html>
<html>
<head>
<style>
table {
    width:100%;
}
table, th, td {
    border: 1px solid black;
    border-cellspacing: 3px
    border-cellpadding: 0
    border-collapse: collapse;
}
th, td {
    padding: 5px;
    text-align: center;
}
</style>
</head>
<body>

<h2>CDR Performance test result</h2>
<table border="1" bgcolor="white">
   <tr bgcolor="#eee">
      <th bgcolor="#A9A9A9" rowspan="2"><strong>Network Profile</strong></th>
      <th bgcolor="#A9A9A9" rowspan="2"><strong>Test File</strong></th>
      <th bgcolor="#A9A9A9" colspan="2"><strong>TCP SideChannel - StreamData Mode</strong></th>
      <th bgcolor="#A9A9A9" colspan="2"><strong>TCP SideChannel</strong></th>
      <th bgcolor="#A9A9A9" colspan="2"><strong>VVC SideChannel</strong></th>
   </tr>
   <tr>
      <th bgcolor="#A9A9A9"><strong>Client -> Agent</strong></th>
      <th bgcolor="#A9A9A9"><strong>Agent -> Client</strong></th>
      <th bgcolor="#A9A9A9"><strong>Client -> Agent</strong></th>
      <th bgcolor="#A9A9A9"><strong>Agent -> Client</strong></th>
      <th bgcolor="#A9A9A9"><strong>Client -> Agent</strong></th>
      <th bgcolor="#A9A9A9"><strong>Agent -> Client</strong></th>
   </tr>
'''

patternMail     = re.compile(r'\w+@vvvvvv\.com')
patternUsername = re.compile(r'^\w+[\d+]$')

class Mailer():
   '''
   This class is used to send mail - HTML format
   '''
   def __init__(self, sender, receiver, subject, html = HTMLBODY, precheckin = True):
      self.sender     = sender
      self.receiver   = receiver
      self.subject    = subject
      self.html       = html
      self.precheckin = precheckin
      self.smtpsvr    = 'smtp.vvvvvv.com'

   def __call__(self, testResult):
      logger.info('Sending mail.')
      if self.precheckin:
         self.generateHTMLContent(testResult)
      else:
         self.generateCDRPerfHTMLContent(testResult)
      self.sendEmail()

   def generateHTMLContent(self, racetrackResult):
      resultContent = '''\
<tr bgcolor="#fff">
   <td bgcolor="white">
      <p><strong>&nbsp;%s&nbsp;</strong></p>
   </td>
   <td bgcolor="white">
      <p>
         <strong><span style="color:white;background:green">&nbsp;%d&nbsp;</span></strong>
         <strong>/</strong>
         <strong><span style="color:white;background:red">&nbsp;%d&nbsp;</span></strong>
      </p>
   </td>
   <td bgcolor="white">
      <p>
         <strong>&nbsp;%s&nbsp;</strong>
      </p>
   </td>
   <td bgcolor="white">
      <p>
         <strong><a href="%s">&nbsp;%s&nbsp;</a></strong>
      </p>
   </td>
   <td bgcolor="white">
      <p>
         <strong><a href="%s">&nbsp;%s&nbsp;</a></strong>
      </P>
   </td bgcolor="white">
</tr>
</table>
<br>
<hr>
<br>
<p><strong>&nbsp;Test Details:</strong></p>
<p>&emsp;Jenkins URL:&nbsp;%s</p>
<p>&emsp;Client     :&nbsp;%s</p>
<p>&emsp;Agent      :&nbsp;%s</p>
</body>
</html>''' % racetrackResult
      self.html += resultContent

   def generateCDRPerfHTMLContent(self, cdrPerfResults):
      for cdrPerfResult in cdrPerfResults:
         resultContent = '''\
<tr bgcolor="#fff">
   <td bgcolor="white">
      <p><strong>&nbsp;%s&nbsp;</strong></p>
   </td>
   <td bgcolor="white">
      <p><strong>&nbsp;%s&nbsp;</strong></p>
   </td>
   <td bgcolor="white">
      <p>
         <strong>&nbsp;%s&nbsp;</strong>
      </p>
   </td>
   <td bgcolor="white">
      <p>
         <strong>&nbsp;%s&nbsp;</strong>
      </p>
   </td>
   <td bgcolor="white">
      <p>
         <strong>&nbsp;%s&nbsp;</strong>
      </p>
   </td>
   <td bgcolor="white">
      <p>
         <strong>&nbsp;%s&nbsp;</strong>
      </p>
   </td>
   <td bgcolor="white">
      <p>
         <strong>&nbsp;%s&nbsp;</strong>
      </p>
   </td>
   <td bgcolor="white">
      <p>
         <strong>&nbsp;%s&nbsp;</strong>
      </p>
   </td>
</tr>''' % cdrPerfResult
         self.html += resultContent
      labelContent = '''\
</table>
</body>
</html>'''
      self.html += labelContent

   def sendEmail(self):
      msg            = MIMEText(self.html, 'html', 'utf-8')
      msg['Subject'] = self.subject
      if type(self.receiver) == str:
         self.receiver = re.split(r',\s*', self.receiver)
      elif type(self.receiver) == list:
         logger.info('No need to change the format of receiver.')
      else:
         logger.error('The format of receiver is not correct.')
      logger.info('Format the mail address.')
      self.receiver = map(lambda item: item.strip('"\''), self.receiver)
      self.receiver = map(lambda item: item if patternMail.match(item) else item + '@vvvvvv.com', self.receiver)
      msg['TO']      = ','.join(self.receiver)
      logger.info('Send mail to %s' % msg['TO'])
      try:
         smtp = smtplib.SMTP()
         smtp.connect(self.smtpsvr)
         smtp.sendmail(self.sender, self.receiver, msg.as_string())
      except Exception, err:
         logger.error('Send email error: %s' % err)
      finally:
         smtp.quit()

# Test
if __name__ == '__main__':
   r = [('1.5 Mbps, 5% packet loss, 150 ms delay', '7.iso',
         '', '', '', '', '153.5KBps', '140.0KBps'),
         ('10 Mbps, 1% packet loss, 50 ms delay', '70.iso',
         '', '', '', '', '1955.8KBps', '1310.7KBps'),
         ('100 Mbps, 0.1% packet loss, 80 ms delay', '700.iso',
         '', '', '', '', '2764.8KBps', '2826.2KBps'),
         ('100 Mbps, 5% packet loss', '700.iso',
         '', '', '', '', '7219.2KBps', '7731.2KBps'),
         ('256 Kbps, 1% packet loss, 150 ms delay', '7.iso',
         '', '', '', '', '132.1KBps', '140.5KBps'),
         ('Ideal Network', '700.iso',
         '', '', '', '', '50626.6KBps', '42209.3KBps')]
   a = Mailer('boshil@vvvvvv.com', receiverTest, 'Test', HTMLCDRBODY, False)
   logger.info(a.precheckin)
   a(r)
