# common_utils.py
import struct
import socket
import time # Necessário para time.time() no cliente

# --- Constantes do Protocolo ---
PACKET_TYPE_DATA = 0
PACKET_TYPE_ACK = 1
MAX_DATA_SIZE = 100 # Tamanho máximo dos dados em um pacote (bytes)
WINDOW_SIZE = 5     # Tamanho da janela de envio (pacotes)
TIMEOUT_SEGUNDOS = 1.0 # Timeout para esperar ACK (1 segundo)
MAX_RETRIES = 5     # Máximo de timeouts para o mesmo pacote base antes de desistir

# --- Checksum Function (Exemplo Simples: Soma de Bytes) ---
# Nota: Este checksum é muito básico e não robusto como os usados em TCP/UDP reais.
#       Serve apenas para demonstrar o conceito de detecção de erro.
def calculate_checksum(data_bytes):
    """Calcula um checksum simples somando os valores dos bytes."""
    if not data_bytes:
        return 0 # Checksum de zero bytes é zero
    checksum = 0
    for byte in data_bytes:
        checksum = (checksum + byte) & 0xFFFF # Soma e mantém em 16 bits (wrap around)
    return checksum

# --- Formatos de Pacote (COM CHECKSUM) ---
# H = unsigned short (2 bytes) para o checksum
# > = Big-endian (Ordem de Rede)
# B = unsigned char (1 byte)
# I = unsigned int (4 bytes)

# Formato Cabeçalho Dados: Tipo(1B), SeqNum(4B), Checksum(2B), TamDados(4B)
DATA_HEADER_FORMAT = '>BIHI' # Adicionado 'H' para Checksum
DATA_HEADER_LEN = struct.calcsize(DATA_HEADER_FORMAT) # 1 + 4 + 2 + 4 = 11 bytes

# Formato Pacote ACK: Tipo(1B), AckNum(4B), Checksum(2B)
ACK_PACKET_FORMAT = '>BIH' # Adicionado 'H' para Checksum
ACK_PACKET_LEN = struct.calcsize(ACK_PACKET_FORMAT) # 1 + 4 + 2 = 7 bytes


# --- Funções Auxiliares de Criação de Pacote ---

def create_data_packet(seq_num, data_bytes):
    """Cria um pacote de dados com cabeçalho e checksum."""
    data_len = len(data_bytes)
    # Calcula checksum SOBRE OS CAMPOS + DADOS (exceto o próprio campo checksum)
    # Empacota temporariamente sem checksum (ou com checksum 0) para calcular
    temp_header_no_checksum = struct.pack('>BII', PACKET_TYPE_DATA, seq_num, data_len)
    checksum_data = temp_header_no_checksum + data_bytes
    checksum = calculate_checksum(checksum_data)

    # Empacota o cabeçalho final COM o checksum
    final_header = struct.pack(DATA_HEADER_FORMAT, PACKET_TYPE_DATA, seq_num, checksum, data_len)
    return final_header + data_bytes

def create_ack_packet(ack_num):
    """Cria um pacote ACK com checksum."""
    # Calcula checksum sobre Tipo + AckNum
    temp_ack_no_checksum = struct.pack('>BI', PACKET_TYPE_ACK, ack_num)
    checksum = calculate_checksum(temp_ack_no_checksum)
    # Empacota final COM checksum
    return struct.pack(ACK_PACKET_FORMAT, PACKET_TYPE_ACK, ack_num, checksum)

# --- Funções Auxiliares de Verificação e Parse ---

