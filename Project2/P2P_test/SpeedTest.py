import time
from threading import Thread

from Project2.PClient import PClient
from Project2.SC_model.client import Client
from Project2.SC_model.server import Server

tracker_address = ("127.0.0.1", 10086)
#"../test_files/bg.png"
#"../test_files/alice.txt"
file_path =  "../test_files/bg.png"

def client_download(client):
    client.download(file_path)


if __name__ == '__main__':
    # A, B, C, D, E join the network
    A = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    B = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    C = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    D = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    E = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    fid = A.register(file_path)
    files = {}
    clients = [B, C, D, E]
    threads = []

    # function for download and save
    def download(node, index):
        files[index] = node.download(fid)

    for i, client in enumerate(clients):
        threads.append(Thread(target=download, args=(clients[i], i)))

    time_start = time.time_ns()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"Time of P2P model: {(time.time_ns() - time_start) * 1e-9}")
    with open(file_path, "rb") as bg:
        bs = bg.read()
        for i in files:
            if files[i] != bs:
                raise Exception()

    A.close()
    for c in clients:
        c.close()

    # SC model
    server = Server(upload_rate=100000, download_rate=1000000, port=10087)
    server.start()
    # the download rate of different clients
    rates = [100000, 100000, 100000, 100000]
    threads.clear()

    for i, rate in enumerate(rates):
        c = Client("c%d" % (i + 1), rate)
        threads.append(Thread(target=client_download, args=[c]))

    time_start = time.time_ns()
    for thread in threads:
        thread.start()

    for t in threads:
        t.join()
    print(f"Time of SC model: {(time.time_ns() - time_start) * 1e-9}")
    server.close()
