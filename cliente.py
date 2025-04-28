import common_utils
import time

TIMEOUT = 2  # segundos
MAX_PAYLOAD_SIZE = 3  # máximo de caracteres por pacote
WINDOW_SIZE = 4  # tamanho da janela

def choose_protocol():
    print("\nEscolha o protocolo de comunicação:")
    print("1 - Go-Back-N")
    print("2 - Repetição Seletiva")
    
    while True:
        choice = input("Digite sua escolha (1 ou 2): ")
        if choice == '1':
            return "GBN"
        elif choice == '2':
            return "SR"
        else:
            print("Escolha inválida. Digite 1 ou 2.")

def print_window(base, next_seq_num):
    print(f"🪟 Janela atual: {base} - {base + WINDOW_SIZE - 1}")

def start_client(host='localhost', port=12345):
    client_socket = common_utils.create_socket()
    if client_socket is None:
        print("Não foi possível criar o socket do cliente.")
        return

    try:
        client_socket.connect((host, port))
        print(f"Conectado ao servidor {host}:{port}")

        protocol = choose_protocol()

        handshake_message = f"PROTOCOLO:{protocol};TAMANHO_JANELA:{WINDOW_SIZE};TAMANHO_PACOTE:{MAX_PAYLOAD_SIZE}"
        client_socket.sendall(handshake_message.encode())
        server_response = client_socket.recv(1024)
        print(f"Resposta do servidor: {server_response.decode()}")

        message = input("\nDigite a mensagem para enviar: ")

        packets = [message[i:i+MAX_PAYLOAD_SIZE] for i in range(0, len(message), MAX_PAYLOAD_SIZE)]
        total_packets = len(packets)

        base = 0
        next_seq_num = 0
        acked = [False] * total_packets
        timers = {}

        client_socket.settimeout(0.5)

        print_window(base, next_seq_num)

        while base < total_packets:
            while next_seq_num < base + WINDOW_SIZE and next_seq_num < total_packets:
                packet = common_utils.create_packet(next_seq_num % 256, packets[next_seq_num])
                client_socket.sendall(packet)
                print(f"Enviado pacote Seq={next_seq_num % 256}, Dados='{packets[next_seq_num]}'")
                timers[next_seq_num] = time.time()
                next_seq_num += 1

            try:
                ack_packet = client_socket.recv(1024)
                ack_seq = common_utils.parse_ack(ack_packet)
                print(f"ACK recebido: {ack_seq}")

                if protocol == "GBN":
                    if ack_seq == base % 256:
                        base += 1
                        print_window(base, next_seq_num)
                elif protocol == "SR":
                    for idx in range(len(packets)):
                        if idx % 256 == ack_seq:
                            acked[idx] = True
                            print(f"Pacote {idx} confirmado pelo servidor (SR).")
                            break
                    while base < total_packets and acked[base]:
                        base += 1
                        print_window(base, next_seq_num)

            except Exception:
                current_time = time.time()
                for idx in range(base, min(base + WINDOW_SIZE, total_packets)):
                    if not acked[idx] and (current_time - timers.get(idx, current_time)) > TIMEOUT:
                        packet = common_utils.create_packet(idx % 256, packets[idx])
                        client_socket.sendall(packet)
                        print(f"Timeout! Reenviando pacote Seq={idx % 256}, Dados='{packets[idx]}'")
                        timers[idx] = time.time()

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        client_socket.close()
        print("Conexão encerrada.")

if __name__ == "__main__":
    start_client()
