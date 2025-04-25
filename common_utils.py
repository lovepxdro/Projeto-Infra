import struct
import socket
import time

PACKET_TYPE_DATA = 0
PACKET_TYPE_ACK = 1
MAX_DATA_SIZE = 100
WINDOW_SIZE = 5
TIMEOUT_SEGUNDOS = 1.0
MAX_RETRIES = 5

def calculate_checksum(data_bytes):
    if not data_bytes:
        return 0
    checksum = 0
    for byte in data_bytes:
        checksum = (checksum + byte) & 0xFFFF
    return checksum

DATA_HEADER_FORMAT = '>BIHI'
DATA_HEADER_LEN = struct.calcsize(DATA_HEADER_FORMAT)

ACK_PACKET_FORMAT = '>BIH'
ACK_PACKET_LEN = struct.calcsize(ACK_PACKET_FORMAT)

def create_data_packet(seq_num, data_bytes):
    data_len = len(data_bytes)
    temp_header_no_checksum = struct.pack('>BII', PACKET_TYPE_DATA, seq_num, data_len)
    checksum_data = temp_header_no_checksum + data_bytes
    checksum = calculate_checksum(checksum_data)
    final_header = struct.pack(DATA_HEADER_FORMAT, PACKET_TYPE_DATA, seq_num, checksum, data_len)
    return final_header + data_bytes

def create_ack_packet(ack_num):
    temp_ack_no_checksum = struct.pack('>BI', PACKET_TYPE_ACK, ack_num)
    checksum = calculate_checksum(temp_ack_no_checksum)
    return struct.pack(ACK_PACKET_FORMAT, PACKET_TYPE_ACK, ack_num, checksum)

def verify_packet_checksum(packet_bytes):
    if not packet_bytes:
        return False

    packet_type = packet_bytes[0]

    try:
        if packet_type == PACKET_TYPE_DATA:
            if len(packet_bytes) < DATA_HEADER_LEN:
                return False
            _, seq_num, received_checksum, data_len = struct.unpack_from(DATA_HEADER_FORMAT, packet_bytes)
            temp_header_no_checksum = struct.pack('>BII', packet_type, seq_num, data_len)
            data_bytes = packet_bytes[DATA_HEADER_LEN:]
            checksum_data = temp_header_no_checksum + data_bytes
            calculated_checksum = calculate_checksum(checksum_data)
            return calculated_checksum == received_checksum

        elif packet_type == PACKET_TYPE_ACK:
            if len(packet_bytes) != ACK_PACKET_LEN:
                return False
            _, ack_num, received_checksum = struct.unpack(ACK_PACKET_FORMAT, packet_bytes)
            ack_no_checksum = struct.pack('>BI', packet_type, ack_num)
            calculated_checksum = calculate_checksum(ack_no_checksum)
            return calculated_checksum == received_checksum
        else:
            return False
    except struct.error:
        return False
    except IndexError:
        return False

def parse_data_header(header_bytes):
    if len(header_bytes) != DATA_HEADER_LEN:
        return None, None, None, None
    try:
        packet_type, seq_num, checksum, data_len = struct.unpack(DATA_HEADER_FORMAT, header_bytes)
        if packet_type != PACKET_TYPE_DATA:
            return None, None, None, None
        return packet_type, seq_num, checksum, data_len
    except struct.error:
        return None, None, None, None

def parse_ack_packet(packet_bytes):
    if len(packet_bytes) != ACK_PACKET_LEN:
        return None, None, None
    try:
        packet_type, ack_num, checksum = struct.unpack(ACK_PACKET_FORMAT, packet_bytes)
        if packet_type != PACKET_TYPE_ACK:
            return None, None, None
        return packet_type, ack_num, checksum
    except struct.error:
        return None, None, None

def recv_all(sock, n):
    data = bytearray()
    while len(data) < n:
        try:
            chunk_size = min(n - len(data), 4096)
            packet = sock.recv(chunk_size)
            if not packet:
                return None
            data.extend(packet)
        except socket.timeout:
            raise socket.timeout
        except socket.error:
            return None
    return bytes(data)