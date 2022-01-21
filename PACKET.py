from datetime import datetime

class PACKET:
    def __init__(self,TYPE,sender,recever='SERVER',data=None):
        self.time = datetime.now()
        self.TYPE = TYPE
        self.sender = sender
        self.recever = recever
        self.data = data
