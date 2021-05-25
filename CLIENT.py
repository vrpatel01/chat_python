import socket
import threading
import pickle
from getpass import getpass
from datetime import datetime

class PACKET:
    def __init__(self,TYPE,sender,recever='SERVER',data=None):
        self.time = datetime.now()
        self.TYPE = TYPE
        self.sender = sender
        self.recever = recever
        self.data = data


class CLIENT():

    def __init__(self):
        print('WELCOME')
        # (input('Enter SERVER IP: '),input('Enrer SERVER port: '))
#         self.S_addr = ("127.0.0.1", 45000)
        self.S_addr = (input('Enter SERVER IP: '),input('Enrer SERVER port: '))
        self.HName = socket.gethostname()
        self.ip = socket.gethostbyname(self.HName)
        self.Groupes = {}
        self.mes_history = []
        self.new_mes = []

        self.c_rec = self.connect_server()
        if not self.load_reg():
            print('WELCOME\n1. New ACCOUNT\n2. Login')
            ch = input('>> ')
            if ch == '1':
                self.regester()
                self.save_reg()
                self.login(True)
            elif ch == '2':
                self.login(False)
        else:
            self.login(True)
            self.request('REGESTRATION_DETAIL')

        thread = threading.Thread(target=self.lisen_forever)
        thread.start()

        print("1. SEND \t2. SHOW\t3. LOAD OLD\t4. LOAD NEW\t5. New Group")
        while True:
            ch = input('>')
            if ch == '1':
                self.send_msg()
            elif ch == '2':
                self.show()
            elif ch == '3':
                self.request('OLD_MESSAGES')
            elif ch == '4':
                self.request('NEW_MESSAGES')
            elif ch == '5':
                self.create_group()
            else:
                pp = input("EXIT 0 : ")
                if pp == "0":
                    self.send_stop()
                    break
        else:
            print('SOMTHINGs WRONG ')

    def create_group(self):
        members = []
        print('Enter Group info')
        name = input('Enter Name of group (unique)')
        while True:
            try:
                no_membes = int(input('number of members: '))
                break
            except Exception as e:
                print(e)
        for i in range(no_membes):
            memb = input('Menber nick name > ')
            members.append(memb)
        obj = PACKET('C_GROUP',self.nickName)
        obj.uname = self.uname
        obj.members = members
        obj.group_name = name
        self.send_packet(self.c_snd,obj)

    def lisen_forever(self):
        conn = self.c_rec
        while True:
            obj = self.rec_packet(conn)
            if obj.TYPE == 'I_MESSAGE':
                self.mes_history.append(obj)
                print(obj.data)
            elif obj.TYPE == 'G_MESSAGE':
                self.mes_history.append(obj)
                print(obj.data)
            elif obj.TYPE == 'C_GROUP':
                if obj.ack:
                    print(obj.message)
                else:
                    print(obj.message)
                    l = input('RETRY 1 >')
                    if l == '1':
                        self.create_group()
            elif obj.TYPE == 'OLD_MESSAGES':
                self.load_mesgs(obj.data)
            elif obj.TYPE == 'NEW_MESSAGES':
                if obj.ack:
                    self.load_new_mesgs(obj.data)
                else:
                    print('No new messages')
            elif obj.TYPE == 'REGESTRATION_DETAIL':
                self.load_reg(obj.data)
            elif obj.TYPE == 'GROUP_ADDED':
                self.mes_history.append(obj)
                print(obj.message)
            elif obj.TYPE == 'STOP':
                self.send_stop()
            else:
                print(f'INVALID OBJECT {obj.TYPE},{obj.data}')

    def create_reg(self):
        print('Enter the information to create account:\t')
        print('[username] (not shared with anyone alphanumeric)')
        self.uname = input('>')
        print('[password] (alphanumeric with symbols)')
        self.passwd = getpass('>')
        print('[Nick Name] what people will see you as alphanumeric ')
        self.nickName = input('>')
        self.snid = "SNID"
        self.HName = socket.gethostname()
        self.IP = socket.gethostbyname(self.HName)
        self.PubKey = "PKY"
        self.PrvKey = "KEY"

        print('Cheacking for validation ...')

    def regester(self):
        self.create_reg()
        if self.register_():
            return True
        else:
            return self.regester()

    def register_(self):
        conn = self.connect_server()
        dct = {'uname':self.uname,'passwd':self.passwd,'nickName':self.nickName,'ip':self.ip,'HName':self.HName,'PubKey':self.PubKey}
        obj = PACKET('REGISTER', self.uname, 'SERVER', dct)
        obj.uname = self.uname
        obj.nickName = self.nickName
        obj.passwd = self.passwd
        self.send_packet(conn,obj)
        obj = self.rec_packet(conn)
        conn.close()
        if obj.ack:
            print(f'Regestration Successful. uname: {obj.uname} passwd: {obj.passwd} nickName:{obj.nickName}')
            self.uname = obj.uname
            self.passwd = obj.passwd
            return True
        else:
            print(
                f"Regestration Unseccessful. uname: {obj.uname} passwd: {obj.passwd}  nickName:{obj.nickName}")
            return False

    def save_reg(self):
        with open('reg', 'wb') as f:
            pickle.dump([self.Groupes,self.uname,self.passwd,self.nickName, self.PubKey, self.PrvKey], f)

    def load_reg(self,data=False):
        if not data:
            try:
                with open('reg', 'rb') as f:
                    self.Groupes, self.uname, self.passwd, self.nickName, self.PubKey, self.PrvKey = pickle.load(
                        f)
                    self.load_mesgs()
                    return True
            except Exception as e:
                print(e)
            else:
                return False
        else:
            self.Groupes, self.uname, self.passwd, self.nickName, self.PubKey, self.PrvKey = data
            print('data got from server', self.Groupes, self.uname,
                  self.passwd, self.nickName, self.PubKey, self.PrvKey)

    def send_packet(self,conn,obj):
        print(obj.uname)
        packet = pickle.dumps(obj)
        l = str(len(packet)).rjust(10,' ').encode('utf-8')
        conn.send(l)
        conn.send(packet)

    def rec_packet(self,conn):
        while True:
            l = conn.recv(10).decode('utf-8')
            if l:
                l = int(l)
                while True:
                    packet = conn.recv(l)
                    if packet:
                        obj = pickle.loads(packet)
                        return obj

    def login(self,saved=False):
        if saved:
            uname = self.uname
            passwd = self.passwd
        else:
            uname = input("ENTER USERNAME \t>")
            passwd = getpass('ENTER PASSWORD \t>')

        if self.login_(uname,passwd):
            if self.login_rec():
                return True
        else:
            return self.login()

    def login_rec(self):
        conn = self.connect_server()
        obj = PACKET('LOGIN_REC',self.uname)
        obj.snid_rec = self.snid_rec
        obj.uname = self.uname
        self.send_packet(conn, obj)
        obj = self.rec_packet(conn)
        if obj.ack:
            self.c_rec = conn
            return True
        else:
            print('SOMTHING IS VERY WRONG\r restart the program and register  again...')
            conn.close()
            exit()
            return False

    def login_(self,uname,passwd):
        conn = self.connect_server()
        obj = PACKET('LOGIN',uname,'SERVER')
        obj.uname = uname
        obj.passwd = passwd
        self.send_packet(conn, obj)
        obj = self.rec_packet(conn)
        if obj.ack:
            print(f'Login Successful. nickname: {obj.nickName}, snid_rec {obj.snid_rec}')
            self.uname = uname
            self.passwd = passwd
            self.nickName = obj.nickName
            self.snid_rec = obj.snid_rec
            self.c_snd = conn
            return True
        else:
            print(
                f"Login Unseccessful. {obj.messages}")
            conn.close()
            return False

    def send_msg(self):
        ch = input('1. Indevidual\t2. Group')
        if ch == '1':
            to_nickName = input("Send to: ")
            data = input("mes: ")
            obj = PACKET('I_MESSAGE', self.nickName, to_nickName, data)
        else:
            to = input("Send to: ")
            data = input("mes: ")
            obj = PACKET('G_MESSAGE', self.nickName, to, data)
        obj.uname = self.uname
        obj.nickName = self.nickName
        self.send_packet(self.c_snd, obj)

    def send_stop(self):
        self.save_mesgs()
        try:
            obj = PACKET('STOP',self.uname,'SERVER')
            obj.uname = self.uname
            self.send_packet(self.c_snd,obj)
            self.c_snd.close()
            print(f'[connection closed] sender')
        except Exception as e:
            print(e)
        exit()

    def load_mesgs(self,data=False):
        if not data:
            try:
                with open('messages', 'rb') as f:
                    self.mes_history = pickle.load(f)
                    return True
            except Exception as e:
                print(e)
            else:
                return False
        else:
            self.mes_history = data

    def load_new_mesgs(self,data):
        print('daata of neww messages',data)
        self.new_mes = data
        print(f'{len(self.new_mes)} new mwssages..')
        self.show(self.new_mes)
        self.mes_history.append(self.new_mes)
        self.new_mes=[]

    def save_mesgs(self):
        with open('messages', 'wb') as f:
            pickle.dump(self.mes_history, f)
        
    def request(self,TYPE):
        print('requesting details')
        obj = PACKET(TYPE,self.uname,'SERVER')
        obj.uname = self.uname
        obj.nickName = self.nickName
        self.send_packet(self.c_snd,obj)

    def show(self,ls=False):
        lst = ls if ls else self.mes_history
        senders = []
        for mes in lst:
            senders.append(mes.sender)
        senders = set(senders)
        print(senders)
        for mes in lst:
            sender = mes.sender
            s= sender.ljust(10," ")
            s+='> ' + mes.data
            s = s.ljust(64, ' ') + '\t' + mes.time.strftime("%H:%M:%S")
            print(s)

    def connect_server(self, addrs=False):
        if not addrs:
            addrs = self.S_addr
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(addrs)
        return client

if __name__ == '__main__':
    me = CLIENT()
