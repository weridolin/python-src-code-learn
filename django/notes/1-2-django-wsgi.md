<!--
 * @Description: 
 * @email: 359066432@qq.com
 * @Author: lhj
 * @software: vscode
 * @Date: 2021-10-27 00:57:34
 * @platform: windows 10
 * @LastEditors: lhj
 * @LastEditTime: 2021-10-30 01:12:49
-->

## 启动一个 WSGI 服务
DJANGO的 启动命令``runserver `` 其实就是启动一个wsgi服务

## django 的 `manage.py`

```python 

    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

```
可以看到 ``manage.py`` 执行的就是把配置文件的路径设置为一个环境变量，然后启动`execute_from_command_line`然后后面就是输入的参数

```python 
def execute_from_command_line(argv=None):
    """Run a ManagementUtility."""
    utility = ManagementUtility(argv)
    utility.execute()

```

这里其实就是实例化``ManagementUtility``,然后执行`execute`函数
```python
# 
class ManagementUtility:
    """
    Encapsulate the logic of the django-admin and manage.py utilities.
    """
    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]
        self.prog_name = os.path.basename(self.argv[0])
        if self.prog_name == '__main__.py':
            self.prog_name = 'python -m django'
        self.settings_exception = None

```
ManagementUtility其实把django-admin和  manage.py utilities 单元的一些封装


```python

def execute(self):
        """
        Given the command-line arguments, figure out which subcommand is being
        run, create a parser appropriate to that command, and run it.
        """
        # 给出 command 的参数，指出要执行哪个命令，比如 runserver ，对应创建一个parser并执行
        try:
            subcommand = self.argv[1] # 比如 runserver
        except IndexError:
            subcommand = 'help'  # Display help if no arguments were given.

        # Preprocess options to extract --settings and --pythonpath.
        # These options could affect the commands that are available, so they
        # must be processed early.
        parser = CommandParser(
            prog=self.prog_name,
            usage='%(prog)s subcommand [options] [args]',
            add_help=False,
            allow_abbrev=False,
        ) 
        # 这里是初始化了一个解析器，用于解析输入的参数，CommandParser继承ArgumentParser是python基础类包中的一个类，
        # 这个函数的目的是将ArgumentParser封装成符合django内部调用的接口形式，并且优化了参数错误的报错提示信息
        parser.add_argument('--settings')
        parser.add_argument('--pythonpath')
        parser.add_argument('args', nargs='*')  # catch-all
        try:
            # 参考ArgumentParser的源码，parse_known_args返回一个 namespace 和 传入的args
            # namespace 即为储存 args的一个object
            options, args = parser.parse_known_args(self.argv[2:])
            handle_default_options(options)
        except CommandError:
            pass  # Ignore any option errors at this point.

        try:
            # 获取 setting 里面的INSTALLED_APPS
            # 懒加载 settings
            settings.INSTALLED_APPS
        except ImproperlyConfigured as exc:
            self.settings_exception = exc
        except ImportError as exc:
            self.settings_exception = exc

        if settings.configured:
            # Start the auto-reloading dev server even if the code is broken.
            # The hardcoded condition is a code smell but we can't rely on a
            # flag on the command class because we haven't located it yet.
            if subcommand == 'runserver' and '--noreload' not in self.argv:
                try:
                    # 运行setup，同时捕抓错误 TODO 待详细阅读
                    autoreload.check_errors(django.setup)()
                except Exception:
                    # The exception will be raised later in the child process
                    # started by the autoreloader. Pretend it didn't happen by
                    # loading an empty list of applications.
                    apps.all_models = defaultdict(dict)
                    apps.app_configs = {}
                    apps.apps_ready = apps.models_ready = apps.ready = True

                    # Remove options not compatible with the built-in runserver
                    # (e.g. options for the contrib.staticfiles' runserver).
                    # Changes here require manually testing as described in
                    # #27522.
                    _parser = self.fetch_command('runserver').create_parser('django', 'runserver')
                    _options, _args = _parser.parse_known_args(self.argv[2:])
                    for _arg in _args:
                        self.argv.remove(_arg)

            # In all other cases, django.setup() is required to succeed.
            else:
                django.setup()

        self.autocomplete()

        if subcommand == 'help':
            if '--commands' in args:
                sys.stdout.write(self.main_help_text(commands_only=True) + '\n')
            elif not options.args:
                sys.stdout.write(self.main_help_text() + '\n')
            else:
                self.fetch_command(options.args[0]).print_help(self.prog_name, options.args[0])
        # Special-cases: We want 'django-admin --version' and
        # 'django-admin --help' to work, for backwards compatibility.
        elif subcommand == 'version' or self.argv[1:] == ['--version']:
            sys.stdout.write(django.get_version() + '\n')
        elif self.argv[1:] in (['--help'], ['-h']):
            sys.stdout.write(self.main_help_text() + '\n')
        else:
            # 这里是找到对应的 command application，并且去启动
            self.fetch_command(subcommand).run_from_argv(self.argv)

def handle_default_options(options):
    """
    Include any default o tions that all commands should accept here
    so that ManagementUtility can handle them before searching for
    user commands.
    """
    # 如果传入 settings,则修改setting环境变量
    # 同时 sys.path增加python path
    if options.settings:
        os.environ['DJANGO_SETTINGS_MODULE'] = options.settings
    if options.pythonpath:
        sys.path.insert(0, options.pythonpath)

def setup(set_prefix=True):
    """
    Configure the settings (this happens as a side effect of accessing the
    first setting), configure logging and populate the app registry.
    Set the thread-local urlresolvers script prefix if `set_prefix` is True.
    """
    from django.apps import apps
    from django.conf import settings
    from django.urls import set_script_prefix
    from django.utils.log import configure_logging
    
    # 日志配置
    configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)
    if set_prefix:
        set_script_prefix(
            '/' if settings.FORCE_SCRIPT_NAME is None else settings.FORCE_SCRIPT_NAME
        )
    # 注册app，这里是就是加载 INSTALLED_APPS 加载应用程序配置和模型。 TODO 待详细阅读
    apps.populate(settings.INSTALLED_APPS)


```

