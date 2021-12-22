import argparse

import dns.resolver

parser = argparse.ArgumentParser(description="dns client")
parser.add_argument('-q', help="is used to specify the name of query")
parser.add_argument('-s', help="is used to specify the source IP address of query")
parser.add_argument('-p', help="is used to specify the source port number of query")
parser.add_argument('-server', help="is used to specify the IP address of Local DNS server")
parser.add_argument('-display', action='store_true',
                    help="is used to print the information about every DNS query and response")

args = parser.parse_args()  # 处理命令行输入参数

qname = args.q
sourceIP = args.s
sourcePort = int(args.p)  # 将str转换成int类型
root_dns_ip = args.server


# response的成员变量
# int flags   #The DNS flags of the message.
# int id    #The query id; the default is a randomly chosen id.
# list of RRset additional
# list of RRset answer
# list of RRset authority

def display_query(source_ip, source_port, query_name, rtype, server_name, server_ip, response):  # 展示查询过程
    print("(%s#%d) send query(%s %s %s rd=0) to DNS Server: (%s %s#%d)" % (
        source_ip, source_port, query_name, rtype, "IN", server_name, server_ip, 53))
    print(response, "\n")


def root_query(server_ip, source_ip, source_port, display):  # 循环查询到本地dns服务器的地址
    query_name = '<Root>'
    query = dns.message.make_query(query_name, 'NS')  # 根节点查询
    query.flags = 0x0020  # 单次查询
    response = dns.query.udp(query, where=server_ip, source=source_ip, source_port=source_port)
    query_name = str(response.authority[0][0]).split(" ")[0][:-1]
    if display:
        display_query(source_ip, source_port, query_name, 'NS', "Local DNS server", server_ip, response)

    query = dns.message.make_query(query_name, 'A')  # 本地DNS节点查询
    query.flags = 0x0020  # 单次查询
    response = dns.query.udp(query, where=server_ip, source=source_ip, source_port=source_port)
    if display:
        display_query(source_ip, source_port, query_name, 'A', "Local DNS server", server_ip, response)

    return query_name, str(response.answer[0][0])


def dns_query(query_name, dns_ip, dns_name, source_ip, source_port, display):
    query = dns.message.make_query(query_name, 'A')
    query.flags = 0x0020  # 单次查询
    response = dns.query.udp(query, where=dns_ip, source=source_ip, source_port=source_port)
    if display:
        display_query(source_ip, source_port, query_name, 'A', dns_name, dns_ip, response)
    if response.answer:
        answer = str(response.answer[0]).split("\n")
        first_ans = answer[0].split(" ")
        if first_ans[3] == "CNAME":  # 查询到别名CNAME
            query_name = first_ans[4][:-1]  # 更新query name
        else:
            return answer  # 查询结束，直接返回答案

    if response.additional:  # 可直接获得并更新下级dns的名字和ip
        additional = str(response.additional[0]).split(" ")
        dns_name, dns_ip = additional[0][:-1], additional[-1]
        return dns_query(query_name, dns_ip, dns_name, source_ip, source_port, display)  # 递归查询

    if response.authority:  # 只有下级dns的名字，去本地dns服务器查询其ip后更新当前dns名字、ip再继续查询
        dns_name = str(response.authority[0][0]).split(" ")[0][:-1]
        dns_answer = dns_query(dns_name, local_dns_ip, local_dns_name, source_ip, source_port, display)[0].split(" ")
        dns_name, dns_ip = dns_answer[0][:-1], dns_answer[-1]  # 更新当前dns的名字和ip
        return dns_query(query_name, dns_ip, dns_name, source_ip, source_port, display)  # 继续递归查询

    if not response.answer and not response.additional and not response.authority:
        raise Exception("No information received!")  # 没有得到任何查询结果，结束查询并抛出异常
    else:  # 只拿到CNAME，重新从本地dns查询
        return dns_query(query_name, local_dns_ip, local_dns_name, source_ip, source_port, display)


local_dns_name, local_dns_ip = root_query(root_dns_ip, sourceIP, sourcePort, args.display)
final_answer = dns_query(qname, local_dns_ip, local_dns_name, sourceIP, sourcePort, args.display)
final_name, final_ip = None, []

for ans in final_answer:  # 解析最终的查询结果并打印
    ans_list = str(ans).split(" ")
    final_name = ans_list[0][:-1]
    final_ip.append(ans_list[-1])

print("Final Answer:\nName: ", final_name, "\nAddress:")
for ip in final_ip:
    print(ip)
if final_name != args.q:
    print("Aliases: ", args.q)
