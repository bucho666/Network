# -*- coding: utf-8 -*-
import socket
import select

class Socket(object):
    def __init__(self, raw_socket=None):
        if not raw_socket:
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket = raw_socket

    def receivable(self):
        read, write, error = select.select([self._socket], [], [], 0)
        if read: return True
        return False

    def close(self):
        if self._socket is None: return
        self._socket.close()
        self._socket = None

    def is_close(self):
        if self._socket is None: return True
        return False

class ServerSocket(Socket):
    def __init__(self):
        Socket.__init__(self)
        
    def listen(self, port, bind_address='localhost', backlog=5):
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((bind_address, port))
        self._socket.listen(backlog)

    def accept(self):
        raw_socket, address = self._socket.accept() 
        return ClientSocket(raw_socket)

class ClientSocket(Socket):
    RECEIVE_SIZE = 65536
    def __init__(self, raw_socket=None):
        Socket.__init__(self, raw_socket)
        self._buffer = ''

    def connect(self, address, port):
        self._socket.connect((address, port))

    def receive(self):
        if self.is_close():
            return None
        try:
            return self._receive()
        except socket.error:
            self.close()
            return None

    def _receive(self):
        data = self._socket.recv(self.RECEIVE_SIZE)
        if data:
            return data
        self.close()
        return None

    def send(self, message):
        self._buffer += message

    def flush(self):
        if self.is_close() or self._buffer == '': return
        try:
            self._socket.send(self._buffer)
            self._buffer = ''
        except socket.error:
            self.close()

if __name__ == '__main__':
    import unittest

    class NetWorkTest(unittest.TestCase):
        PORT = 6666
        TEST_MESSAGE = 'this is test message'
        def setUp(self):
            self.server = ServerSocket()
            self.client = ClientSocket()

        def tearDown(self):
            self.server.close()
            self.client.close()

        def testConnectionError(self):
            self.assertRaises(socket.error, self.client.connect, 'localhost', self.PORT)

        def testListenAndNoAccept(self):
            self.server.listen(self.PORT)
            self.assertFalse(self.server.receivable())

        def testConnect(self):
            self.server.listen(self.PORT)
            self.client.connect('localhost', self.PORT)
            self.assertTrue(self.server.receivable())

        def testAccept(self):
            server_side_socket = self.connect()
            self.assertEqual(server_side_socket.__class__.__name__, 'ClientSocket')

        def testServerSideClose(self):
            server_side_socket = self.connect()
            server_side_socket.close()
            data = self.client.receive()
            self.assertFalse(data)
            self.assertTrue(self.client.is_close())

        def testClientSideClose(self):
            server_side_socket = self.connect()
            self.client.close()
            data = server_side_socket.receive()
            self.assertFalse(data)
            self.assertTrue(server_side_socket.is_close())

        def testSendFromClient(self):
            server_side_socket = self.connect()
            self.client.send(self.TEST_MESSAGE)
            self.client.flush()
            self.assertTrue(server_side_socket.receivable())
            self.assertEqual(server_side_socket.receive(), self.TEST_MESSAGE)

        def testSendFromServerSide(self):
            server_side_socket = self.connect()
            server_side_socket.send(self.TEST_MESSAGE)
            server_side_socket.flush()
            self.assertTrue(self.client.receivable())
            self.assertEqual(self.client.receive(), self.TEST_MESSAGE)

        def testReceiveWhenClosed(self):
            server_side_socket = self.connect()
            server_side_socket.close()
            self.client.close()
            self.assertEqual(server_side_socket.receive(), None)
            self.assertEqual(self.client.receive(), None)

        def testSendWhenClosed(self):
            server_side_socket = self.connect()
            server_side_socket.close()
            self.client.close()
            self.assertEqual(server_side_socket.send(self.TEST_MESSAGE), None)
            self.assertEqual(self.client.send(self.TEST_MESSAGE), None)

        def connect(self):
            self.server.listen(self.PORT)
            self.client.connect('localhost', self.PORT)
            return self.server.accept()

    unittest.main() 
