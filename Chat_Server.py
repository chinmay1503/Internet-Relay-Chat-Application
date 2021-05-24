"""
Group Project: Internet Chat Relay Application
By Chinmay Tawde and Akansha Jain
"""

from socket import *
from cryptography.fernet import Fernet
import threading, atexit, time

class Client():
    
    def __init__(self, name, conn, addr, room):
        self._clientName = name
        self._clientSocket = conn
        self._clientAddress = addr
        self._currentRoom = room
        self._currentRoom.add_client(self)
        self._currentRoom.send_room_status(self)
        self._exists = True
        
        receiving_thread = threading.Thread(target = self._receive_from_client)
        receiving_thread.start()
        
    def set_room(self, room):
        if not self._currentRoom == None:
            self._currentRoom.remove_client(self)
            
        if type(room) == int:
                room = eval("eval('self._currentRoom.get_server().ROOM{}')".format(room))
        self._currentRoom = room
        self._currentRoom.add_client(self)
        
    def get_name(self):
        return self._clientName

    def send_to_client(self, data: str):
        try:
            #Encode message first
            msg = data.encode("UTF-8")
            #then encrypt before sending
            msg = f.encrypt(msg)
            print(msg)
            self._clientSocket.send(msg)
        except ConnectionResetError:
            # If error occurs while sending message to client disconnect the client
            self._exists = False
            self._currentRoom.remove_client(self)
            self._currentRoom.get_server().remove_client(self)

    def _receive_from_client(self):
        while self._exists:
            try:
                packet = f.decrypt(self._clientSocket.recv(1024)).decode("UTF-8")
                self._parse_packet(packet)
            except ConnectionResetError:
                # If error occurs while receiving message from client disconnect the client
                self._exists = False
                self._currentRoom.remove_client(self)
                self._currentRoom.get_server().remove_client(self)

    def _parse_packet(self, p: str):
        # Packet Types
        # Message     -> MessageHeader;MessageContent
        # Private Message -> MessageHeader;PrivateMessageToken;TargetName;MessageContent
        # Room Details -> RoomDetailsHeader;RoomNum      Total number of rooms visible on screen for all clients
        # Room Change -> RoomHeader;RoomNum
        # Create Room -> CreateHeader;RoomNum
        # List Room Members -> ListMembersHeader;RoomNum
        # Change Nickname -> nameHeader;NickName
        # Disconnect  -> DisconnectHeader;
        # Error -> ErrorHeader;ErrorMessage
        # Update -> UpdateHeader;UpdateMessage
        parsed = p.split(';')
        command = parsed[0]
        if command == '_message':
            if parsed.__len__() > 2:
                if len(parsed) == 4:
                    if (parsed[1] == "pvt_msg"):
                        targetClientName = parsed[2]
                        room = self._currentRoom
                        found_target_in_room = False
                        for room_member in room._occupants:
                            if room_member.get_name() == targetClientName:
                                found_target_in_room = True
                                msg = "_message;[" + parsed[1] + "]" + self._clientName + ': ' + parsed[3]
                                room_member.send_to_client(msg)

                        if not found_target_in_room:
                            err_msg = "error;Specified Client Not Found in Room"
                            self.send_to_client(err_msg)

                else:
                    err_msg = "error;Invalid message format, for pvt message Type ""pvt_msg;ClientName;SecretMessage"""
                    self.send_to_client(err_msg)
            else :
                self._currentRoom.send_message(self._clientName, ';'.join(parsed[1:]).rstrip())
        elif command == 'create_room':
            self.notify_room_creation(self, p)
        elif command == 'room':
            self.set_room(int(parsed[1]))
        elif command == 'list_members':
            members_list = "list_members;" + self._currentRoom._get_occupants()
            self.send_to_client(members_list)
        elif command == 'disconnect':
            if self._exists:
                self._exists = False
                self._clientSocket.close()
                self._currentRoom.remove_client(self)
                self._currentRoom.get_server().remove_client(self)
        elif command == 'name':
            old_name = self._clientName
            self._clientName = ';'.join(parsed[1:]).rstrip()
            if self._currentRoom.get_server().nickNames.count(self._clientName) > 0:
                err_msg = "error;The Nickname is already taken, Enter a unique nickname"
                self.send_to_client(err_msg)
            else:
                self._currentRoom.get_server().nickNames.remove(old_name)
                self._currentRoom.get_server().nickNames.append(self._clientName)
                self._currentRoom.send_update("update;--{} has changed their name to {}--".format(old_name, self._clientName))
        elif command == "update":
            self._currentRoom.send_update(';'.join(parsed[1:]).rstrip())
        elif command == '':
            if self._exists:
                self._exists = False
                self._clientSocket.close()
                self._currentRoom.remove_client(self)
                self._currentRoom.get_server().remove_client(self)

    def _send_confirmation(self, c):
        self.send_to_client(c)

    def notify_room_creation(self, client, message):
        current_room = client._currentRoom
        client_server = current_room._server
        client = self._clientName
        client_server._roomsOnScreen += 1
        for rooms in (client_server.rooms):
            for room_member in rooms._occupants:
                if not room_member.get_name() == client:
                    room_member.send_to_client(message)


