# -*- coding: utf8
'''
Created on 2012-2-29

@author: zyl
'''

import os
import sys
import fcntl
import datetime

def syscmd(cmd):
    ret = os.system(cmd)
    if ret != 0:
        print "shell execute error, ret: " + str(ret) + ", cmd: " + cmd
        errquit('fail')

def errquit(msg):
    print msg
    sys.exit(1)

def current_timestamp():
    now = datetime.datetime.now()
    return "%02d-%02d-%02d-%02d-%02d-%02d" % (now.year, now.month, now.day, now.hour, now.minute, now.second)
    
def set_cloexec_flag(fd):
    old = fcntl.fcntl(fd, fcntl.F_GETFD)
    fcntl.fcntl(fd, fcntl.F_SETFD, old | fcntl.FD_CLOEXEC)

def daemon(pidfile, stdin = '/dev/null', stdout = '/dev/null', stderr = '/dev/null'):
    pid = os.fork()
    if pid != 0:
        sys.exit(0)
    os.chdir('/')
    os.setsid()
    os.umask(0)
    pid = os.fork()
    if pid != 0:
        sys.exit(0)
    sys.stdout.flush()
    sys.stderr.flush()
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
    pidwriter = open(pidfile, 'w+')
    pidwriter.write('%s\n' % os.getpid())
    pidwriter.close()
