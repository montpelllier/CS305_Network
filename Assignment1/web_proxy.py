# -*- coding: utf-8 -*-
import datetime
import sys
import threading
from socket import *

GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
IP = '127.0.0.1'
PORT = 8080


class Proxy(threading.Thread):
    def __init__(self, data, address, cache, request, client):
        threading.Thread.__init__(self)
        self.data = data
        self.address = address
        self.cache = cache
        self.request = request
        self.client = client

    def run(self):
        cur = datetime.datetime.utcnow().strftime(GMT_FORMAT)
        if self.request in self.cache:  # request in cache:
            if self.request[0] != 'POST':
                new_data = self.data[:len(self.data) - 2] + b'If-Modified-Since: ' + self.cache[self.request][
                    1].encode() + b'\r\n\r\n'
                response = getResponse(self.address, new_data)
                status_code = response.decode().split(" ")[1]  # 获取状态码
                print(status_code)
                if status_code == '200':  # 网站修改
                    self.cache[self.request] = (response, cur)
                    cacheWriter(self.cache)
                if status_code == '304':  # 未修改
                    response = self.cache[self.request][0]
                    print("Read from cache.")

            else:
                response = self.cache[self.request][0]
                print("Read from cache")
        else:
            print("Connecting to ", self.address)
            response = getResponse(self.address, self.data)
            self.cache[self.request] = (response, cur)
            cacheWriter(self.cache)
        self.client.send(response)  # 将报文传回客户服务器
        return


def addrInput(IP, PORT):
    sys_in = sys.argv[1:]
    if len(sys_in) == 1:
        if int(sys_in[0]) < 65536 & int(sys_in[0]) >= 0:
            PORT = int(sys_in[0])
        else:
            IP = sys_in[0]
    elif len(sys_in) == 2:
        IP = sys_in[0]
        PORT = int(sys_in[1])
    return (IP, PORT)
    # 参数输入及判断


def cacheReader():  # 缓存读取
    file_read = open("Cache.txt", 'r+')
    read_in = file_read.read()
    if read_in:
        cache = eval(read_in)
    else:
        cache = {}
    file_read.close()
    return cache


def cacheWriter(cache):
    file_write = open("Cache.txt", 'w+')
    file_write.write(str(cache))
    file_write.close()


def dataProcessor(data):
    head = data.decode().split('\r\n')[0].split(" ")
    order = head[0]
    host = head[1].split("/")[2]
    # 获得地址和cache的key
    return (host, 80), (order, host)


def getResponse(address, data):
    tcpProSock = socket()  # 创建代理socket
    tcpProSock.connect(address)  # 建立连接
    tcpProSock.send(data)  # 发送请求
    response = tcpProSock.recv(20480)
    tcpProSock.close()  # 关闭socket
    return response


# Create a server socket, bind it to a port and start listening
tcpSerSock = socket(AF_INET, SOCK_STREAM)
# Fill in start.
tcpSerSock.bind(addrInput(IP, PORT))
tcpSerSock.listen(5)  # 允许最大连接数量

cache = cacheReader()
# Fill in end.
while 1:
    # Strat receiving data from the client
    print('Ready to serve...')
    tcpCliSock, addr = tcpSerSock.accept()
    print('Received a connection from:', addr)
    # Proxy the request from the clinet
    # Fill in start.
    while 1:
        data = tcpCliSock.recv(2048)
        address, request = dataProcessor(data)
        proxy = Proxy(data, address, cache, request, tcpCliSock)
        proxy.start()
        proxy.join()
        break
    # Fill in end.
    tcpCliSock.close()

# Fill in start.

# Fill in end.
