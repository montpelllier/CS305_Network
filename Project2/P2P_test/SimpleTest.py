from Project2.PClient import PClient

tracker_address = ("127.0.0.1", 10086)

if __name__ == '__main__':
    # A,B join the network
    A = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    B = PClient(tracker_address, upload_rate=100000, download_rate=100000)

    # A register a file and B download it
    fid = A.register("../test_files/alice.txt")
    data1 = B.download(fid)

    # A cancel the register of the file
    A.close()

    # C join the network and download the file from B
    C = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    data2 = C.download(fid)

    # data3 = open("../test_files/alice.txt", "rb")
    # if data1 == data3:
    #     print("data1 is correct")
    # if data2 == data3:
    #     print("data2 is correct")

    if data1 == data2:
        print("Success!")
    else:
        # print("data1: ", len(data1))
        # print("----------------------------------------------------------------------------------")
        # print("data2: ",len(data2))
        raise RuntimeError

    B.close()
    C.close()
