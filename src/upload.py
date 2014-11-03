# -*- coding: utf8
'''
Created on 2012-2-28

@author: zyl
'''
import cgi
import cgitb
import util
import os
import datetime

if __name__ == '__main__':
    cgitb.enable()
    print "Content-Type: text/html;charset=UTF-8"     # HTML is following
    print                               # blank line, end of headers
    form = cgi.FieldStorage()
    if 'upfile' not in form:
        util.errquit('need upfile')
    if 'target' not in form:
        util.errquit('need target')
    target = form.getvalue('target')
    if os.path.isdir(target):
        util.errquit('target path error')
    dirname = os.path.dirname(target)
    if len(dirname.strip()) == 0:
        util.errquit('target miss dir')
    if not os.path.isdir(dirname):
        util.errquit('target dir ' + dirname + ' is not exist')
    fileitem = form['upfile']
    if not fileitem.file:
        util.errquit('can not receive upfile')
    now = datetime.datetime.now()
    tmpfile = target + '.' + util.current_timestamp()
    fwriter = open(tmpfile, 'w')
    while True:
        tmp = fileitem.file.read(1024)
        if tmp:
            fwriter.write(tmp)
        else:
            break;
    fwriter.close()
    util.syscmd("mv " + tmpfile + " " + target)
    