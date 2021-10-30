<!--
 * @Description: 
 * @email: 359066432@qq.com
 * @Author: lhj
 * @software: vscode
 * @Date: 2021-10-29 01:12:35
 * @platform: windows 10
 * @LastEditors: lhj
 * @LastEditTime: 2021-10-30 10:47:41
-->

## WSGIServer
继承关系为：WSGIServer -> simple_server.WSGIServer -> HTTPServer -> HTTPServer
```python

class WSGIServer(HTTPServer):

    """BaseHTTPServer that implements the Python WSGI protocol"""

    application = None

    def server_bind(self):
        """Override server_bind to store the server name."""
        HTTPServer.server_bind(self) # 这里 = super().server_bind()
        self.setup_environ() # 将server name 储存到环境变量

    def setup_environ(self):
        # Set up base environment
        env = self.base_environ = {}
        env['SERVER_NAME'] = self.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PORT'] = str(self.server_port)
        env['REMOTE_HOST']=''
        env['CONTENT_LENGTH']=''
        env['SCRIPT_NAME'] = ''

    def get_app(self):
        return self.application

    def set_app(self,application):
        self.application = application

# WSGI INSTANCE
    def serve_forever(self, poll_interval=0.5):
       """
        Handle one request at a time until shutdown.
        Polls for shutdown every poll_interval seconds. Ignores
        self.timeout. If you need to do periodic tasks, do them in
        another thread.
        """
        
        self.__is_shut_down.clear()
        try:
            # XXX: Consider using another file descriptor or connecting to the
            # socket to wake this up instead of polling. Polling reduces our
            # responsiveness to a shutdown request and wastes cpu at all other
            # times.
            with _ServerSelector() as selector:
                selector.register(self, selectors.EVENT_READ)

                while not self.__shutdown_request:
                    ready = selector.select(poll_interval)
                    # bpo-35017: shutdown() called during select(), exit immediately.
                    if self.__shutdown_request:
                        break
                    if ready:
                        self._handle_request_noblock()

                    self.service_actions()
        finally:
            self.__shutdown_request = False
            self.__is_shut_down.set()

```
<!-- TODO SOCKET LEARN -->
这里可以先了解[python socket](www.baidu.com) 

上个note说到，`runsever`说到底就是实例化一个`WSGIServer`，然后调用`serve_forever`方法,启动一个监听服务
然后就是一个正常的WGSI请求-->处理的过程,我们再看上一个NOTE提到的`RUN`方法
```python

def run(addr, port, wsgi_handler, ipv6=False, threading=False, server_cls=WSGIServer):
    server_address = (addr, port)
    if threading:
        httpd_cls = type('WSGIServer', (socketserver.ThreadingMixIn, server_cls), {})
    else:
        httpd_cls = server_cls
    httpd = httpd_cls(server_address, WSGIRequestHandler, ipv6=ipv6)
    if threading:
        # ThreadingMixIn.daemon_threads indicates how threads will behave on an
        # abrupt shutdown; like quitting the server by the user or restarting
        # by the auto-reloader. True means the server will not wait for thread
        # termination before it quits. This will make auto-reloader faster
        # and will prevent the need to kill the server manually if a thread
        # isn't terminating correctly.
        httpd.daemon_threads = True
    httpd.set_app(wsgi_handler)
    httpd.serve_forever()

```
这里的`wsgi_handler`为一个具体 `WSGIHandler`实例，用来处理处理`REQUEST`请求
这里我们再理解下这个图：
![django-wsgi](../imgs/django-wsgi.png)
理解一下，主要有几点:
- 1 django 自己对python 原生WSGIServer,WSGIRequest,ServerHandle进行了封装.
- 2 request 到来时，走的原生 `handler_request`方法，然后实例化WSGIRequestHandler。
再看看上面的`httpd = httpd_cls(server_address, WSGIRequestHandler, ipv6=ipv6)`,
其实就是`WSGIServer(server_address, WSGIRequestHandler, ipv6=ipv6)`
```PYTHON 原生WSGI 服务
   ...
       def process_request(self, request, client_address):
        """Call finish_request.

        Overridden by ForkingMixIn and ThreadingMixIn.

        """
        self.finish_request(request, client_address)
        self.shutdown_request(request)

    def server_close(self):
        """Called to clean-up the server.

        May be overridden.

        """
        pass

    def finish_request(self, request, client_address):
        """Finish one request by instantiating RequestHandlerClass."""
        self.RequestHandlerClass(request, client_address, self)
    ...

```
这里的`RequestHandlerClass(request, client_address, self)`就是 `WSGIRequestHandler(request, client_address, self)`

