import socket
import threading
from sys import argv


def send_file(socket_port, packet_length):
    # socket initialization
    sock_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_client.bind((UDP_IP, socket_port))
    sock_client.settimeout(0.1)

    # file initialization
    filename, address = sock_client.recvfrom(1024)
    print("received :", filename.decode('utf-8'))
    file = open('files/' + filename.decode('utf-8').rstrip('\0'), 'rb')
    content = file.read()

    step = 0
    NUM_SEG = 1  # the number of the segment

    # loop where we send the file in packets of <packet_length> length
    while step * packet_length <= len(content):
        # we adapt the end of the sequence to the length of the content in order not to send random
        # data from the memory
        end = (step + 1) * packet_length if (step + 1 * packet_length) < len(content) else len(content)

        # we create the segment number on 6 bytes then we add the content of the file
        SEG = bytes(str(NUM_SEG).zfill(6), 'utf-8')
        SEG += content[step * packet_length:end]
        print("send : ", NUM_SEG)
        sock_client.sendto(SEG, address)

        # we need to use a try except block because of the timeout on the socket, which allows us to
        # send the packet again if lost
        try:
            data_ack, address = sock_client.recvfrom(1024)
            print("received :", data_ack.decode('utf-8'))

            # if the segment number does not match the ACK number we stay at the same segment number
            # else we go to the next one
            if data_ack.decode('utf-8').rstrip('\0') != "ACK" + str(NUM_SEG).zfill(6):
                NUM_SEG += -1
            else:
                step += 1
                NUM_SEG += 1
        except socket.timeout:
            print("no ACK received, trying sending again")
            continue

    # when we reach the end of the content we send a message "FIN" to the client to end the communication
    MESSAGE_FIN = bytes("FIN", 'utf-8')
    sock_client.sendto(MESSAGE_FIN, address)


if __name__ == "__main__":
    # initialization of the arguments from the command line
    if len(argv) < 2:
        print("Use of the program : 'python3 " + argv[0] + " <port number>'")
        exit(1)

    if int(argv[1]) <= 1000:
        print("The port number must be above 1000")
        exit(1)

    port = int(argv[1])

    # we listen to every interfaces on port given by args on the console
    UDP_IP = ''
    UDP_PORT = port

    # socket initialization
    sock = socket.socket(socket.AF_INET,
                         socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    # we give a new port to send the file that's above the original port
    port_new = port + 1 if port + 1 < 65535 else 1001

    #
    while 1:
        # receiving the SYN from the client
        data, addr = sock.recvfrom(1024)
        print("received :", data.decode('utf-8'))
        port_new = port_new + 1 if port_new + 1 < 65535 else 1001

        # we start the thread before sending the SYN-ACK because the thread can take too much time to start
        # and the client try to connect to a socket that does not exist yet, causing an error
        thread = threading.Thread(target=send_file, args=(int(port_new), 1024))
        thread.start()

        # sending the SYN-ACK to the client with the new port number
        MESSAGE = bytes("SYN-ACK" + str(port_new), 'utf-8')
        sock.sendto(MESSAGE, addr)

        # receiving ACK from the client
        data, addr = sock.recvfrom(1024)
        print("received :", data.decode('utf-8'))
