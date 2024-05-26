"""
    这是一个简单的网络代理服务器，它的作用是监听本地的 8888 端口，
    然后获取用户浏览器的网络请求，将其发送到对应服务器，并将相应数据
    分发给用户浏览器

    本代理服务器支持 自定义网站屏蔽列表，用户可以在同目录下的 'blacklists.txt'
    文件中添加不喜欢的网站的域名（支持 正则表达式），本代理服务器将会把在黑名单
    中的域名的请求替换为 本机回环地址（'127.0.0.1'）

    本代理服务器也支持 自定义用户过滤列表，可以防止某些用户访问外部网站

    作者：李悠然
    作者的班级：计科二班
    作者的学号：2022405532
"""

import socket
import threading
import re
import os

# 逐行读取同目录下的 'blacklists.txt' 文件，并将其内容添加到屏蔽列表中
blacklists = []
with open('blacklists.txt') as bl:
    blacklists = bl.readlines()

# 再逐行读取同目录下的 'blockusers.txt' 文件，并将其内容添加到过滤用户名单中
blockusers = []
with open('blockusers.txt') as bu:
    blockusers = bu.readlines()

class http_proxy:
    """
    这是实现整个 HTTP 代理服务器的基础结构
    """
 
    def __init__(self, init_sock : socket):
        """
        http_proxy 类的构造方法，它将对传入的套接字进行接收操作
        """
        self.__method = None
        header = b''
        try:
            while True:
                # 循环接收套接字 conn 的请求报文，并将其添加为 http_proxy 的 header 部分
                # 直到其请求报文到达结尾（'\r\n\r\n'）
                data = init_sock.recv(4096)
                header = b"%b%b" % (header, data)
                if header.endswith(b'\r\n\r\n') or (not data):
                    break
        except:
            pass

        # 下面的四个数据成员中，除了 header_list，其它的数据成员都定义为私有成员
        self.__header = header
        self.header_list = header.split(b'\r\n')
        self.__host = None
        self.__port = None
 
    def get_method(self):
        """
        获取请求方式
        """
        if self.__method is None:
            self.__method = self.__header[:self.__header.index(b' ')]
        return self.__method
 
    def get_host_info(self, if_hook_host = False, detour_host = b'www.baidu.com'):
        """
        获取目标主机的ip和端口
        这里我尝试过对请求的 Host 进行第三方引导，但是浏览器识别出了我在假冒原来的网站，
        对我的返回进行了拦截，详情请参见实验报告文档
        
        复现方法：
            使用同目录下的 old_proxy.py 文件启动代理服务器即可
        """
        if self.__host is None:
            method = self.get_method()
            line = self.header_list[0].decode('utf8')

            # 根据请求方法是否为 CONNECT 执行不同的解析程序
            if method == b"CONNECT":
                host = line.split(' ')[1]
                if ':' in host:
                    host, port = host.split(':')
                else:
                    port = 443
            else:
            # 逐项检测 header_list 中的字节串，提取 host 和 port 数据 
                for i in self.header_list:
                    if i.startswith(b"Host:"):
                        host = i.split(b" ")
                        if len(host) < 2:
                            continue
                        host = host[1].decode('utf8')
                        break
                else:
                    host = line.split('/')[2]
                if ':' in host:
                    host, port = host.split(':')
                else:
                    port = 80

            # 屏蔽用户定义的黑名单网站（返回本机回环地址 '127.0.0.1'）
            for entry in blacklists:
                if re.match(entry.strip(), host):
                    self.__host = '127.0.0.1'
                    break
            else:
                self.__host = host
            self.__port = int(port)

        # 如果启用了 hook，那么返回指定的第三方 Host 
        if if_hook_host:
            print('原来的请求信息:\n' + self.__header.decode())
            temp = self.__header.replace(self.__host.encode(), detour_host)
            self.__host = detour_host
            print('转换后的请求信息：\n' + temp.decode())
            self.__header = temp
            return detour_host, self.__port
        
        # 否则返回正确的请求数据
        else:
            return self.__host, self.__port
 
    @property
    def data(self):
        """
        返回最原始的，未经处理的头部数据
        """
        return self.__header
 
    def is_https(self):
        """
        判断是否为 https 协议
        """
        if self.get_method() == b'CONNECT':
            return True
        return False
 
def communicate(lhs_sock, rhs_sock):
    """
    socket之间的数据交换
    请注意此函数在代理服务器传输数据的不同方向上复用

    例如，当左边的参数是客户端 socket 而右边的参数是服务端 socket 时，
    代表代理服务器从客户端接收请求数据，然后将其转发（sendall）给服务端
    反过来，当左边的参数是服务端 socket 而右边的参数是客户端 socket 时，
    代表代理服务器从服务端接收响应数据，然后将其分发（仍然是 sendall）给客户端
    """
    try:
        while True:
            data = lhs_sock.recv(1024)
            if not data:
                return
            rhs_sock.sendall(data)
    except:
        pass
 
 
printed = False

def process_socket(client):
    """
    处理传入的客户端 socket
    """
    
    global printed

    # 如果当前用户在过滤名单中，那么不提供代理服务
    if is_blocked:
        if not printed:
            printed = True
            print("警告：当前登录的用户为：" + username)
            print("该用户已被代理服务器管理员过滤，将无法提供上网服务")
        return

    # 设置超时时间为 30s
    timeout = 30
    client.settimeout(timeout)
    header = http_proxy(client)
    if not header.data:
        client.close()
        return
    print(*header.get_host_info(), header.get_method())
    proxy_address = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        proxy_address.connect(header.get_host_info())
        proxy_address.settimeout(timeout)

        # 如果使用 https 协议，则向客户端套接字发送特殊的处理信息
        if header.is_https():
            data = b"HTTP/1.0 200 Connection Established\r\n\r\n"
            client.sendall(data)
            new_thread = threading.Thread(target=communicate,args=(client, proxy_address))
            new_thread.start()
        else:
            proxy_address.sendall(header.data)
        communicate(proxy_address, client)
    except:
        proxy_address.close()
        client.close()
 
 
def proxy_start(ip, port):
    """
    代理服务的入口点
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((ip, port))
    s.listen(15)
    print('欢迎使用代理服务器！！！')
    while True:
        conn, addr = s.accept()
        new_thread = threading.Thread(target=process_socket, args=(conn,))
        new_thread.start()
 
# 检测当前用户是否在过滤名单列表中，如果在，那么不提供代理服务
is_blocked = False
username = os.getlogin()
if username in blockusers:
    is_blocked = True
 
if __name__ == '__main__':
    IP = "127.0.0.1"
    PORT = 8888
    proxy_start(IP, PORT)