#!/usr/bin/env python
################################################################################
# Copyright 2011 VMware, Inc.  All rights reserved.
################################################################################

import os
import shutil
import socket
import subprocess
import sys

crlPrefix = None
password = 'XXXXXX'
openssl = 'openssl'
opensslConf = None

def createCert(ca, domain, extension, label, hostname, crlurl=''):
    env = os.environ.copy()
    env.update({
        'ALTNAME': 'DNS:%s.%s' % (hostname, domain),
        'CANAME': ca,
        'CRLURL': crlurl,
        'OPENSSL_CONF': opensslConf
        })

    keyFile = os.path.join(ca, 'private', '%s.%s-key.pem' % (label, domain))
    reqFile = os.path.join(ca, '%s.%s-req.pem' % (label, domain))
    crtFile = os.path.join(ca, '%s.%s-cert.pem' % (label, domain))

    subprocess.check_call([openssl, 'req', '-batch', '-verbose', '-new',
                           '-keyout', keyFile, '-out', reqFile,
                           '-passout', 'pass:%s' % password,
                           '-subj',
                           '/DC=test/DC=cdk/CN=%s.%s' % (hostname, domain)],
                          env=env)
    subprocess.check_call([openssl, 'ca', '-batch', '-verbose',
                           '-in', reqFile, '-out', crtFile, '-key', password,
                           '-policy', 'policy_server',
                           '-extensions', '%s_cert' % extension], env=env)
def createCerts(ca, domain):
    for extension in [ 'cn', 'dns' ]:
        createCert(ca, domain, extension, 'www.%s' % extension, 'www.%s' % extension)
        createCert(ca, domain, extension, 'wildcard.%s' % extension, '*.%s' % extension)

def createCA(ca, extensions=None, domains=[]):
    env = os.environ.copy()
    env.update({
        'ALTNAME': 'DNS:%s' % ca,
        'CANAME': ca,
        'CRLURL': '%s/%s.crl' % (crlPrefix, ca),
        'OPENSSL_CONF': opensslConf
        })

    shutil.rmtree(ca, True)
    os.makedirs(os.path.join(ca, 'newcerts'), 0755)
    os.makedirs(os.path.join(ca, 'private'), 0750)

    open(os.path.join(ca, 'index.txt'), 'w').close()
    f = open(os.path.join(ca, 'serial'), 'w')
    f.write('01')
    f.close()

    keyFile = os.path.join(ca, 'private', '%s-key.pem' % ca)
    crtFile = os.path.join(ca, '%s-cert.pem' % ca)

    cmd = [ openssl, 'req', '-batch', '-verbose', '-new', '-x509',
            '-keyout', keyFile, '-out', crtFile, '-days', '1',
            '-passout', 'pass:%s' % password,
            '-subj', '/DC=test/CN=%s' % ca ]
    if extensions:
        cmd.extend(['-extensions', extensions])

    subprocess.check_call(cmd, env=env)

    for domain in domains:
        createCerts(ca, domain)

def createIntermediateCA(root, intermediate, extensions, domains):
    ca = '%s-%s' % (intermediate, root)

    env = os.environ.copy()
    env.update({
        'ALTNAME': 'DNS:%s' % ca,
        'CANAME': ca,
        'CRLURL': '%s/%s.crl' % (crlPrefix, ca),
        'OPENSSL_CONF': opensslConf
        })

    shutil.rmtree(ca, True)
    os.makedirs(os.path.join(ca, 'newcerts'), 0755)
    os.makedirs(os.path.join(ca, 'private'), 0750)

    open(os.path.join(ca, 'index.txt'), 'w').close()
    f = open(os.path.join(ca, 'serial'), 'w')
    f.write('01')
    f.close()

    keyFile = os.path.join(ca, 'private', '%s-key.pem' % ca)
    reqFile = os.path.join(ca, '%s-req.pem' % ca)
    crtFile = os.path.join(ca, '%s-cert.pem' % ca)

    cmd = [ openssl, 'req', '-batch', '-verbose', '-new',
            '-keyout', keyFile, '-out', reqFile,
            '-passout', 'pass:%s' % password,
            '-subj', '/DC=test/CN=%s' % ca ]
    if extensions:
        cmd.extend([ '-extensions', extensions ])

    subprocess.check_call(cmd, env=env)

    env['CANAME'] = root
    cmd = [ openssl, 'ca', '-batch', '-verbose', '-in', reqFile,
            '-out', crtFile, '-key', password ]
    if extensions:
        cmd.extend([ '-extensions', extensions ])

    subprocess.check_call(cmd, env=env)

    for domain in domains:
        createCerts(ca, domain)

def createCrlCert(ca, domain, label):
    extension = 'crl'
    label = '%s.%s' % (label, extension)
    hostname = label
    createCert(ca, domain, extension, label, hostname, '%s/%s.crl' % (crlPrefix, ca))

def createRevokedCert(ca, domain):
    extension = 'crl'
    label = 'revoked.%s' % extension
    hostname = label

    createCrlCert(ca, domain, 'revoked')

    env = os.environ.copy()
    env.update({
        'ALTNAME': '',
        'CANAME': ca,
        'CRLURL': '',
        'OPENSSL_CONF': opensslConf
        })

    crtFile = os.path.join(ca, '%s.%s-cert.pem' % (label, domain))
    crlPemFile = os.path.join(ca, 'crl.pem')
    crlFile = os.path.join('crls', '%s.crl' % ca)

    subprocess.check_call([ openssl, 'ca', '-revoke', crtFile,
                            '-key', password ], env=env)
    subprocess.check_call([ openssl, 'ca', '-gencrl', '-crlexts', 'crl_ext',
                            '-out', crlPemFile, '-key', password ], env=env)
    subprocess.check_call([ openssl, 'crl', '-in', crlPemFile, '-out', crlFile,
                            '-outform', 'der' ], env=env)

def createAll(openssl, configFile):
    global opensslConf
    global crlPrefix
    opensslConf = configFile
    crlPrefix = "URI:http://%s:8000" % socket.gethostname()

#    if 'OPENSSL' in os.environ:
#        openssl = os.environ['OPENSSL']

    if not os.path.exists(opensslConf):
        print >> sys.stderr, 'certSetup: Could not locate conf file %s' % opensslConf
        sys.exit(1)

    print 'certSetup: Using %s and %s' % (openssl, opensslConf)

    shutil.rmtree('crls', True)
    os.mkdir('crls', 0755)

    createCA('SystemCA', 'crl_ca', [ 'test', 'invalid' ])
    createIntermediateCA('SystemCA', 'Intermediate', 'crl_ca', [ 'test', 'invalid' ])
    createCrlCert('SystemCA', 'test', 'www')
    createCrlCert('SystemCA', 'invalid', 'www')
    createRevokedCert('SystemCA', 'test')
    createCert('SystemCA', 'eku.invalid', 'cli_eku', 'client', 'client')
    createCert('SystemCA', 'eku.test', 'srv_eku', 'server', 'server')

    createCA('UntrustedCA', 'v3_ca', [ 'test' ])
    createIntermediateCA('UntrustedCA', 'Intermediate', 'v3_ca', [ 'test' ])

    createCA('self-signed.dns.test', 'dns_ca')
    createCA('self-signed.cn.test')
    createCA('mismatch.invalid')


if __name__ == '__main__':
    createAll()