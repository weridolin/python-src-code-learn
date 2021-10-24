<!--
 * @Description:
 * @email: 359066432@qq.com
 * @Author: lhj
 * @software: vscode
 * @Date: 2021-10-24 21:11:11
 * @platform: windows 10
 * @LastEditors: lhj
 * @LastEditTime: 2021-10-24 21:33:46
-->

# django 的 WSGI 服务

众所周知，所有的服务都是按照一定的协议对数据进行 pack,通过 HTTP/TPC 发送到指定 IP:PORT,那么 DJANGO 作为一个 WEB 框架，本身也是绑定监听一个端口，启动一个 HTTP 服务,并且遵循了 `WSGI`协议

## 何为 `WSGI` ?

WSGI 全称 Web Server Gateway Interface，从名称可理解为一个网关，是一个描述 web 服务器和 Python web 应用程序或框架之间通信的规范，它解释了web服务器如何与python-web应用程序/框架通信，以及web应用程序/框架如何被链接以处理请求，怎么理解呢，我们都知道DJANGO的所有接口就是一个个函数或者类，那么从客户端发起一个请求，到一个具体的api处理这一过程，数据是按照什么规范，怎么被传递的呢，``WSGI``就扮演了这个角色，可以说，它是扮演``HTTP请求``到``DJANGO-APP`` **中间者**的角色。
[注：python wsgi pep3333](https://www.python.org/dev/peps/pep-3333/)
![wsgi存在哪里？](../imgs/wsgi.png)
## 启动一个 HTTP 服务
DJANGO的 启动命令``runserver `` 其实就是启动一个HTTP服务。