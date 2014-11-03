# -*- coding: utf8
'''
Created on 2012-2-29

@author: zyl
'''
import BaseHTTPServer
import CGIHTTPServer
import os
import sys
import copy
import urllib
import select
import util

class CGIHandler(CGIHTTPServer.CGIHTTPRequestHandler):
    
    def is_cgi(self):
        return True
    
    def run_cgi(self):
        path = self.path
        ss = path.split('?')
        cmd = ss[0].strip('/')
        query = None
        if len(ss) > 1:
            query = ss[1]
        
        scriptname = cmd + '.py'
        scriptfile = sys.path[0].rstrip('/') + '/' + scriptname
        
        if not os.path.exists(scriptfile):
            self.send_error(404, "No such CGI script (%r)" % scriptname)
            return
        if not os.path.isfile(scriptfile):
            self.send_error(403, "CGI script is not a plain file (%r)" % scriptname)
            return

        env = copy.deepcopy(os.environ)
        env['SERVER_SOFTWARE'] = self.version_string()
        env['SERVER_NAME'] = self.server.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PROTOCOL'] = self.protocol_version
        env['SERVER_PORT'] = str(self.server.server_port)
        env['REQUEST_METHOD'] = self.command
        rest = cmd
        if query:
            rest += '?' + query
        uqrest = urllib.unquote(rest)
        env['PATH_INFO'] = uqrest
        env['PATH_TRANSLATED'] = self.translate_path(uqrest)
        env['SCRIPT_NAME'] = scriptname
        if query:
            env['QUERY_STRING'] = query
        host = self.address_string()
        if host != self.client_address[0]:
            env['REMOTE_HOST'] = host
        env['REMOTE_ADDR'] = self.client_address[0]
        authorization = self.headers.getheader("authorization")
        if authorization:
            authorization = authorization.split()
            if len(authorization) == 2:
                import base64, binascii
                env['AUTH_TYPE'] = authorization[0]
                if authorization[0].lower() == "basic":
                    try:
                        authorization = base64.decodestring(authorization[1])
                    except binascii.Error:
                        pass
                    else:
                        authorization = authorization.split(':')
                        if len(authorization) == 2:
                            env['REMOTE_USER'] = authorization[0]
        
        if self.headers.typeheader is None:
            env['CONTENT_TYPE'] = self.headers.type
        else:
            env['CONTENT_TYPE'] = self.headers.typeheader
        length = self.headers.getheader('content-length')
        if length:
            env['CONTENT_LENGTH'] = length
        referer = self.headers.getheader('referer')
        if referer:
            env['HTTP_REFERER'] = referer
        accept = []
        for line in self.headers.getallmatchingheaders('accept'):
            if line[:1] in "\t\n\r ":
                accept.append(line.strip())
            else:
                accept = accept + line[7:].split(',')
        env['HTTP_ACCEPT'] = ','.join(accept)
        ua = self.headers.getheader('user-agent')
        if ua:
            env['HTTP_USER_AGENT'] = ua
        co = filter(None, self.headers.getheaders('cookie'))
        if co:
            env['HTTP_COOKIE'] = ', '.join(co)
        
        for k in ('QUERY_STRING', 'REMOTE_HOST', 'CONTENT_LENGTH',
                  'HTTP_USER_AGENT', 'HTTP_COOKIE', 'HTTP_REFERER'):
            env.setdefault(k, "")

        self.send_response(200, "Script output follows")
        
        # add fd_cloexec flag to input and output
        util.set_cloexec_flag(self.rfile.fileno())
        util.set_cloexec_flag(self.wfile.fileno())
        
        self.wfile.flush() # Always flush before forking
        pid = os.fork()
        if pid != 0:
            # Parent
            pid, sts = os.waitpid(pid, 0)
            # throw away additional data [see bug #427345]
            while select.select([self.rfile], [], [], 0)[0]:
                if not self.rfile.read(1):
                    break
            if sts:
                self.log_error("CGI script exit status %#x", sts)
            else:
                self.wfile.write('\n-----\n%s\n-----\n' % 'rd_ok')
            self.wfile.flush()
            return
        # Child
        interp = sys.executable
        if 'upload' == cmd:
            args = ['', scriptfile]
        else:
            args = ['', '-u', scriptfile]
        try:
            os.dup2(self.rfile.fileno(), sys.stdin.fileno())
            os.dup2(self.wfile.fileno(), sys.stdout.fileno())
            os.execve(interp, args, env)
        except:
            self.server.handle_error(self.request, self.client_address)
            os._exit(127)
        return



if __name__ == '__main__':
    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        print "need port"
        sys.exit(1)
    httpd = BaseHTTPServer.HTTPServer(("", port), CGIHandler)
    # add fd_cloexec flag to socket
    util.set_cloexec_flag(httpd.fileno())
    print "serving at port", port
    sdir = sys.path[0].rstrip('/')
    pidfile = sdir + '/server.pid'
    logdir = sdir + '/log'
    if not os.path.isdir(logdir):
        os.mkdir(logdir)
    logfile = logdir + '/server.log'
    util.daemon(pidfile, stdout = logfile, stderr = logfile)
    sys.stdout.write('server start %s\n' % util.current_timestamp())
    httpd.serve_forever()


