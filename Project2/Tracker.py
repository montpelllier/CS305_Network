from Proxy import Proxy


class Tracker:
    def __init__(self, upload_rate=10000, download_rate=10000, port=None):
        self.proxy = Proxy(upload_rate, download_rate, port)
        self.files = {}#记录加入file的clients

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

    def response(self, data: str, address: (str, int)):
        self.__send__(data.encode(), address)

    def start(self):
        """
        Start the Tracker and it will work forever
        :return: None
        """
        print("tracker start:", self.proxy.port)
        while True:
            #print("waiting...")
            # frm is ("[IP]",port) and client is ("[IP]",port), see test.py
            # frm is related to the __send__() in Tracker.py, see there and you know
            msg, frm = self.__recv__()
            # msg transmit is bytes, and process in str here.
            # turn frm into string, here client is a string
            msg, client = msg.decode(), "(\"%s\", %d)" % frm
            #print(msg)
            if msg.startswith("REGISTER:"):
                # Client can use this to REGISTER a file and record it on the tracker
                fid = msg[9:]
                if fid not in self.files:  # 注册文件
                    self.files[fid] = []
                self.files[fid].append(client)  # 将节点与文件块绑定
                self.response("REGISTER:Success," + fid, frm)

            elif msg.startswith("QUERY:"):
                # Client can use this to check who has the specific file with the given fid
                fid = msg[6:]
                result = []
                self.files[fid].append(client)
                for c in self.files[fid]:
                    result.append(c)
                for c in result:
                    c = c[1:-1]
                    client = c.split(",")[0].split("\"")[1], int(c.split(", ")[1])
                    self.response("QUERY-BACK:"+fid+":[%s]" % (", ".join(result)), client)

            elif msg.startswith("CANCEL:"):
                # Client can use this msg to cancel the share of a file
                fid = msg[7:]
                if client in self.files[fid]:
                    self.files[fid].remove(client)
                self.response("CANCEL:Success," + fid, frm)
                print("cancel", fid, "of", client)

            # elif msg.startswith("CLOSE"):
            #
            #     for file in self.files:
            #         for chunk in file:
            #             if client in chunk:
            #                 chunk.remove(client)
            #     print("close", client)



if __name__ == '__main__':
    tracker = Tracker(port=10086)
    tracker.start()
