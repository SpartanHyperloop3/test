#run with tcp_client_multithread

import socket
import threading

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverRunning = True
ip = str(socket.gethostbyname(socket.gethostname()))
port = 8080

clients = {}

s.bind((ip, port))
s.listen()
print('Server Ready...')
print('Ip Address of the Server::%s' % ip)


def handleClient(client, pi_name):
    clientConnected = True
    keys = clients.keys()
    help = 'List of commands\n1::**connectedpi=>gives you the list of the pis currently connected\n2::**quit=>To end your session\n3::**broadcast=>To broadcast your message to each and every pi currently online\n4::Add the name of the pi at the end of your message preceded by @ to send it to thaat particular pi'

    while clientConnected:
        try:
            msg = client.recv(1024).decode('ascii')
            response = 'Number of Pis connected\n'
            found = False
            if '**connectedpi' in msg:
                clientNo = 0
                for name in keys:
                    clientNo += 1
                    response = response + str(clientNo) + '::' + name + '\n'
                client.send(response.encode('ascii'))
            elif '**help' in msg:
                client.send(help.encode('ascii'))
            elif '**broadcast' in msg:
                msg = msg.replace('**broadcast', '')
                for k, v in clients.items():
                    v.send(msg.encode('ascii'))
            elif '**quit' in msg:
                response = 'Stopping Session and exiting...'
                client.send(response.encode('ascii'))
                clients.pop(pi_name)
                print(pi_name + ' has been disconnected')
                clientConnected = False
            else:
                for name in keys:
                    if ('@' + name) in msg:
                        msg = msg.replace('@' + name, '')
                        clients.get(name).send(msg.encode('ascii'))
                        found = True
                if (not found):
                    client.send('Trying to send message to invalid pi.'.encode('ascii'))
        except:
            clients.pop(pi_name)
            print(pi_name + ' has been logged out')
            clientConnected = False


while serverRunning:
    client, address = s.accept()
    pi_name = client.recv(1024).decode('ascii')
    print('%s connected to the server' % str(pi_name))
    client.send('Hello, world! Type **help to know all the commands'.encode('ascii'))

    if (client not in clients):
        clients[pi_name] = client
        threading.Thread(target=handleClient, args=(client, pi_name,)).start()