``CommandParser``继承了 ``ArgumentParser``,并且重写了`parse_args`, `error`方法，主要是增加了参数错误校验和
优化报错提示。

通过`execute`的代码可以看出，EXECUTE方法主要就是
- 1.实例化`ArgumentParser`校验参数的合法性，懒加载settings
- 2.运行setup，加载一些配置和导入对应APP
- 3.找到command对应的单元模块，并执行run_from_argv方法



## runserver command

runserver 是django定义的命令，也是启动一个wsgi协议的web服务。由上述的解析可以看出。`runserver`是执行
`django\core\management\commands\runserver.py`里面的`command`里面的`run_from_argv`方法

- run_from_argv(*args) -->  execute(self, *args, **options):
```python

    def run_from_argv(self, argv):
        """
        Set up any environment changes requested (e.g., Python path
        and Django settings), then run this command. If the
        command raises a ``CommandError``, intercept it and print it sensibly
        to stderr. If the ``--traceback`` option is present or the raised
        ``Exception`` is not ``CommandError``, raise it.
        """
        self._called_from_command_line = True
        parser = self.create_parser(argv[0], argv[1])

        options = parser.parse_args(argv[2:])
        cmd_options = vars(options)
        # Move positional args out of options to mimic legacy optparse
        args = cmd_options.pop('args', ())
        handle_default_options(options)
        try:
            self.execute(*args, **cmd_options)
        except CommandError as e:
            if options.traceback:
                raise

            # SystemCheckError takes care of its own formatting.
            if isinstance(e, SystemCheckError):
                self.stderr.write(str(e), lambda x: x)
            else:
                self.stderr.write('%s: %s' % (e.__class__.__name__, e))
            sys.exit(e.returncode)
        finally:
            try:
                connections.close_all()
            except ImproperlyConfigured:
                # Ignore if connections aren't setup at this point (e.g. no
                # configured settings).
                pass


## execute
    def execute(self, *args, **options):
        """
        Try to execute this command, performing system checks if needed (as
        controlled by the ``requires_system_checks`` attribute, except if
        force-skipped).
        """
        if options['force_color'] and options['no_color']:
            raise CommandError("The --no-color and --force-color options can't be used together.")
        if options['force_color']:
            self.style = color_style(force_color=True)
        elif options['no_color']:
            self.style = no_style()
            self.stderr.style_func = None
        if options.get('stdout'):
            self.stdout = OutputWrapper(options['stdout'])
        if options.get('stderr'):
            self.stderr = OutputWrapper(options['stderr'])

        if self.requires_system_checks and not options['skip_checks']:
            if self.requires_system_checks == ALL_CHECKS:
                self.check()
            else:
                self.check(tags=self.requires_system_checks)
        if self.requires_migrations_checks:
            self.check_migrations()
        output = self.handle(*args, **options)
        if output:
            if self.output_transaction:
                connection = connections[options.get('database', DEFAULT_DB_ALIAS)]
                output = '%s\n%s\n%s' % (
                    self.style.SQL_KEYWORD(connection.ops.start_transaction_sql()),
                    output,
                    self.style.SQL_KEYWORD(connection.ops.end_transaction_sql()),
                )
            self.stdout.write(output)
        return output



```
- 1 同样是对参数的校验
- 2 调用execute()
- 3 execute在调用handle()，该方法在不同command(即为不同指令)实现

