from array import array
from tkinter import *
import hashlib
import re
from typing import List
import websockets
import threading
import asyncio
import time

class App(Tk):
    class Block:
        index = 0
        data = ""
        timestamp = 0
        hash = ""
        previousHash = ""
        diff = 5
        nonce = 0

    chain = []
    send_sockets = []

    def __init__(self):
        super().__init__()
        self.listen_port = StringVar(value="3000")
        self.join_address = StringVar(value="localhost:3000")

        frame1 = Frame(self)
        frame2 = Frame(self)
        frame3 = Frame(self)

        frame1.pack(side=TOP)
        frame2.pack(side=TOP)
        frame3.pack(side=TOP)

    
        Label(frame1, text="Listen:", font=("Arial", 15), padx=5,pady=5).pack(side=LEFT)
        Entry(frame1, width=50, textvariable=self.listen_port).pack(side=LEFT)
        Button(frame1, text="Listen", command=self.log100, font=("Arial", 15), padx=5, pady=5).pack(side=LEFT)
        Label(frame1, text="Listening to: ", font=("Arial", 15), padx=5, pady=5).pack(side=LEFT)


        Label(frame2, text="Add:", font=("Arial", 15), padx=5, pady=5).pack(side=LEFT)
        Entry(frame2, width=50, textvariable=self.join_address).pack(side=LEFT)
        Button(frame2, text="Submit", command=lambda: self.log.insert(END, "new thingy"), font=("Arial", 15), padx=5, pady=5).pack(side=LEFT)  

        self.log = Listbox(frame3, width=100, height=30, background="LightGray", selectmode=SINGLE)
        self.log.pack(side=BOTTOM)

    def logText(self, thing):
        self.log.insert(END, thing)
        self.log.see(END)

    def log100(self):
        for x in range(100):
            time.sleep(0.5)
            self.logText(x)

    def hello(self):
        print("hello world")

    def mine(self):
        new = self.Block()
        while(True):
            new.hash = hashlib.sha256(new.index + new.timestamp + new.data + new.previousHash + new.diff + new.nonce)
            if( re.search('(?!0)', new.hash ).start() > new.diff - 1 ):
                return new
            else:
                new.nonce += 1

    async def reciver(self, port):
        try:
            async with websockets.serve(self.download, "localhost", port, max_size=None, ping_interval=None):
                await asyncio.Future()
        except Exception as e:
            print("Guess not %s" % e)


    def startserver(self):
        try:
            server = threading.Thread(target=asyncio.run, args=(self.reciver(int(self.port.get())),))
            server.daemon = True
            server.start()
            self.statusLabel.config(text="Server running on port: %d" % int(self.port.get()))

        except Exception as e:
            self.statusLabel.config(text="failed to start server")

    async def sender(self, address):
        async with websockets.connect("ws://%s" % address, max_size=None) as websocket:
            self.send_sockets.append(websocket)

    def connect(self):
        try:
            server = threading.Thread(target=asyncio.run, args=(self.sender("address"),))
            server.daemon = True
            server.start()
        except Exception as e:
            self.log("failed to connect")


if __name__ == "__main__" :
    app = App()
    app.mainloop()