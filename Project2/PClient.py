import threading
import time

from Proxy import Proxy
import hashlib
from threading import Thread


def hash(file_path):  # 根据文件内容生成hash值作为fid
    with open(file_path, 'rb') as f:
        data = f.read()
        ret = hashlib.md5(data).hexdigest()
        return ret


class PClient:
    def __init__(self, tracker_addr: (str, int), proxy=None, port=None, upload_rate=0, download_rate=0):
        if proxy:
            self.proxy = proxy
        else:
            self.proxy = Proxy(upload_rate, download_rate, port)  # Do not modify this line!
        self.tracker = tracker_addr
        self.size = 1000
        """
        Start your additional code below!
        """
        # 本地储存的文件
        self.data = {}
        self.lock = threading.RLock()

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
        fid = hash(file_path)
        reg_msg = "REGISTER:" + fid + str(len(fid)/1000)
        print(reg_msg)
        file = open(file_path, "rb")
        file_date = file.read()
        file.close()
        self.data[fid] = file_date
        print(self.tracker)
        self.__send__(reg_msg.encode(), self.tracker)
        msg, frm = self.__recv__()
        msg, client = msg.decode(), "(\"%s\", %d)" % frm
        print("From", client, ": ", msg)
        waiting = Thread(target=self.online)
        waiting.start()

        # 注册后要启动一个while循环接受指令?

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
        query_msg = "QUERY:" + fid
        print(query_msg)

        self.__send__(query_msg.encode(), self.tracker)
        msg, frm = self.__recv__()
        msg, client = msg.decode(), "(\"%s\", %d)" % frm
        print("From", client, ": ", msg)
        owner = msg[2:-2].split("), (")

        # consider the first owner as the candidate
        candidate = (owner[0].split(",")[0].split("\"")[1], int(owner[0].split(", ")[1]))

        request = "REQUEST:" + fid + ",0," + str(self.proxy.download_rate)
        # Thread(self.online()).start()
        self.lock.acquire()
        self.__send__(request.encode(), candidate)

        # while True:
        #     print(self.proxy.port," receiving...")
        #     msg, frm = self.__recv__()
        #     """
        #     status was the flag send by the host,
        #     0: the first bag of the data
        #     1: the bag is not finnish
        #     2: the end of the bag
        #     """
        #     msg, client = msg.decode(), "(\"%s\", %d)" % frm
        #     print(self.proxy.port, " received!")
        #     status = msg[9:10]
        #     fid = msg[10:42]
        #     data = msg[42:]
        #     if status == "0":
        #         self.data[fid] = data
        #         self.__send__("continue".encode(), frm)
        #     elif status == "1":
        #         self.data[fid] += data
        #         self.__send__("continue".encode(), frm)
        #     else:
        #         self.data[fid] += data
        #         self.__send__("Download Success!".encode(), frm)
        #         self.lock.release()
        #         break
        data = self.data[fid]
        reg_msg = "REGISTER:" + fid
        self.__send__(reg_msg.encode(), self.tracker)
        Thread(target=self.online).start()

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

        self.lock.acquire()
        self.__send__(cancel_msg.encode(), self.tracker)
        msg, frm = self.__recv__()
        self.lock.release()

        # del self.data[fid]

        """
        End of your code
        """

    def close(self):
        """
        Completely stop the client, this client will be unable to share or download files any more
        :return: You can design as your need
        """
        for key in self.data.keys():
            self.cancel(key)
        print("closed!")
        """
        End of your code
        """
        self.proxy.close()

    def online(self):
        print("come in")
        while True:
            try:
                msg, frm = self.__recv__(1)
            except Exception:
                continue
            msg, client = msg.decode(), "(\"%s\", %d)" % frm

            if msg.startswith("REQUEST:"):
                fid, section, down_rate = msg[8:].split(",")
                section, down_rate = int(section), int(down_rate)
                rate = min(self.proxy.upload_rate, down_rate)
                # rate = int(rate/1000)

                data = ""
                for i in self.data.keys():
                    if i == fid:
                        data = self.data[i]
                        break
                # max_len = 5000
                # bag_num = 0
                print("len:", len(data))
                left = section * 1000
                right = min((section+rate)*1000, len(data))

                data = str(section)+","+str(section+right)+str(data[section: section+rate])
                self.__send__(data.encode())


            #     while True:
            #         if bag_num*max_len < len(data) and bag_num != 0:
            #             b_data = "RESPONSE:" + "1" + str(fid) + str(data[bag_num*max_len:bag_num*max_len+max_len])
            #             print("before sending...")
            #             self.__send__(b_data.encode(), frm)
            #             print("send done")
            #             msg, frm = self.__recv__()
            #             print("recv")
            #             msg, client = msg.decode(), "(\"%s\", %d)" % frm
            #             print("msg", msg)
            #             bag_num += 1
            #             if msg.startswith("continue"):
            #
            #                 continue
            #             else:
            #                 break
            #         elif bag_num == 0:
            #             b_data = "RESPONSE:" + "0" + str(fid) + str(data[bag_num*max_len:bag_num*max_len+max_len])
            #             print("before sending...")
            #             self.__send__(b_data.encode(), frm)
            #             print("send done")
            #             msg, frm = self.__recv__()
            #             print("recv")
            #             msg, client = msg.decode(), "(\"%s\", %d)" % frm
            #             print("msg", msg)
            #             bag_num += 1
            #             if msg.startswith("continue"):
            #                 print(msg)
            #                 continue
            #             else:
            #                 break
            #         else:
            #             b_data = "RESPONSE:" + "2" + str(fid) + str(data[bag_num*max_len:])
            #             print("before sending...")
            #             self.__send__(b_data.encode(), frm)
            #             print("send done")
            #             msg, frm = self.__recv__()
            #             print("recv")
            #             msg, client = msg.decode(), "(\"%s\", %d)" % frm
            #             print("msg", msg)
            #             if msg.startswith("continue"):
            #                 print(msg)
            #                 continue
            #             else:
            #                 print("bag_num:", bag_num)
            #                 break
            #
            # print("break")
            # data = "RESPONSE:" + "0" + fid + data
            # self.__send__(data.encode(),frm)
            # msg, frm = self.__recv__()
            # msg, client = msg.decode(), "(\"%s\", %d)" % frm
            # print("From", client, ": ", msg)

            # if msg.startswith("RESPONSE:"):
            #     """
            #     status was the flag send by the host,
            #     0: the first bag of the data
            #     1: the bag is not finnish
            #     2: the end of the bag
            #     """
            #     status = msg[9:10]
            #     fid = msg[10:41]
            #     data = msg[41:]
            #     self.data[fid] = data
            #     self.__send__("Download Success!".encode(), frm)
            #     # self.register(fid)
            #     return self.data[fid]

    def test(self):
        time.sleep(2)
        print("end")


if __name__ == '__main__':
    pass
