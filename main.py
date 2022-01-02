from array import ArrayType, array
from tkinter import *
import hashlib
import pickle
from typing import List
import websockets
import threading
import asyncio
import time

class Block:
    index = 0
    data = ""
    timestamp = 0
    hash = ""
    prev_hash = ""
    diff = 2
    nonce = 0
    def __init__(self, index : int, data : str, timestamp : float, prev_hash : str, diff : int):
        self.index = index
        self.data = data
        self.timestamp = timestamp
        self.prev_hash = prev_hash
        self.diff = diff

    def toString(self):
        return f"""
        Index: {self.index}
        Data: {self.data}
        Timestamp: {str(self.timestamp)}
        hash: {str(self.hash)}
        prevHash: {str(self.prev_hash)}
        diff: {self.diff}
        nonce: {self.nonce}
        """
        
    def toStringNN(self):
        return f"""Index: {self.index}, hash: {str(self.hash)}, prevHash: {str(self.prev_hash)}, diff: {self.diff}, nonce: {self.nonce}"""

class App(Tk):           

    chain = []
    send_sockets = []
    diff : int = 2
    dif_adjust_interval : int = 2
    block_gen_interval : float = 1.5 # sekunde
    mine_block_count : int = 100

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
        Button(frame1, text="Listen", command=self.startserver, font=("Arial", 15), padx=5, pady=5).pack(side=LEFT)
        self.statusLabel = Label(frame1, text="", font=("Arial", 15), padx=5, pady=5)
        self.statusLabel.pack(side=LEFT)


        Label(frame2, text="Add:", font=("Arial", 15), padx=5, pady=5).pack(side=LEFT)
        Entry(frame2, width=50, textvariable=self.join_address).pack(side=LEFT)
        Button(frame2, text="Submit", command=self.connect, font=("Arial", 15), padx=5, pady=5).pack(side=LEFT)  

        self.log = Listbox(frame3, width=200, height=30, background="LightGray", selectmode=SINGLE)
        self.log.pack(side=BOTTOM)

        Button(self, text="Start mining", command=self.start_mining_thread, font=("Arial", 15), padx=5, pady=5).pack()  

    def logText(self, thing : str):
        self.log.insert(END, thing)
        self.log.see(END)

    def mineBlock(self, newBlock : Block):
        count : int = 0
        while(1):
            newBlock.hash = self.hash(newBlock)
            count += 1
            if(count%10000==0):
                print(f"{count} hash is {newBlock.hash}")
            if(str(newBlock.hash).startswith(newBlock.diff * '0')):
                return newBlock
            else:
                newBlock.nonce += 1

    async def emit(self, msg):
        for socket in self.send_sockets:
            try:
                await socket.send(pickle.dumps(msg))
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"probs closed smthing")
                self.send_sockets.remove(socket)

    async def getUpdates(self, websocket):
        print("got connection")
        try:
            async for message in websocket:
                new_chain = pickle.loads(message)
                print("recived chain")
                if self.validate_chain(new_chain):
                    print(f"chain valid, diffs are new {self.calculate_chain_diff(new_chain)}, and current {self.calculate_chain_diff(self.chain)}")
                    if (self.calculate_chain_diff(new_chain) > self.calculate_chain_diff(self.chain)):
                        self.logText("updated to new chain")
                        self.printChain(new_chain)
                        self.chain = new_chain
                        self.diff = new_chain[-1].diff
                        self.logText(f"new diff is now {self.diff}")
        except Exception as e:
            print(f"stopped recieving data from one app because {e}")

    async def reciver(self, port):
        try:
            async with websockets.serve(self.getUpdates, "localhost", port, max_size=None, ping_interval=None):
                await asyncio.Future()
        except Exception as e:
            print(f"Guess not ${e}")

    def startserver(self):
        try:
            server = threading.Thread(target=asyncio.run, args=(self.reciver(int(self.listen_port.get())),))
            server.daemon = True
            server.start()
            self.statusLabel.config(text="Listening to: %d" % int(self.listen_port.get()))

        except Exception as e:
            self.logText("failed to start server")
            print(e)

    async def addSender(self, address):
        try:
            self.logText(f"connection to ws://{address}")
            async with websockets.connect(f"ws://{address}", max_size=None) as websocket:
                self.send_sockets.append(websocket)
                await asyncio.Future()
        except Exception as e:
            print("E;")
            print(e)

    def connect(self):
        try:
            server = threading.Thread(target=asyncio.run, args=(self.addSender(self.join_address.get()),))
            server.daemon = True
            server.start()
        except Exception as e:
            self.logText("failed to connect")

    def startMining(self):
        for x in range(1,self.mine_block_count):
            print(f"mining block {x}")
            if len(self.chain)==0:
                prev_hash : str = "0"
            else :
                prev_hash : str = self.chain[-1].hash
            block = Block(len(self.chain),"Block data things", time.time(), prev_hash, self.diff)
            block = self.mineBlock(block)
            if(self.can_add_block(block)):
                self.chain.append(block)
                self.logText(block.toStringNN())
                if(block.index%self.dif_adjust_interval==0):
                    self.diff = self.adjust_diff()
                    self.logText(f"Diff adjusted to {self.diff}")

    def startUpdates(self):
        while 1:
            time.sleep(5)
            asyncio.run(self.emit(self.chain))

    def start_mining_thread(self):
        try:
            miner = threading.Thread(target=self.startMining)
            miner.daemon = True
            miner.start()

            updater = threading.Thread(target=self.startUpdates)
            updater.daemon = True
            updater.start()
        except Exception as e:
            self.logText("failed to connect")
            
    def can_add_block(self, block : Block):
        if(len(self.chain)==0 & block.index==0):
            return True

        prev_block : Block = self.chain[-1]
        if(prev_block.hash != block.prev_hash):
            return False
        if(prev_block.index != block.index - 1):
            return False
        
        return True

    def adjust_diff(self):
        previousAdjustmentBlock = self.chain[len(self.chain) - self.dif_adjust_interval]
        timeExpected = self.block_gen_interval * self.dif_adjust_interval
        timeTaken = self.chain[-1].timestamp - previousAdjustmentBlock.timestamp

        if ( timeTaken < (timeExpected / 2) ):
            return previousAdjustmentBlock.diff + 1 # povečanje težavnosti
        elif  ( timeTaken > (timeExpected * 2) ):
            return previousAdjustmentBlock.diff - 1 # pomanjšanje težavnosti
        else :
            return previousAdjustmentBlock.diff # težavnost ostane enaka

    def calculate_chain_diff(self, chain):
        diff = 0
        for x in chain:
            diff += pow(2, x.diff)
        return diff

    def printChain(self, chain):
        for x in chain:
            self.logText(x.toStringNN())

    def validate_chain(self, chain : List):
        # index
        # hash
        # prev Hash
        # blok je ustrezen, če je njegova časovna značka največ 1 minuto večja od našega trenutnega časa
        # blok v verigi je ustrezen če je njegova časovna značka največ 1 minuto manjša od časovne značke prejšnjega bloka
        for x in range(1,len(chain)):
            if(chain[x].index != (chain[x-1].index + 1)):
                print("invalid index")
                return False

            if(chain[x].hash != self.hash(chain[x])):
                print("invalid hash")
                return False

            if(chain[x].prev_hash != chain[x-1].hash):
                print("invalid prevhash")
                return False

            if((chain[x].timestamp - time.time() ) > 60 ):
                print("invalid timestamp1")
                return False

            if((chain[x-1].timestamp - chain[x].timestamp) > 60):
                print("invalid timestamp2")
                return False

        return True

    def hash(self, block : Block):
        return hashlib.sha256(
                str(block.index).encode() 
            + str(block.timestamp).encode()
            + str(block.data).encode() 
            + str(block.prev_hash).encode() 
            + str(block.diff).encode() 
            + str(block.nonce).encode()).hexdigest()

if __name__ == "__main__" :
    app = App()
    app.mainloop()