class Room:
    
    def __init__(self, name, server):
        self._roomName = name
        self._server = server
        self._occupants = []

    def get_server(self):
        return self._server   

    def get_name(self):
        return self._roomName    

    def add_client(self, new_client):
        self._occupants.append(new_client)
        msg = "update;" + new_client._clientName + " has joined the room"
        time.sleep(1)
        self.send_update(msg)

    def send_room_status(self, new_client):
        msg = "room_details;" + str(new_client._currentRoom._server._roomsOnScreen)
        time.sleep(1)
        new_client.send_to_client(msg)

    def remove_client(self, client):
        if client in self._occupants:
            self._occupants.remove(client)
        msg = "update;" + client._clientName + " has disconnected from the room"
        self.send_update(msg)

    def send_message(self, sender, _message):
        packet = "_message;" + sender + ': ' + _message
        for room_member in self._occupants:
            if not room_member.get_name() == sender:
                room_member.send_to_client(packet)

    def _get_occupants(self):
        if not self._occupants:
            print("Empty")
            return
        member_list_string = ''
        for room_member in self._occupants:
            member_list_string += room_member.get_name() + ', '
        return member_list_string[0:-2]
        
    def send_update(self, u):
        for room_member in self._occupants:
            room_member.send_to_client(u)


class MultiChatServer:
    
    def __init__(self, maxClients, serverPort):
        self._maxClients = maxClients
        self._clients = []
        self._roomsOnScreen = 0
        self.rooms = []
        self.nickNames = []

        self.ROOM0 = Room('0', self)
        self.ROOM1 = Room('1', self)
        self.ROOM2 = Room('2', self)
        self.ROOM3 = Room('3', self)
        self.ROOM4 = Room('4', self)

        self._serverSocket = socket(AF_INET, SOCK_STREAM)
        self._serverPort = serverPort

    def add_all_rooms_to_array(self):
        self.rooms.append(self.ROOM0)
        self.rooms.append(self.ROOM1)
        self.rooms.append(self.ROOM2)
        self.rooms.append(self.ROOM3)
        self.rooms.append(self.ROOM4)

    def print_room_clients(self):
        for each_room in [self.ROOM0, self.ROOM1, self.ROOM2, self.ROOM3, self.ROOM4]:
            print(each_room.get_name(), each_room._occupants)
        
    def start(self):
        self._serverSocket.bind(('',self._serverPort))
        self._serverSocket.listen(16)
        print("Server is listening on port", self._serverPort)
        listening_thread = threading.Thread(target = self._accept_connections)
        listening_thread.start()

    def end(self):
        try:
            self._serverSocket.close()
        except:
            pass

    def remove_client(self, client):
        if client in self._clients:
            if self.nickNames.count(client.get_name()) > 0: self.nickNames.remove(client.get_name())
            self._clients.remove(client)
        del client

    def _is_server_full(self):
        return self._maxClients == len(self._clients)

    def _accept_connections(self):
        while True:
            if not self._is_server_full():
                connection_socket, addr = self._serverSocket.accept()
                new_client = Client("Client{}".format(len(self._clients)+1), connection_socket, addr, self.ROOM0)
                self._clients.append(new_client)
                self.nickNames.append(new_client.get_name())
                time.sleep(2)
                if len(self._clients) > 0: self._clients[-1].send_to_client('1;{}'.format(new_client.get_name()))
            else:
                connection_socket, addr = self._serverSocket.accept()
                err_msg = "error;Server is full".encode("UTF-8")
                err_msg = f.encrypt(err_msg)
                connection_socket.send(err_msg)
                connection_socket.close()

    def load_key(self):
        return open("secret.key", "rb").read()


if __name__ == "__main__":
    maxClients = 10
    serverPort = 5000
    server = MultiChatServer(maxClients, serverPort)
    server.add_all_rooms_to_array()
    key = server.load_key()
    global f
    f = Fernet(key)
    server.start()
    atexit.register(server.end)
