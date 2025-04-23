import socket
import struct

HEADER_LENGTH = 4

def send_message(sock, message):
    """Prefixes the message with its length and sends it."""
    encoded_message = message.encode('utf-8')
    message_length = len(encoded_message)
    length_header = struct.pack('>I', message_length)
    try:
        sock.sendall(length_header)
        sock.sendall(encoded_message)
    except socket.error as e:
        print(f"Error sending data: {e}")
        raise

def receive_message(sock):
    """Receives a message prefixed with its length."""
    try:
        raw_length_header = recv_all(sock, HEADER_LENGTH)
        if not raw_length_header:
            return None
        
        message_length = struct.unpack('>I', raw_length_header)[0]
        
        message_data = recv_all(sock, message_length)
        if not message_data:
             return None
             
        return message_data.decode('utf-8')
        
    except socket.error as e:
        print(f"Error receiving data: {e}")
        return None
    except struct.error as e:
        print(f"Error unpacking header: {e}")
        return None


def recv_all(sock, n):
    """Helper function to receive exactly n bytes."""
    data = bytearray()
    while len(data) < n:
        try:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        except socket.error as e:
            print(f"Error in recv_all: {e}")
            return None
    return bytes(data)