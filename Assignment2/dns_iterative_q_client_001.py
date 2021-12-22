import argparse
import dns.message
import dns.resolver
import dns.query
from socket import *
# import sys
# # reload(sys)
# sys.setdefaultencoding('utf8')


QUERY = 'www.bilibili.com'
SOURSE_IP = '10.21.8.110'
SOURSE_PORT = 14000
SERVER_PORT = 53
SERVER_IP = '8.8.8.8'
RDCLASS = 'IN'
RDTYPE_A = 'A'
RDTYPE_NS = 'NS'

parser = argparse.ArgumentParser()
parser.add_argument("-q",help="please specify the name of query")
parser.add_argument("-s",help="please specify the source IP address query")
parser.add_argument("-p",help="please specify the source port number of query",type=int)
parser.add_argument("-server",help="please specify the IP address of Local DNS server")
#parser.add_argument("-display",help="can print the information about every DNS query and response")

args = parser.parse_args()
if args.q:
    QUERY = args.q

if args.s:
    SOURSE_IP=args.s
if args.p:
    SOURSE_PORT=args.p
if args.server:
    SERVER_IP = args.server


def makeMessage(qname, rdtype, serverIP):  # 给定 查询域名，rdtype, 服务器ip,得到response报文
    message = dns.message.make_query(qname, rdtype)
    message.flags = 0X0020
    responseMessage = dns.query.udp(message, serverIP, port=SERVER_PORT, source=SOURSE_IP, source_port=SOURSE_PORT)
    return responseMessage


rdtype = RDTYPE_NS
serverIP = SERVER_IP
qname = "<Root>"
serverName = "Local DNS server"
aliases = ''
cName = QUERY
qAddress = []
nameServer = ''
responseMessage = makeMessage("<Root>", rdtype, serverIP)

while 1:
    queryMessage="\n(%s#%d) send query(%s %s %s rd=0) to DNS Server: (%s %s#%d)" % (
        SOURSE_IP, SOURSE_PORT, qname, rdtype, RDCLASS, serverName, serverIP, SERVER_PORT)
    print(queryMessage.encode('utf-8'))  # 打印查询信息
    # print('('+SOURSE_IP+'#'+SOURSE_PORT+') send query('+message.keyname,rdtype,RDCLASS,'rd=0)')
    response=("response message:\n"+responseMessage.to_text()).encode('utf-8')
    print(response)  # 打印返回信息
    if responseMessage.answer:
        first_ans = str(responseMessage.answer[0]).split('\n')[0].split()  # answer的第一行

        if nameServer == '':  # 如果更新权威服务器查权威服务器，否则查给定域名
            qname = cName
        else:
            qname = nameServer

        serverName = first_ans[0]
        serverIP = first_ans[4]
        # for i in responseMessage.answer:
        #     print("ans items:",i.to_text())

        # print("firstans[0]:",first_ans[0])
        if first_ans[3] != str(responseMessage.question[0]).split()[2]:  # ans 和question rdtype 不匹配
            # print("ans:",first_ans[3])
            # print("quest:",str(responseMessage.question[0]).split()[2])
            cName = first_ans[4]  # 得到cname

            if responseMessage.additional:
                serverName = str(responseMessage.additional[0]).split()[0]
                serverIP = str(responseMessage.additional[0]).split()[4]
                qname = cName  # 开始查cname
                aliases = QUERY  # 查询域名为aliases
                # print("cname:", cName)

            else:  # 类型不匹配且只有 answer RRS 从头查起
                print("嘿嘿嘿嘿嘿嘿哈哈哈哈")
                qname = "<Root>"
                serverName = 'Local DNS server'
                serverIP = SERVER_IP


        elif first_ans[0] == cName or first_ans[0] == aliases \
                or first_ans[0][:-1] == cName or first_ans[0][:-1] == aliases:
            # answer 第一个(末尾可能有.)是cname或aliases 得到答案跳出循环
            items = str(responseMessage.answer[0]).split('\n')
            for i in items:
                qAddress.append(i.split()[4])
            break

        elif first_ans[0] == nameServer:  # 查询到权威服务器ip
            print("哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈")
            qname = cName  # ？？？？

        # print("serverIP ans:", serverIP)

        rdtype = RDTYPE_A

        



    elif responseMessage.additional:
        serverName = str(responseMessage.additional[0]).split()[0]
        serverIP = str(responseMessage.additional[0]).split()[4]
        # print("serverIP add:", serverIP)

        if nameServer == '':
            qname = cName
        else:
            qname = nameServer

        rdtype = RDTYPE_A

        

    elif responseMessage.authority:
        serverName = 'Local DNS server'
        serverIP = SERVER_IP
        if qname == '<Root>':  # 查询 root时
            # for i in responseMessage.authority:  # 只有authority
            #     print("item in auth:", i.to_text())
            qname = str(responseMessage.authority[0]).split()[4]
            # print("qname:", qname)

            rdtype = RDTYPE_A

            

        else:
            nameServer = str(responseMessage.authority[0]).split()[4]
            qname = "<Root>"

            rdtype = RDTYPE_NS


    print("\n下次：(%s#%d) send query(%s %s %s rd=0) to DNS Server: (%s %s#%d)" % (
    SOURSE_IP, SOURSE_PORT, qname, rdtype, RDCLASS, serverName, serverIP, SERVER_PORT))  # 打印查询信息
    responseMessage = makeMessage(qname, rdtype, serverIP)           

print("Final Answer:")
print("Name:", cName)
print("Addresses:")
for ip in qAddress:
    print(ip)
if aliases != '':
    print("Aliases:", aliases)
