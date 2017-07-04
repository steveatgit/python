#!/usr/bin/env python

import logging
logging.basicConfig(filename='example.log',level=logging.DEBUG)

s = '0'
n = int(s)
logging.info('n = %d' % n)
logging.debug('This message should go to the log file')
logging.info('So should this')
logging.warning('And this, too')
print 10/n