def verify_packet_checksum(packet_bytes):
    """
    Verifica o checksum de um pacote (Dados ou ACK).
    Retorna True se OK, False se corrompido ou formato inválido.
    """
    if not packet_bytes:
        print("Erro Checksum: Pacote vazio.")
        return False

    # Extrai o tipo para saber o formato esperado
    packet_type = packet_bytes[0] # Primeiro byte é o tipo

    try:
        if packet_type == PACKET_TYPE_DATA:
            if len(packet_bytes) < DATA_HEADER_LEN:
                 print("Erro Checksum (DATA): Pacote menor que cabeçalho.")
                 return False
            # Desempacota header de dados para pegar o checksum recebido
            _, seq_num, received_checksum, data_len = struct.unpack_from(DATA_HEADER_FORMAT, packet_bytes)
            # Recria o que foi usado para calcular o checksum original
            temp_header_no_checksum = struct.pack('>BII', packet_type, seq_num, data_len)
            data_bytes = packet_bytes[DATA_HEADER_LEN:]
            checksum_data = temp_header_no_checksum + data_bytes
            # Recalcula o checksum
            calculated_checksum = calculate_checksum(checksum_data)

            if calculated_checksum == received_checksum:
                return True
            else:
                print(f"Checksum DATA inválido! Seq={seq_num}, Recebido={received_checksum}, Calculado={calculated_checksum}")
                return False

        elif packet_type == PACKET_TYPE_ACK:
             if len(packet_bytes) != ACK_PACKET_LEN:
                 print(f"Erro Checksum (ACK): Tamanho incorreto {len(packet_bytes)} != {ACK_PACKET_LEN}.")
                 return False
             # Desempacota ACK para pegar o checksum recebido
             _, ack_num, received_checksum = struct.unpack(ACK_PACKET_FORMAT, packet_bytes)
             # Recria o que foi usado para calcular o checksum original
             ack_no_checksum = struct.pack('>BI', packet_type, ack_num)
             # Recalcula o checksum
             calculated_checksum = calculate_checksum(ack_no_checksum)

             if calculated_checksum == received_checksum:
                 return True
             else:
                 print(f"Checksum ACK inválido! Ack={ack_num}, Recebido={received_checksum}, Calculado={calculated_checksum}")
                 return False
        else:
             # Tipo desconhecido
             print(f"Tipo de pacote desconhecido ({packet_type}) para verificação de checksum.")
             return False
    except struct.error as e:
        print(f"Erro de struct ao verificar checksum: {e}")
        return False
    except IndexError:
         print("Erro de índice ao verificar checksum (pacote muito curto?).")
         return False


def parse_data_header(header_bytes):
    """Analisa o cabeçalho de um pacote de dados (COM checksum)."""
    if len(header_bytes) != DATA_HEADER_LEN:
        return None, None, None, None # Tamanho incorreto
    try:
        # Desempacota: tipo, numero_seq, checksum, tamanho_dados
        packet_type, seq_num, checksum, data_len = struct.unpack(DATA_HEADER_FORMAT, header_bytes)
        if packet_type != PACKET_TYPE_DATA:
            return None, None, None, None # Não é pacote de dados
        return packet_type, seq_num, checksum, data_len
    except struct.error:
        return None, None, None, None # Erro ao desempacotar

def parse_ack_packet(packet_bytes):
    """Analisa um pacote ACK (COM checksum)."""
    if len(packet_bytes) != ACK_PACKET_LEN:
        return None, None, None # Tamanho incorreto
    try:
        # Desempacota: tipo, ack_num, checksum
        packet_type, ack_num, checksum = struct.unpack(ACK_PACKET_FORMAT, packet_bytes)
        if packet_type != PACKET_TYPE_ACK:
            return None, None, None # Não é pacote ACK
        return packet_type, ack_num, checksum
    except struct.error:
        return None, None, None # Erro ao desempacotar


# --- Função Auxiliar de Rede ---

def recv_all(sock, n):
    """Helper function to receive exactly n bytes using the socket's timeout."""
    data = bytearray()
    while len(data) < n:
        try:
            # Pede o restante necessário, limitado a um chunk razoável
            chunk_size = min(n - len(data), 4096)
            packet = sock.recv(chunk_size)
            if not packet:
                # Conexão fechada pelo outro lado
                print("recv_all: Conexão fechada inesperadamente.")
                return None
            data.extend(packet)
        except socket.timeout:
            # Timeout ocorreu ANTES de receber todos os n bytes
            # Retorna None para indicar que o timeout específico da operação recv ocorreu
            # print("recv_all: Timeout durante recebimento.") # Debug opcional
            raise socket.timeout # Re-levanta a exceção para ser tratada no loop principal
        except socket.error as e:
            print(f"Erro em recv_all: {e}")
            return None # Indica falha irrecuperável
    return bytes(data) # Retorna os bytes completos