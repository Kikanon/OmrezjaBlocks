from array import array
import hashlib
import re

class App:
    class Block:
        index = 0
        data = ""
        timestamp = 0
        hash = ""
        previousHash = ""
        diff = 5
        nonce = 0

    chain = []

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


if __name__ == "__main__" :
    test = App()
    test.hello()