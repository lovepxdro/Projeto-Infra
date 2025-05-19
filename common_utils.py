import socket
import struct
import hashlib

def create_socket():
    try:
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        print(f"Erro ao criar socket: {e}")
        return None

def calculate_checksum(data):
    checksum = hashlib.md5(data.encode()).hexdigest()
    return checksum[:4]  # 4 caracteres (16 bits)

def create_packet(seq_num, data):
    checksum = calculate_checksum(data)
    header = struct.pack('!B4s', seq_num, checksum.encode())
    return header + data.encode()

def parse_packet(packet):
    seq_num, checksum = struct.unpack('!B4s', packet[:5])
    data = packet[5:].decode()
    return seq_num, checksum.decode(), data

# ACK e NACK agora incluem identificador ('A' ou 'N') seguido do número de sequência
def create_ack(seq_num):
    return struct.pack('!cB', b'A', seq_num)

def parse_ack(ack_packet):
    tipo, seq_num = struct.unpack('!cB', ack_packet)
    if tipo != b'A':
        raise ValueError("Pacote não é um ACK válido.")
    return seq_num

def create_nack(seq_num):
    return struct.pack('!cB', b'N', seq_num)

def parse_nack(nack_packet):
    tipo, seq_num = struct.unpack('!cB', nack_packet)
    if tipo != b'N':
        raise ValueError("Pacote não é um NACK válido.")
    return seq_num