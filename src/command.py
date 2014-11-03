# -*- coding: utf8
'''
Created on 2012-2-28

@author: zyl
'''
import cgi
import cgitb
import util
import os

if __name__ == '__main__':
    cgitb.enable()
    print "Content-Type: text/plain;charset=UTF-8"     # HTML is following
    print                                              # blank line, end of headers
    form = cgi.FieldStorage()
    if 'cmd' not in form:
        util.errquit('need cmd')
    cmd = form.getvalue('cmd')
    cf = cmd.split()[0]
    if os.path.isfile(cf):
        util.syscmd("chmod +x " + cf)
    util.syscmd(cmd)



