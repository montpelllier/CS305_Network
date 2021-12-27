import hashlib
import math
import random
import time
from threading import Thread

from Project2.Proxy import Proxy

chunk_size = 16000


class PClient:
    def __init__(self, tracker_addr: (str, int), proxy=None, port=None, upload_rate=0, download_rate=0):

        if proxy:
            self.proxy = proxy
        else:
            self.proxy = Proxy(upload_rate, download_rate, port)  # Do not modify this line!

        self.tracker = tracker_addr
        self.online_thread = Thread(target=self.online)
        self.upload_thread = Thread(target=self.upload)

        self.online_flag = True  # 结束线程
        self.local_data = {}  # 本地储存的文件 fid-[chunk]
        self.neighbor_client = {}  # 邻居节点队列 fid-[client]
        self.fast_client = {}  # 最快的节点 fid-[client]
        self.neighbor_chunk = {}  # 邻居节点拥有的块 fid-[chunk-[client]]
        self.accept = {}  # fid-[bool]
        self.p2p_state = {} # 标注自己是否还在网络
        # self.downloading_state = {}  # 下载状态
        # self.client_list = {}  # 邻居节点队列
        # self.fast_client = {}  # 发送的节点
        # self.reg_state = {}  # 标注注册的文件状态，是否成功注册

        # self.send_queue = {}

        self.online_thread.start()
        self.upload_thread.start()

    def __send__(self, data: bytes, dst: (str, int)):
        """
        Do not modify this function!!!
        You must send all your packet by this function!!!
        :param data: The data to be send
        :param dst: The address of the destination
        """
        self.proxy.sendto(data, dst)

    def __recv__(self, timeout=None) -> (bytes, (str, int)):
        """
        Do not modify this function!!!
        You must receive all data from this function!!!
        :param timeout: if its value has been set, it can raise a TimeoutError;
                        else it will keep waiting until receive a packet from others
        :return: a tuple x with packet data in x[0] and the source address(ip, port) in x[1]
        """
        return self.proxy.recvfrom(timeout)

    @staticmethod
    def str_to_client(client_str) -> (str, int):
        client_str = client_str[1:-1]
        return client_str.split(",")[0].split("\"")[1], int(client_str.split(", ")[1])

    def register(self, file_path: str):
        """
        Share a file in P2P network
        :param file_path: The path to be shared, such as "./alice.txt"
        :return: fid, which is a unique identification of the shared file and can be used by other PClients to
                 download this file, such as a hash code of it
        """
        """
        Start your code below!
        """
        with open(file_path, 'rb') as f:  # 生成种子文件, hash码+分片总数
            data = f.read()
        file = hashlib.md5(data).hexdigest()
        length = math.ceil(len(data) / chunk_size)
        fid = file + "#" + str(length)  # 生成fid

        self.p2p_state[fid] = True
        self.neighbor_client[fid] = []
        self.fast_client[fid] = []
        self.accept[fid] = [False for _ in range(length)]
        self.neighbor_chunk[fid] = [[] for _ in range(length)]
        self.local_data[fid] = [None for _ in range(length)]

        reg_msg = b'JOIN:' + fid.encode()
        self.__send__(reg_msg, self.tracker)  # 注册

        for i in range(length):
            self.local_data[fid][i] = data[i * chunk_size: i * chunk_size + chunk_size]
        # 本地文件
        """
        End of your code
        """
        return fid

    def download(self, fid) -> bytes:
        """
        Download a file from P2P network using its unique identification
        :param fid: the unique identification of the expected file, should be the same type of the return value of share()
        :return: the whole received file in bytes
        """
        data = None
        """
        Start your code below!
        """
        length = int(fid.split("#")[1])

        self.neighbor_chunk[fid] = [[] for _ in range(length)]
        self.local_data[fid] = [None for _ in range(length)]
        self.accept[fid] = [True for _ in range(length)]
        self.p2p_state[fid] = True
        self.fast_client[fid] = []
        self.neighbor_client[fid] = []


        self.__send__(b'JOIN:' + fid.encode(), self.tracker)

        while True:
            time.sleep(0.5)
            data, isComplete = b'', True
            for chunk in self.local_data[fid]:
                if chunk is None:
                    isComplete = False
                    break
                else:
                    data += chunk
            if isComplete:
                print(self.proxy.port, "download finish")
                break
        """
        End of your code
        """
        return data

    def cancel(self, fid):
        """
        Stop sharing a specific file, others should be unable to get this file from this client any more
        :param fid: the unique identification of the file to be canceled register on the Tracker
        :return: You can design as your need
        """
        cancel_msg = "CANCEL:" + fid
        self.__send__(cancel_msg.encode(), self.tracker)
        while self.p2p_state[fid]:
            time.sleep(0.05)
        self.neighbor_client.pop(fid)
        self.fast_client.pop(fid)
        """
        End of your code
        """

    def close(self):
        """
        Completely stop the client, this client will be unable to share or download files any more
        :return: You can design as your need
        """
        file_list = list(self.neighbor_client.keys())
        for fid in file_list:
            self.cancel(fid)
        self.online_flag = False
        print(self.proxy.port, "closed!")
        """
        End of your code
        """
        self.proxy.close()

    def upload(self):
        while True:
            if not self.online_flag:
                break
            time.sleep(0.05)
            for fid in self.local_data:
                i = 0
                rare_chunk = []
                num = math.inf
                node = None
                for chunk in self.local_data[fid]:
                    if chunk is not None and fid in self.neighbor_chunk:
                        if len(self.neighbor_chunk[fid][i]) < num:
                            num = len(self.neighbor_chunk[fid][i])
                            rare_chunk = [i]
                        elif len(self.neighbor_chunk[fid][i]) == num:
                            rare_chunk.append(i)
                    i += 1
                # 搜索稀缺资源
                if rare_chunk:
                    i = random.choice(rare_chunk)  # 随机选一个
                    if fid not in self.fast_client:
                        continue
                    for client in self.fast_client[fid]:
                        if fid not in self.neighbor_chunk:
                            continue
                        if client not in self.neighbor_chunk[fid][i]:
                            node = PClient.str_to_client(client)
                            self.neighbor_chunk[fid][i].append(client)
                            # print(type(node), node)
                            break
                    if node is not None:  # 询问要不要
                        upload_msg = "UPLOAD:" + fid + "-" + str(i)
                        # print(self.proxy.port, upload_msg)
                        self.__send__(upload_msg.encode(), node)

    def online(self):
        while True:
            if not self.online_flag:
                break
            try:
                msg, frm = self.__recv__(0.5)
            except Exception:
                continue
            # msg, client = msg.decode(), "(\"%s\", %d)" % frm
            client = "(\"%s\", %d)" % frm

            if msg.startswith(b'JOIN:'):
                fid, nodes = msg[5:].decode().split(":")
                nodes = nodes.split("-")
                for node in nodes:
                    if node == '':
                        continue
                    self.neighbor_client[fid].append(node)
                    self.fast_client[fid].append(node)
                # 新节点加入网络

                #print(self.proxy.port, self.fast_client[fid])

            elif msg.startswith(b'UPLOAD:'):
                chunk_id = msg[7:]
                fid, id = chunk_id.decode().split("-")
                if client not in self.neighbor_chunk[fid][int(id)]:
                    self.neighbor_chunk[fid][int(id)].append(client)

                if self.accept[fid][int(id)]:  # 接受
                    self.accept[fid][int(id)] = False
                    back_msg = b'WANT:' + chunk_id
                    self.__send__(back_msg, frm)
                    # 通知邻居节点
                    for c in self.neighbor_client[fid]:
                        if c != client:
                            node = PClient.str_to_client(c)
                            have_msg = b'HAVE:' + chunk_id
                            self.__send__(have_msg, node)

            elif msg.startswith(b'WANT:'):
                chunk_id = msg[5:]
                fid, id = chunk_id.decode().split("-")
                chunk = self.local_data[fid][int(id)]
                data_msg = b'DATA:' + chunk_id + b':' + chunk
                self.__send__(data_msg, frm)

            elif msg.startswith(b'HAVE:'):
                chunk_id = msg[5:].decode()
                fid, id = chunk_id.split("-")
                self.neighbor_chunk[fid][int(id)].append(client)  # 记录拥有情况

            elif msg.startswith(b'DATA:'):
                chunk_id = msg[5:].split(b':')[0]
                print(self.proxy.port, "from", frm, chunk_id)
                chunk = msg[6 + len(chunk_id):]
                fid, id = chunk_id.decode().split("-")
                self.local_data[fid][int(id)] = chunk
            elif msg.startswith(b'CANCEL-BACK:'):
                fid = msg[12:].decode()
                self.p2p_state[fid] = False
            else:
                print("unexpected message:", msg)


if __name__ == '__main__':
    pass