### WSGIRequestHandler
`WSGIRequestHandler`是DJANGO对request的一次封装。我们再回顾下一开始那个图，`WSGIRequestHandler`主要就是调用`handle`方法，实例化一个`ServeHandle`
并调用`run`方法
```python

class WSGIRequestHandler(simple_server.WSGIRequestHandler):
    protocol_version = 'HTTP/1.1'

    def address_string(self):
        # Short-circuit parent method to not call socket.getfqdn
        return self.client_address[0]

    def log_message(self, format, *args):
        extra = {
            'request': self.request,
            'server_time': self.log_date_time_string(),
        }
        
        if args[1][0] == '4':
            # 0x16 = Handshake, 0x03 = SSL 3.0 or TLS 1.x
            if args[0].startswith('\x16\x03'):
                extra['status_code'] = 500
                logger.error(
                    "You're accessing the development server over HTTPS, but "
                    "it only supports HTTP.\n", extra=extra,
                )
                return

        if args[1].isdigit() and len(args[1]) == 3:
            status_code = int(args[1])
            extra['status_code'] = status_code

            if status_code >= 500:
                level = logger.error
            elif status_code >= 400:
                level = logger.warning
            else:
                level = logger.info
        else:
            level = logger.info

        level(format, *args, extra=extra)

    def get_environ(self):
        # Strip all headers with underscores in the name before constructing
        # the WSGI environ. This prevents header-spoofing based on ambiguity
        # between underscores and dashes both normalized to underscores in WSGI
        # env vars. Nginx and Apache 2.4+ both do this as well.
        for k in self.headers:
            if '_' in k:
                del self.headers[k]

        return super().get_environ()

    def handle(self):
        self.close_connection = True
        self.handle_one_request()
        while not self.close_connection:
            self.handle_one_request()
        try:
            self.connection.shutdown(socket.SHUT_WR)
        except (AttributeError, OSError):
            pass

    def handle_one_request(self):
        """Copy of WSGIRequestHandler.handle() but with different ServerHandler"""
        self.raw_requestline = self.rfile.readline(65537)
        if len(self.raw_requestline) > 65536:
            self.requestline = ''
            self.request_version = ''
            self.command = ''
            self.send_error(414)
            return

        if not self.parse_request():  # An error code has been sent, just exit
            return

        handler = ServerHandler(
            self.rfile, self.wfile, self.get_stderr(), self.get_environ()
        )
        handler.request_handler = self      # backpointer for logging & connection closing
        handler.run(self.server.get_app())


################  ServerHandler.run()
    ...
    def run(self, application):
        """Invoke the application"""
        # Note to self: don't move the close()!  Asynchronous servers shouldn't
        # call close() from finish_response(), so if you close() anywhere but
        # the double-error branch here, you'll break asynchronous servers by
        # prematurely closing.  Async servers must return from 'run()' without
        # closing if there might still be output to iterate over.
        try:
            self.setup_environ()
            self.result = application(self.environ, self.start_response)
            self.finish_response()
        except:
            try:
                self.handle_error()
            except:
                # If we get an error handling an error, just give up already!
                self.close()
                raise   # ...and let the actual server figure it out.
    ...



```
可以看到`WSGIRequestHandler`主要是对environ进行了二次封装。`handle_one_request`中实例化了一个`ServerHandler`,`RUN`方法
中传入了`self.server.get_app()`,回顾我们上面的笔记和之前，可以知道这里其实就是一个`WSGIHandler`实例(在`run`方法传入)
所以！这里的run调用的是什么，就是` application(self.environ, self.start_response)`,其实就是` WSGIHandler()(self.environ, self.start_response)`
其实就是`WSGIHandler().__call__(self.environ, self.start_response)`~~~~

- 再次回顾我们一开始那个图，其实我们现在已经走到了 `WSGIHandler`这一步骤里面了。
``` PYTHON
class WSGIHandler(base.BaseHandler):
    request_class = WSGIRequest

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_middleware()

    def __call__(self, environ, start_response):
        set_script_prefix(get_script_name(environ))
        signals.request_started.send(sender=self.__class__, environ=environ)
        request = self.request_class(environ)
        response = self.get_response(request)

        response._handler_class = self.__class__

        status = '%d %s' % (response.status_code, response.reason_phrase)
        response_headers = [
            *response.items(),
            *(('Set-Cookie', c.output(header='')) for c in response.cookies.values()),
        ]
        start_response(status, response_headers)
        if getattr(response, 'file_to_stream', None) is not None and environ.get('wsgi.file_wrapper'):
            # If `wsgi.file_wrapper` is used the WSGI server does not call
            # .close on the response, but on the file wrapper. Patch it to use
            # response.close instead which takes care of closing all files.
            response.file_to_stream.close = response.close
            response = environ['wsgi.file_wrapper'](response.file_to_stream, response.block_size)
        return response
```
这里主要就是`get_response`方法，找到url对应的VIEW，执行后返回 response，之后的详细的处理过程留到以后再说~

