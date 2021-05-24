"""
Group Project: Internet Chat Relay Application
By Chinmay Tawde and Akansha Jain
"""

import tkinter, threading
from cryptography.fernet import Fernet
from socket import *
import sys


class ChatWindow:

    def __init__(self):

        #Initialize Tkinter
        self._master = tkinter.Tk()
        self._master.title("Group Assignment: Internet Chat Application")

        self._master.resizable(0, 0)  # Disables window maximize

        self._main_frame = tkinter.Frame(self._master)
        self._main_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tkinter.W + tkinter.E, columnspan=6)
        self._main_frame.columnconfigure(0, weight=1)

        self._ip_field_label = tkinter.Label(master=self._main_frame, text="IP:")
        self._ip_field_label.grid(row=0, column=0, padx=5, pady=3, sticky=tkinter.W)

        self._ip_var = tkinter.StringVar()
        self._ip_input_field = tkinter.Entry(master=self._main_frame, textvariable=self._ip_var, width=35)
        self._ip_input_field.grid(row=0, column=1, padx=5, pady=5, sticky=tkinter.W)

        self._port_label = tkinter.Label(master=self._main_frame, text="Port:")
        self._port_label.grid(row=0, column=2, padx=5, pady=5)

        self._port_var = tkinter.StringVar()
        self._port_input_field = tkinter.Entry(master=self._main_frame, textvariable=self._port_var, width=15)
        self._port_input_field.grid(row=0, column=3, padx=6, pady=5)

        self._connect_btn = tkinter.Button(master=self._main_frame, command=self.connect, text="Connect")
        self._connect_btn.grid(row=0, column=4, padx=5, pady=5, sticky=tkinter.W)

        self._nickname_frame = tkinter.Frame(self._master)
        self._nickname_frame.grid(row=1, column=0, padx=5, pady=5, sticky=tkinter.W, columnspan=6)
        self._nickname_frame.columnconfigure(0, weight=1)

        self._name_var = tkinter.StringVar()
        self._nickname_input_field = tkinter.Entry(master=self._nickname_frame, textvariable=self._name_var, width=25)
        self._nickname_input_field.grid(row=0, column=5, padx=15, pady=5, sticky=tkinter.W)
        self._nickname_input_field.bind('<Return>', lambda x: self.change_name())

        self._confirm_nickname_btn = tkinter.Button(master=self._nickname_frame, command=self.change_name, text="Change Name")
        self._confirm_nickname_btn.grid(row=0, column=6, padx=5, pady=5)

        self._room_frame = tkinter.Frame(self._master)
        self._room_frame.grid(row=2, column=0, padx=5, pady=5, sticky=tkinter.W, columnspan=6)
        self._room_frame.columnconfigure(0, weight=1)

        self._defaultRoom_btn = tkinter.Button(master=self._room_frame, command=self.move_default_room, text="Default Room")
        self._defaultRoom_btn.grid(row=0, column=2, padx=5, pady=5)

        self._add_room_btn = tkinter.Button(master=self._room_frame, command=lambda: self.add_room(True), text="Add Room")
        self._add_room_btn.grid(row=0, column=1, padx=5, pady=5)

        chat_frame = tkinter.Frame(self._master)
        chat_frame.grid(row=3, column=0, pady=5, sticky=tkinter.W + tkinter.E, columnspan=6)
        chat_frame.columnconfigure(0, weight=1)

        self._listbox = tkinter.Listbox(chat_frame, width=50, height=20, font="RobotoSlabLight")
        self._listbox.grid(row=0, column=0, padx=5, pady=5)

        self._send_frame = tkinter.Frame(self._master)
        self._send_frame.grid(row=4, column=0, padx=5, pady=5, sticky=tkinter.W + tkinter.E, columnspan=6)
        self._send_frame.columnconfigure(0, weight=1)

        self._send_btn = tkinter.Button(master=self._send_frame, command=self._message, text="Send")
        self._send_btn.grid(row=0, column=0, padx=5, pady=5, sticky=tkinter.W)

        self._list_btn = tkinter.Button(master=self._send_frame, command=self.get_member_list, text="List Members")
        self._list_btn.grid(row=0, column=1, padx=5, pady=5, sticky=tkinter.W)

        self._send_var = tkinter.StringVar()
        self._message_input_field = tkinter.Entry(master=self._send_frame, textvariable=self._send_var, width=55)
        self._message_input_field.grid(row=0, column=2, padx=5, pady=5, sticky=tkinter.W)
        self._message_input_field.bind('<Return>', lambda x: self._message())

        self._error_frame = tkinter.Frame(self._master, relief=tkinter.RIDGE, borderwidth=8)
        self._error_frame.grid(row=5, column=0, sticky=tkinter.W + tkinter.E, columnspan=6)
        self._error_frame.columnconfigure(0, weight=1)

        self._info_label = tkinter.Label(master=self._error_frame, text="No errors")
        self._info_label.grid(row=0, column=0, padx=5, pady=5, sticky=tkinter.W)

        def close():
            try:
                self._serverSocket.close()
                self._serverSocket = None
                self._name = None
                self._connected = False
            except:
                pass

        self._serverSocket = None
        self._name = None
        self._connected = False
        self._roomCount = 1
        self._currentRoom = 0

        self._master.protocol("WM_DELETE_WINDOW", close())

        # Places the window on center
        self._master.eval('tk::PlaceWindow . center')
        self._master.mainloop()

    def check_server_response(self):
        while self._connected:
            if not self._serverSocket == None:
                try:
                    response = f.decrypt(self._serverSocket.recv(1024)).decode("UTF-8")
                    self._parse_packet(response)
                    # print(response)
                except ConnectionAbortedError:
                    pass
                except:
                    print("Unexpected error:", sys.exc_info()[0])
                    raise

    def _parse_packet(self, p: str):
        # Packet Types
        # Message     -> MessageHeader;MessageContent
        # Room Details -> RoomDetailsHeader;RoomNum      Total number of rooms visible on screen for all clients
        # Room Change -> RoomHeader;RoomNum
        # Create Room -> CreateHeader;RoomNum
        # List Room Members -> ListMembersHeader;RoomNum
        # Disconnect  -> DisconnectHeader;
        # Error -> ErrorHeader;ErrorMessage
        # Update -> UpdateHeader;UpdateMessage
        parsed = p.split(';')
        command = parsed[0]
        if command == '_message':
            self._update_messages(';'.join(parsed[1:]).rstrip())
        elif command == 'room_details':
            self._showExistingRooms(int(parsed[1]))
        elif command == 'room':
            self.set_room(int(parsed[1]))
        elif command == 'create_room':
            self._roomCount = int(parsed[1])
            self.add_room(False)
        elif command == 'list_members':
            members_list = "<Participants>: [" + parsed[1] + "]"
            self._update_messages(members_list)
        elif command == 'disconnect':
            self._serverSocket.close()
            self.cleanUpGui()
            self._serverSocket = None
            self._name = None
            self._connected = False
            self._connect_btn['text'] = "Connect"
            self.set_infolabel_messages("Disconnected from server")
        elif command == '1':
            self._name = parsed[1]
        elif command == 'error':
            self.set_infolabel_messages(';'.join(parsed[1:]).rstrip())
        elif command == 'update':
            self._update_messages(';'.join(parsed[1:]).rstrip())
        elif command == '':
            self.activate_others(0)
            self._serverSocket.close()
            self._serverSocket = None
            self._name = None
            self._connected = False
            self._connect_btn['text'] = "Connect"
            self.set_infolabel_messages("Disconnected from server")

    def _showExistingRooms(self, m):
        if (m >= 1):
            self.create_room_1()
        if (m >= 2):
            self.create_room_2()
        if (m >= 3):
            self.create_room_3()
        if (m >= 4):
            self.create_room_4()

            # if this condition also satifies disable the add button
            self._add_room_btn.config(state=tkinter.DISABLED)

        # assign current room number values to m
        if (m != 0):
            self._roomCount = m

    def change_name(self):
        new_name = self._name_var.get()
        self._name = new_name
        if len(new_name) <= 10:
            self._send_packet(str('name;' + new_name))
        else:
            self.set_infolabel_messages("Name must be fewer than 10 letters")

    def _update_messages(self, m):
        if len(m) == 0 or not self._connected:
            return
        self._listbox.insert('end', m)

    def _message(self):
        m = self._send_var.get().rstrip()
        if len(m) == 0:
            return
        self._send_var.set('')
        self._listbox.insert('end', self._name + ': ' + m)
        self._send_packet(str('_message;' + m))

    def set_room(self, room):
        if type(room) == int:
            self._currentRoom = room

    def get_member_list(self):
        room = self._currentRoom
        m = "list_members;" + str(room)
        self._send_packet(m)

    def _send_packet(self, p):
        if self._connected:
            msg = p.encode("UTF-8")
            msg = f.encrypt(msg)
            print(msg)
            self._serverSocket.send(msg)
            self.set_infolabel_messages("Request Sent")
        else:
            self.set_infolabel_messages("Could not send packet, not connected to server.")

    def activate_others(self, roomNum):
        i = 0
        _room1_button = getattr(self, "_room1_button", -1)
        _room2_button = getattr(self, "_room2_button", -1)
        _room3_button = getattr(self, "_room3_button", -1)
        _room4_button = getattr(self, "_room4_button", -1)
        for f in [self._defaultRoom_btn, _room1_button, _room2_button, _room3_button, _room4_button]:
            if f != -1:
                f = f.config
                if not i == roomNum:
                    f(state=tkinter.NORMAL)
                i += 1

    def create_room_1(self):
        self._room1_button = tkinter.Button(master=self._room_frame, command=self.move_room1, text="Room 1")
        self._room1_button.grid(row=0, column=3, padx=5, pady=5)
        self._room1_button.grid()

    def create_room_2(self):
        self._room2_button = tkinter.Button(master=self._room_frame, command=self.move_room2, text="Room 2")
        self._room2_button.grid(row=0, column=4, padx=5, pady=5)
        self._room2_button.grid()

    def create_room_3(self):
        self._room3_button = tkinter.Button(master=self._room_frame, command=self.move_room3, text="Room 3")
        self._room3_button.grid(row=0, column=5, padx=5, pady=5)
        self._room3_button.grid()

    def create_room_4(self):
        self._room4_button = tkinter.Button(master=self._room_frame, command=self.move_room4, text="Room 4")
        self._room4_button.grid(row=0, column=6, padx=5, pady=5)
        self._room4_button.grid()

    def add_room(self, notify):
        if (self._roomCount <= 4):
            room_count = self._roomCount
            if room_count == 1:
                self.create_room_1()
                if notify: self._send_packet("create_room;1")
            elif room_count == 2:
                self.create_room_2()
                if notify: self._send_packet("create_room;2")
            elif room_count == 3:
                self.create_room_3()
                if notify: self._send_packet("create_room;3")
            elif room_count == 4:
                self.create_room_4()
                if notify: self._send_packet("create_room;4")

            self._roomCount = room_count + 1
        else:
            self._add_room_btn.config(state=tkinter.DISABLED)

    def move_default_room(self):
        self._listbox.delete(0, tkinter.END)
        self.activate_others(0)
        self._defaultRoom_btn.config(state=tkinter.DISABLED)
        self._send_packet("room;0")

    def move_room1(self):
        self._listbox.delete(0, tkinter.END)
        self.activate_others(1)
        self._room1_button.config(state=tkinter.DISABLED)
        self._send_packet("room;1")

    def move_room2(self):
        self._listbox.delete(0, tkinter.END)
        self.activate_others(2)
        self._room2_button.config(state=tkinter.DISABLED)
        self._send_packet("room;2")

    def move_room3(self):
        self._listbox.delete(0, tkinter.END)
        self.activate_others(3)
        self._room3_button.config(state=tkinter.DISABLED)
        self._send_packet("room;3")

    def move_room4(self):
        self._listbox.delete(0, tkinter.END)
        self.activate_others(4)
        self._room4_button.config(state=tkinter.DISABLED)
        self._send_packet("room;4")

    def reset_error(self):
        self._info_label.config(text="No errors")

    def set_infolabel_messages(self, e):
        self._info_label.config(text=e)

    def connect(self):
        if self._connect_btn['text'] == "Connect":
            serverIP = self._ip_var.get()
            serverPort = self._port_var.get()  # ports 0-1024 are reserved
            self._serverSocket = socket(AF_INET, SOCK_STREAM)  # SOCK_STREAM stands for TCP protocol
            try:
                self._serverSocket.connect((serverIP, int(serverPort)))
                self._connected = True
                self.set_infolabel_messages("Connected!")
                self._connect_btn['text'] = "Disconnect"
                self._defaultRoom_btn.config(state=tkinter.DISABLED)
                listening_thread = threading.Thread(target=self.check_server_response)
                listening_thread.start()
            except:
                self.set_infolabel_messages("Could Not Connect")
        elif self._connect_btn['text'] == "Disconnect":
            try:
                self._send_packet('disconnect;{}'.format(self._name))
                self._serverSocket.close()
                self._connected = False
                self._connect_btn['text'] = "Connect"
                self.cleanUpGui()
                self._listbox.delete(0, tkinter.END)
            except:
                self.set_infolabel_messages("Failed to disconnect")

    def cleanUpGui(self):
        # Make default room active again
        self._defaultRoom_btn.config(state=tkinter.NORMAL)

        # Delete rest of the rooms
        if hasattr(self, "_room1_button"):
            self._room1_button.grid_forget()
            del self._room1_button
        if hasattr(self, "_room2_button"):
            self._room2_button.grid_forget()
            del self._room2_button
        if hasattr(self, "_room3_button"):
            self._room3_button.grid_forget()
            del self._room3_button
        if hasattr(self, "_room4_button"):
            self._room4_button.grid_forget()
            del self._room4_button


if __name__ == "__main__":
    key = open("secret.key", "rb").read()
    global f
    f = Fernet(key)
    window = ChatWindow()
