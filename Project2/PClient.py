import math
import random
import threading
import time

from Project2.Proxy import Proxy
import hashlib
from threading import Thread

chunk_size = 16000


# def torrent(file_path):  # 根据文件内容生成hash值作为fid
#     with open(file_path, 'rb') as f:
#         data = f.read()
#     ret = hashlib.md5(data).hexdigest()
#     length = math.ceil(len(data) / chunk_len)
#     return ret, length


class PClient:
    def __init__(self, tracker_addr: (str, int), proxy=None, port=None, upload_rate=0, download_rate=0):
        self.start = None
        if proxy:
            self.proxy = proxy
        else:
            self.proxy = Proxy(upload_rate, download_rate, port)  # Do not modify this line!

        self.tracker = tracker_addr
        self.online_thread = Thread(target=self.online)
        self.chunk_thread = Thread(target=self.update_chunks)

        self.online_flag = True  # 结束线程
        self.local_data = {}  # 本地储存的文件
        self.downloading_state = {}  # 下载状态
        self.client_list = {}  # 可请求的节点队列
        self.fast_client = {}
        self.reg_state = {}  # 标注注册的文件状态，是否成功注册

        self.online_thread.start()
        self.chunk_thread.start()

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

        reg_msg = b'REGISTER:' + fid.encode()
        self.__send__(reg_msg, self.tracker)
        self.reg_state[fid] = False
        self.local_data[fid] = data  # 本地文件

        while not self.reg_state[fid]:
            time.sleep(0.001)
        """
        End of your code
        """
        return fid

    def ask(self):
        for fid in self.local_data.keys():
            if isinstance(self.local_data[fid], list):  # 还在下载
                for client in self.client_list[fid]:
                    ask_msg = b'ASK:' + fid.encode()
                    self.__send__(ask_msg, client)

    def update_chunks(self):
        while True:
            if not self.online_flag:
                break
            self.ask()
            time.sleep(10)

    def scarce_chunk(self, fid) -> int:
        id_list, i, length, = [], 0, math.inf
        for chunk in self.local_data[fid]:
            if isinstance(chunk, list) and len(chunk) > 0:
                if len(chunk) == length:
                    id_list.append(i)
                elif len(chunk) < length:
                    length = len(chunk)
                    id_list.clear()
                    id_list.append(i)
            i += 1
        try:
            return random.choice(id_list)
        except:
            return -1

    def download(self, fid) -> bytes:
        """
        Download a file from P2P network using its unique identification
        :param fid: the unique identification of the expected file, should be the same type of the return value of share()
        :return: the whole received file in bytes
        """
        """
        Start your code below!
        """
        length = int(fid.split("#")[1])
        self.local_data[fid] = [[] for _ in range(length)]
        self.client_list[fid] = []
        self.fast_client[fid] = {}  # client-speed
        ask_once, candidate = True, None

        while isinstance(self.local_data[fid], list):
            if not self.client_list[fid]:
                query_msg = "QUERY:" + fid  # 从tracker获取client表
                self.__send__(query_msg.encode(), self.tracker)

            while not self.client_list[fid]:
                time.sleep(0.001)

            if ask_once:
                self.ask()
                ask_once = False

            if candidate is None:
                candidate = self.client_list[fid][0]

            id = -1
            while id == -1:
                id = self.scarce_chunk(fid)
                time.sleep(0.001)

            chunk_req = fid + "-" + str(id)
            self.downloading_state[chunk_req] = True

            request = "REQUEST:" + chunk_req
            self.__send__(request.encode(), candidate)
            while self.downloading_state[chunk_req]:
                time.sleep(0.001)

            temp, isComplete = b'', True
            for chunk in self.local_data[fid]:
                if isinstance(chunk, list):
                    isComplete = False
                    break
                else:
                    temp += chunk
            if isComplete:
                self.local_data[fid] = temp

        reg_msg = "REGISTER:" + fid
        self.__send__(reg_msg.encode(), self.tracker)
        data = self.local_data[fid]
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
        while self.reg_state[fid]:
            time.sleep(0.001)
        """
        End of your code
        """

    def close(self):
        """
        Completely stop the client, this client will be unable to share or download files any more
        :return: You can design as your need
        """
        for fid in self.reg_state.keys():
            self.cancel(fid)
        self.online_flag = False
        self.chunk_thread.join()
        self.online_thread.join()
        print("closed!")
        """
        End of your code
        """
        self.proxy.close()

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

            if msg.startswith(b'REQUEST:'):
                fid, chunk_id = msg[8:].decode().split("-")
                chunk, chunk_id = b'', int(chunk_id)
                if fid in self.local_data:
                    if not isinstance(self.local_data[fid], list):  # 完整文件
                        chunk = self.local_data[fid][chunk_id * chunk_size:chunk_id * chunk_size + chunk_size]
                    elif not isinstance(self.local_data[fid][chunk_id], list):  # 正在下载
                        chunk = self.local_data[fid][chunk_id]

                back_msg = b'REQUEST-BACK:' + msg[8:] + b':' + chunk
                self.__send__(back_msg, frm)

            elif msg.startswith(b'REQUEST-BACK:'):

                chunk_id = msg[13:].split(b':')[0].decode()  # str
                chunk = msg[14 + len(chunk_id):]  # byte
                print("From", client, self.proxy.port, chunk_id)
                self.downloading_state[chunk_id] = False
                if chunk:
                    fid, id = chunk_id.split("-")
                    self.local_data[fid][int(id)] = chunk
            elif msg.startswith(b'REGISTER:'):
                state, fid = msg[9:].decode().split(",")
                if state == "Success":
                    self.reg_state[fid] = True
            elif msg.startswith(b'CANCEL:'):
                state, fid = msg[7:].decode().split(",")
                if state == "Success":
                    self.reg_state[fid] = False
            elif msg.startswith(b'ASK:'):  # 询问拥有的片段
                fid = msg[4:].decode()
                chunk_list = []
                if fid in self.local_data.keys():
                    if isinstance(self.local_data[fid], list):  # 还在下载
                        left, right, last = 0, 0, None
                        for chunk in self.local_data[fid]:
                            if not isinstance(chunk, list) and isinstance(last, list):
                                left = right
                            elif isinstance(chunk, list) and not isinstance(last, list):
                                chunk_list.append((left, right))  # 打包
                            last, right = chunk, right + 1
                            if right == len(self.local_data[fid]) and chunk is not None:
                                chunk_list.append((left, right))
                    else:
                        length = int(fid.split("#")[1])
                        chunk_list.append((0, length))
                back_msg = "ASK-BACK:" + fid + ":" + str(chunk_list)
                self.__send__(back_msg.encode(), frm)
            elif msg.startswith(b'QUERY-BACK:'):
                fid, msg = msg[11:].decode().split(":")
                owner = msg[2:-2].split("), (")
                if owner != ['']:
                    if fid not in self.client_list:
                        self.client_list[fid] = []
                    for c in owner:
                        client = c.split(",")[0].split("\"")[1], int(c.split(", ")[1])
                        if int(c.split(", ")[1]) != self.proxy.port:
                            self.client_list[fid].append(client)
                # consider the first owner as the candidate

            elif msg.startswith(b'ASK-BACK:'):

                fid, msg = msg[9:].decode().split(":")
                ranges = msg[2:-2].split("), (")
                length = int(fid.split("#")[1])
                has_chunk = [False for _ in range(length)]

                if isinstance(self.local_data[fid], list):  # 文件还在下载
                    for r in ranges:
                        left, right = int(r.split(", ")[0]), int(r.split(", ")[1])
                        for i in range(left, right):
                            has_chunk[i] = True
                    # 有哪些chunk
                    i = 0
                    for chunk in self.local_data[fid]:
                        if isinstance(chunk, list):  # 文件块还在下载
                            if has_chunk[i]:  # 有该文件块
                                if client not in chunk:  # 添加client
                                    self.local_data[fid][i].append(client)
                            elif client in chunk:  # 删除client
                                self.local_data[fid][i].remove(client)
                        i += 1


            else:
                print("unexpected message:", msg)


if __name__ == '__main__':
    pass
