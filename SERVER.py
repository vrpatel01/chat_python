import socket
import threading
import pickle
from datetime import datetime

from . import PACKET




class Client_():
    def __init__(self, dct):
        self.uname = dct['uname']
        self.passwd = dct['passwd']
        self.nickName = dct['nickName']
        self.HName = dct['HName']
        self.ip = dct['ip']
        self.PubKey = dct['PubKey']
        self.PrvKey = 'no'
        self.Groupes = []
        self.Blocked = []
        self.old_mesgs = []
        self.new_mes = []

    def reg_det(self):
        return[self.Groupes, self.uname, self.passwd, self.nickName, self.PubKey, self.PrvKey]


class Group_():
    def __init__(self, name, admin, ls):
        self.name = name
        self.admin = admin
        self.members = [admin, *ls]

    def members_ls(self, uname):
        temp = self.members
        temp.remove(uname)
        return temp


class SERVER():

    def __init__(self, addrs=('127.0.0.1', 45000)):
        self.S_addrs = addrs
        self.Recevers = {}
        self.Senders = {}
        self.nickNames = {}
        self.online = []
        self.snid_ls = ['A23Sc22', 'Acce35a',
                        'Nj3HG3', '87Htr5D', 'JHG76b', 'jtF5rs']
        if not self.load_data():
            self.clients = {}
            self.nickNames = {}
            self.groupes = {}

    def start(self, S_addrs=False):
        if not S_addrs:
            S_addrs = self.S_addrs
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(addrs)
        server.listen()
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(
                target=self.handle_client, args=(conn,))
            thread.start()

    def handle_client(self, conn):
        while True:
            obj = self.rec_packet(conn)
            if obj.TYPE == 'REGISTER':
                self.register_client(conn, obj)
            elif obj.TYPE == 'LOGIN':
                self.login_client(conn, obj)
            elif obj.TYPE == 'LOGIN_REC':
                self.login_client_rec(conn, obj)
            return

    def register_client(self, conn, obj):
        print(f'Regestering {obj.uname}, {obj.data}')
        obj = self.check_client(obj)
        if obj.ack:
            self.register(conn, obj)
            print(f'Regestered {obj.uname}')
        else:
            self.send_packet(conn, obj)
            print(f'regesteration failed {obj.uname}')
        self.send_packet(conn, obj)

    def login_client_rec(self, conn, obj):
        if obj.snid_rec == self.clients[obj.uname].snid_rec:
            obj.ack = True
            self.Recevers[obj.uname] = conn
        else:
            obj.ack = False
        self.send_packet(conn, obj)
        if obj.ack:
            conn = self.Senders[obj.uname]
            self.online.append(obj.uname)
            self.lisen_forever(conn)

    def login_client(self, conn, obj):
        if obj.uname in self.clients:
            client = self.clients[obj.uname]
            if obj.passwd == client.passwd:
                print(f'{obj.uname} Loged in')
                snid_rec = self.allocate_snid()
                self.clients[obj.uname].snid_rec = snid_rec
                obj.snid_rec = snid_rec
                obj.nickName = client.nickName
                obj.ack = True
        else:
            obj.ack = False
            obj.messages = 'INVALID_USERNAME_PASSWORD'
        self.send_packet(conn, obj)
        if obj.ack:
            self.Senders[obj.uname] = conn

    def lisen_forever(self, conn):
        while True:
            obj = self.rec_packet(conn)
            if obj.TYPE == 'I_MESSAGE':
                self.froward_message(obj)
            elif obj.TYPE == 'G_MESSAGE':
                print('Groip mess here')
                self.froward_message_group(obj)
            elif obj.TYPE == 'C_GROUP':
                self.create_group(obj)
            elif obj.TYPE == 'OLD_MESSAGES' or obj.TYPE == 'NEW_MESSAGES' or obj.TYPE == 'REGESTRATION_DETAIL':
                self.send_data(obj)
            elif obj.TYPE == 'STOP':
                self.stop_client(obj)
                return
            else:
                print(f'INVALID OBJECT {obj.TYPE},{obj.data}')

    def stop_client(self, obj):
        conn_r = self.Recevers[obj.uname]
        conn_s = self.Senders[obj.uname]
        self.send_packet(conn_r, PACKET(TYPE='STOP'))
        self.close_conn(conn_r)
        self.close_conn(conn_s)
        del self.Recevers[obj.uname]
        del self.Senders[obj.uname]
        self.online.remove(obj.uname)
        print(f'{obj.uname} loged out')
        print('online clients', self.online)

    def close_conn(self, conn):
        try:
            conn.close()
        except Exception as e:
            print(e)

    def send_data(self, obj):
        client = self.clients[obj.uname]
        if obj.TYPE == 'OLD_MESSAGES':
            data = client.old_mesgs
        elif obj.TYPE == 'NEW_MESSAGES':
            if len(client.new_mes) > 0:
                data = client.new_mes
                client.old_mesgs.append(data)
                client.new_mes = []
            else:
                data = 'FALSE'
        elif obj.TYPE == 'REGESTRATION_DETAIL':
            data = client.reg_det()
        obj.data = data
        obj.ack = False if data == 'FALSE' else  True

        self.send_packet(self.Recevers[obj.uname], obj)

    def create_group(self, obj):
        if obj.group_name not in self.groupes:
            nickNames = obj.members
            unames = []
            valid_nickNames = []
            invalid_nicknames = []
            b_unames = []
            for nickName in nickNames:
                if nickName in self.nickNames:
                    client = self.nickNames[nickName]
                    if obj.uname not in client.Blocked:
                        unames.append(client.uname)
                        valid_nickNames.append(client.nickName)
                    else:
                        b_unames.append(nickName)
                else:
                    invalid_nicknames.append(nickName)
            if len(unames) > 0:
                obj.ack = True
                obj.message = 'Group Created '
                obj.nickNames = valid_nickNames
                obj.invalid_nicknames = invalid_nicknames
                obj.blocked = b_unames
                group = Group_(obj.group_name, obj.uname, unames)
                print('Group created with ', group.name,
                      group.admin, group.members,)
                self.save_data()
                self.updata_member(group)
            else:
                obj.ack = False
                obj.message = 'Goup Not Created'
                obj.invalid_nicknames = invalid_nicknames
                obj.blocked = b_unames
        else:
            obj.ack = False
            obj.message = 'Invalid Group Name'
        self.send_packet(self.Recevers[obj.uname], obj)

    def updata_member(self, group):
        unames = group.members
        obj = PACKET('GROUP_ADDED', group.admin)
        obj.uname = group.admin
        obj.group_name = group.name
        obj.message = f'YOU WERE ADDED IN GROUP {group.name} BY {self.nickNames[group.admin].nickName}'
        for uname in unames:
            self.clients[uname].Groupes.append(group.name)
            obj.recever = self.nickNames[uname].nickName
            self.froward_message(obj)

    def froward_message_group(self, obj):
        if obj.recever in self.groupes:
            group = self.groupes
            recevers = group.members_ls(obj.uname)
            print('recevers list here ',recevers)
            for recever in recevers:
                obj.recever = self.nickNames[recever].nickName
                self.froward_message(obj)

    def froward_message(self, obj):
        if not obj.data:
            obj.data = ''
        if obj.recever in self.nickNames:
            recever = self.nickNames[obj.recever]
            sender = self.clients[obj.uname]
            if recever.uname in self.online:
                self.send_packet(self.Recevers[recever.uname], obj)
                recever.old_mesgs.append(obj)
            else:
                recever.new_mes.append(obj)
            sender.old_mesgs.append(obj)
            obj.ack = True
        else:
            obj.ack = False
            obj.messages = 'INVALID_NICK_NAME'
            print(f'Invalid nickname use by {obj.sender} : {obj.recever}')
        return obj

    def register(self, conn, obj):
        dct = obj.data
        c = Client_(obj.data)
        self.clients[obj.uname] = c
        self.nickNames[obj.nickName] = c
        self.save_data()

    def check_client(self, obj):
        if obj.uname not in self.clients:
            if obj.nickName not in self.nickNames:
                if self.check_passwd(obj.passwd):
                    obj.ack = True
                    return obj
                else:
                    obj.passwd = 'WEAK_PASSWORD'
            else:
                obj.nickName = 'INVALID_NICK_NAME'
        else:
            obj.uname = 'INVALID_USER_NAME'
        obj.ack = False
        return obj

    def check_passwd(self, passwd):
        return True

    def send_packet(self, conn, obj):
        try:
            packet = pickle.dumps(obj)
            l = str(len(packet)).rjust(10, ' ').encode('utf-8')
            conn.send(l)
            conn.send(packet)
        except Exception as e:
            print(e)

    def rec_packet(self, conn):
        while True:
            l = conn.recv(10).decode('utf-8')
            if l:
                l = int(l)
                while True:
                    packet = conn.recv(l)
                    if packet:
                        obj = pickle.loads(packet)
                        return obj

    def manage_server(self):
        zzz = input('>.')
        if zzz == '0':
            self.save_data()
            exit()

    def save_data(self):
        with open('clients_info', 'wb') as f:
            pickle.dump([self.clients, self.nickNames, self.groupes], f)

    def load_data(self):
        try:
            with open('clients_info', 'rb') as f:
                self.clients, self.nickNames,  self.groupes = pickle.load(f)
                return True
        except Exception as e:
            print(e)
            return False

    def allocate_snid(self):
        return self.snid_ls[0]


if __name__ == '__main__':
    addrs = ('127.0.0.1', 45000) # your public ip
    server1 = SERVER(addrs)
    server1.start()
    server1.save_clients()
