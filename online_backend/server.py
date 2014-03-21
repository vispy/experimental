import sys, json, socket, threading, pickle, Image, struct, base64
from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File

from autobahn.twisted.websocket import WebSocketServerFactory, \
                                         WebSocketServerProtocol, \
                                         listenWS


PORT = 8090
HOST = "localhost"

class BroadcastServerProtocol(WebSocketServerProtocol):
    def __init__(self):
        self.client = ""

    def onOpen(self):
        self.factory.register(self)

    # Send PNG image on every message
    def onMessage(self, msg, binary):
        self.factory.broadcast(send_PNG())

    def connectionLost(self, reason):
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)

class BroadcastServerFactory(WebSocketServerFactory):
    """
    Simple broadcast server broadcasting any message it receives to all
    currently connected clients.
    """

    def __init__(self, url, debug = False, debugCodePaths = False):
        WebSocketServerFactory.__init__(self, url, debug = debug,
                                            debugCodePaths = debugCodePaths)
        self.clients = []

    def register(self, client):
        if not client in self.clients:
            self.clients.append(client)
            print "Client registered"

    def unregister(self, client):
        if client in self.clients:
            self.clients.remove(client)
            print "Client unregistered"

    def broadcast(self, msg):
        for c in self.clients:
            c.sendMessage(msg)


class Listener(threading.Thread):
    def __init__(self):
        super(Listener, self).__init__()
        self.socket = socket.socket()
        self.socket.bind((HOST, PORT))
        self.socket.listen(3)
        self.sc, self.address = self.socket.accept()
        print "Client accepted"

    def recv_msg(self):
        # Read message length and unpack it into an integer
        raw_msglen = self.recvall(4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self.recvall(msglen)

    def recvall(self, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = ''
        while len(data) < n:
            packet = self.sc.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def run(self):
        msg, data = "", ""

        while True:
            try:
                # Read all image data
                while True:
                    data = self.recv_msg()
                    msg += data
                    # I know, that is an ugly way, but for now it is ok.
                    if len(data) != 4096:
                        break

                # Well it is getting uglier..
                save_PNG(msg)
                msg, data = "", ""

            except Exception, e:
                print str(e)
                self.socket.close()
                sys.exit()

#Global variable which altered in a thread and can be used by the main thread
PNG = ""
FILE_NAME = "test.png"

# Listener thread calls this function
def save_PNG(msg):
    """
    msg is a numpy.ndarray
    since Image module can convert numpy.ndarray into a PNG image
    with fromarray() function I used it.
    However I couldn't get the bytes from it so every time it is
    saving the image onto disk and re-opens it in order to convert
    it to base64 string.
    """
    global PNG

    img = pickle.loads(msg)
    img = Image.fromarray(img)

    # Save image onto disk
    img.save(FILE_NAME)
    # Reopen it (binary)
    with open("test.png","rb") as im:
        PNG = base64.b64encode(im.read())

# Main thread calls this function
def send_PNG():
    return json.dumps({"image" : PNG})

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'debug':
        log.startLogging(sys.stdout)
        debug = True
    else:
        debug = False

    listener = Listener()
    listener.start()

    ServerFactory = BroadcastServerFactory

    factory = ServerFactory("ws://localhost:9000",
                                    debug = debug,
                                    debugCodePaths = debug)

    factory.protocol = BroadcastServerProtocol
    factory.setProtocolOptions(allowHixie76 = True)
    listenWS(factory)

    reactor.run()
