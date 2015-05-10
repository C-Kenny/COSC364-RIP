import config_parser
import random
import select
import socket
import sys
import time

"""
Author: Rory Varoce and Carl Kenny
Date:   03/05/2015
Prog:   Routing table isn't initialized from config file. Routing table
        is initialized with merely an entry for oneself.
        Routers then listen for incoming advertisements and update
        routing table accordingly (which is pulled from config file,
        compute direct cost from there)
        When a router dies, its direct neighbors set the cost to 16
        and advertise it. Slowly killing the routes profile throughout
        network.
Usage:  $python3 protocol.py file.config
"""

OUTPUT_PORTS = {}   #TODO: Figure out how python's @property system works
INPUT_SOCKETS = []

def create_udp_sockets(input_ports):
    """
    Creates UDP sockets for each input port. Binds one socket to each input port. 
    One input sucket can be used for sending UDP datagrams to neighbors
    :param input_ports int 
    """
    input_sockets = []
    for index_, item in enumerate(input_ports):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', int(item)),)
        input_sockets.append(sock)

    return input_sockets

def message_direct_neighbors():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in OUTPUT_PORTS:
        send = "Ping"
        send = send.encode('utf-8')
        sock.sendto(send, ('0.0.0.0', i))

def get_messages():
    #timeout, void_1, void_2 = select.select(INPUT_SOCKETS, [], [], 10)
    ready_to_read, ready_to_write, in_error = \
            select.select(
                    INPUT_SOCKETS, [], [], timeout)

    if timeout:
        seconds = timeout[0]
        seconds.settimeout(5)
        message, port = seconds.recvform(2)
        print(str(message))

def main(input_file):
    """
    Router ouput ports are input port of another router
    The config file informs saemon about links
    :param input_file str file_name to be parsed
    """
    config_dict = config_parser.parse_config(input_file)
    OUTPUT_PORTS = config_dict["outputs"]  # list
    INPUT_PORTS = config_dict["input-ports"]  # list
    INPUT_SOCKETS = create_udp_sockets(INPUT_PORTS)

    while True:
        # create timeout system
        i = random.randint(-5, 5)
        if i < 0:
            get_messages()
        else:
            message_direct_neighbors()

if __name__ == '__main__':
    try:
        input_file = sys.argv[1]
        main(input_file)
    except IndexError:
        print("RIP requres one config file for the initial setup" +  
        "Usage: $python3 protocol.py file.config")
