import common_utils
import time
import random

TIMEOUT = 2
MAX_PAYLOAD_SIZE = 3
WINDOW_SIZE = 4

LOSS_PROBABILITY = 0.2
CORRUPTION_PROBABILITY = 0.1
ACK_LOSS_PROBABILITY = 0.1
ACK_CORRUPTION_PROBABILITY = 0.1
FORCE_LOST = set()
FORCE_CORRUPT = set()

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

        while True:
            message = input("\nDigite a mensagem para enviar (ou 'sair' para terminar): ")
            if message.lower() == 'sair':
                break

            force_lost_input = input("Insira o nº do pacote individual a perder (ex: 1, 3) ou aperte Enter: ")
            FORCE_LOST = set(map(int, force_lost_input.split(','))) if force_lost_input else set()

            force_corrupt_input = input("Insira o nº de pacote individual a corromper (ex: 2, 4) ou aperte Enter: ")
            FORCE_CORRUPT = set(map(int, force_corrupt_input.split(','))) if force_corrupt_input else set()

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
                    data = packets[next_seq_num]
                    seq = next_seq_num % 256

                    if seq in FORCE_CORRUPT or random.random() < CORRUPTION_PROBABILITY:
                        corrupted_data = "###"
                        packet = common_utils.create_packet(seq, corrupted_data)
                        print(f"❌ Pacote Seq={seq} CORROMPIDO {'(forçado)' if seq in FORCE_CORRUPT else '(simulação)'}")
                    else:
                        packet = common_utils.create_packet(seq, data)

                    if seq in FORCE_LOST or random.random() < LOSS_PROBABILITY:
                        print(f"⚠️ Pacote Seq={seq} PERDIDO {'(forçado)' if seq in FORCE_LOST else '(simulação)'}")
                    else:
                        client_socket.sendall(packet)
                        print(f"📤 Enviado pacote Seq={seq}, Dados='{data}'")

                    timers[next_seq_num] = time.time()
                    next_seq_num += 1

                try:
                    response = client_socket.recv(1024)

                    # Simula perda de ACK
                    if random.random() < ACK_LOSS_PROBABILITY:
                        print("⚠️ ACK/NACK PERDIDO (simulação)")
                        continue

                    # Simula corrupção de ACK
                    if random.random() < ACK_CORRUPTION_PROBABILITY:
                        print("❌ ACK/NACK CORROMPIDO (simulação)")
                        continue

                    if response.startswith(b'N'):
                        nack_seq = common_utils.parse_nack(response)
                        if nack_seq is not None:
                            print(f"🚫 NACK recebido: {nack_seq}")
                            if protocol == "GBN":
                                base = next_seq_num = nack_seq
                                print(f"🔁 GBN: Voltando para Seq={nack_seq}")
                                print_window(base, next_seq_num)
                            elif protocol == "SR":
                                idx = None
                                for i in range(total_packets):
                                    if i % 256 == nack_seq:
                                        idx = i
                                        break
                                if idx is not None:
                                    packet = common_utils.create_packet(nack_seq, packets[idx])
                                    client_socket.sendall(packet)
                                    print(f"🔁 SR: Reenviado pacote Seq={nack_seq}, Dados='{packets[idx]}'")
                                    timers[idx] = time.time()
                        continue

                    ack_seq = common_utils.parse_ack(response)
                    print(f"✅ ACK recebido: {ack_seq}")

                    if protocol == "GBN":
                        expected_ack_min = base % 256
                        expected_ack_max = (base + WINDOW_SIZE - 1) % 256
                        if expected_ack_min <= ack_seq <= expected_ack_max:
                            deslocamento = (ack_seq - expected_ack_min) + 1
                            for i in range(base, base + deslocamento):
                                print(f"✔️ Pacote {i} confirmado (GBN)")
                            base += deslocamento
                            print_window(base, next_seq_num)
                        else:
                            print(f"⚠️ ACK {ack_seq} fora da janela esperada ({expected_ack_min}-{expected_ack_max}). Ignorado.")
                    elif protocol == "SR":
                        for idx in range(base, min(base + WINDOW_SIZE, total_packets)):
                            if idx % 256 == ack_seq:
                                acked[idx] = True
                                print(f"✔️ Pacote {idx} confirmado (SR)")
                                break
                        else:
                            print(f"⚠️ ACK {ack_seq} fora da janela esperada em SR. Ignorado.")
                        while base < total_packets and acked[base]:
                            base += 1
                            print_window(base, next_seq_num)

                except Exception:
                    current_time = time.time()
                    for idx in range(base, min(base + WINDOW_SIZE, total_packets)):
                        if not acked[idx] and (current_time - timers.get(idx, current_time)) > TIMEOUT:
                            packet = common_utils.create_packet(idx % 256, packets[idx])
                            client_socket.sendall(packet)
                            print(f"⏱️ Timeout! Reenviando pacote Seq={idx % 256}, Dados='{packets[idx]}'")
                            timers[idx] = time.time()

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        client_socket.close()
        print("Conexão encerrada.")

if __name__ == "__main__":
    start_client()