- runserver.handle(self, *args, **options):
检验服务的配置，如地址，端口等，在调用`RUN` 方法
```PYTHON
    def run(self, **options):
        """Run the server, using the autoreloader if needed."""
        # 这里有两个RUN的模式，一个是以 reloader的形式启动，应该是检测到修改就会去修改
        use_reloader = options['use_reloader']

        if use_reloader:
            autoreload.run_with_reloader(self.inner_run, **options)
        else:
            self.inner_run(None, **options)

    def inner_run(self, *args, **options):
        # If an exception was silenced in ManagementUtility.execute in order
        # to be raised in the child process, raise it now.
        autoreload.raise_last_exception()

        threading = options['use_threading'] # 是否线程启动
        # 'shutdown_message' is a stealth option.
        shutdown_message = options.get('shutdown_message', '')
        quit_command = 'CTRL-BREAK' if sys.platform == 'win32' else 'CONTROL-C'

        self.stdout.write("Performing system checks...\n\n")
        self.check(display_num_errors=True)
        # Need to check migrations here, so can't use the
        # requires_migrations_check attribute.
        self.check_migrations()
        now = datetime.now().strftime('%B %d, %Y - %X')
        self.stdout.write(now)
        self.stdout.write((
            "Django version %(version)s, using settings %(settings)r\n"
            "Starting development server at %(protocol)s://%(addr)s:%(port)s/\n"
            "Quit the server with %(quit_command)s."
        ) % {
            "version": self.get_version(),
            "settings": settings.SETTINGS_MODULE,
            "protocol": self.protocol,
            "addr": '[%s]' % self.addr if self._raw_ipv6 else self.addr,
            "port": self.port,
            "quit_command": quit_command,
        })

        try:
            handler = self.get_handler(*args, **options) # 返回 WSGIHandler() 实例
            run(self.addr, int(self.port), handler,
                ipv6=self.use_ipv6, threading=threading, server_cls=self.server_cls)
        except OSError as e:
            # Use helpful error messages instead of ugly tracebacks.
            ERRORS = {
                errno.EACCES: "You don't have permission to access that port.",
                errno.EADDRINUSE: "That port is already in use.",
                errno.EADDRNOTAVAIL: "That IP address can't be assigned to.",
            }
            try:
                error_text = ERRORS[e.errno]
            except KeyError:
                error_text = e
            self.stderr.write("Error: %s" % error_text)
            # Need to use an OS exit because sys.exit doesn't work in a thread
            os._exit(1)
        except KeyboardInterrupt:
            if shutdown_message:
                self.stdout.write(shutdown_message)
            sys.exit(0)


    def get_handler(self, *args, **options):
        """Return the default WSGI handler for the runner."""
        return get_internal_wsgi_application()

```
- `handler = self.get_handler(*args, **options) `

- RUN其实主要调用的是get_handler(*args, **options)，调用的是`get_internal_wsgi_application（）`方法
```PYTHON

def get_internal_wsgi_application():
    """
    Load and return the WSGI application as configured by the user in
    ``settings.WSGI_APPLICATION``. With the default ``startproject`` layout,
    this will be the ``application`` object in ``projectname/wsgi.py``.

    This function, and the ``WSGI_APPLICATION`` setting itself, are only useful
    for Django's internal server (runserver); external WSGI servers should just
    be configured to point to the correct application object directly.

    If settings.WSGI_APPLICATION is not set (is ``None``), return
    whatever ``django.core.wsgi.get_wsgi_application`` returns.
    """
    from django.conf import settings
    app_path = getattr(settings, 'WSGI_APPLICATION')
    if app_path is None:
        return get_wsgi_application()

    try:
        return import_string(app_path)
    except ImportError as err:
        raise ImproperlyConfigured(
            "WSGI application '%s' could not be loaded; "
            "Error importing module." % app_path
        ) from err
```
其实就是导入`core.wsgi.application` ,就是return `core.wsgi.application`,查看`core.wsgi.application `，
,其实就是返回`WSGIHandler()`,这里要注意`CORE`即为你的项目名称


- `run(self.addr, int(self.port), handler, ipv6=self.use_ipv6, threading=threading, server_cls=self.server_cls)`
这里就是启动一个WSGI服务了。run的代码如下
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

很明显，就是实例化 WSGIServer(server_address, WSGIRequestHandler, ipv6=ipv6)，然后启动。
这就完成了一个 WSGI服务的启动