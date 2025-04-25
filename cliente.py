import socket
import time
import math
from common_utils import (
    recv_all, create_data_packet, parse_ack_packet, verify_packet_checksum,
    ACK_PACKET_LEN, MAX_DATA_SIZE, WINDOW_SIZE,
    TIMEOUT_SEGUNDOS, MAX_RETRIES, PACKET_TYPE_ACK
)

host = socket.gethostname()
port = 8001
address = (host, port)

sock = None
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT_SEGUNDOS)
    print(f"Conectando ao servidor {host}:{port}...")
    sock.connect(address)
    print("Conectado.")

    mensagem_original = input("Digite a mensagem longa para enviar ao servidor: ")
    mensagem_bytes = mensagem_original.encode('utf-8')

    segments = []
    if mensagem_bytes:
        for i in range(0, len(mensagem_bytes), MAX_DATA_SIZE):
            segments.append(mensagem_bytes[i:i+MAX_DATA_SIZE])
    else:
         segments.append(b'')

    total_packets = len(segments)
    print(f"Mensagem dividida em {total_packets} segmentos de até {MAX_DATA_SIZE} bytes.")

    send_base = 0
    next_seq_num = 0
    timer_start_time = None
    retransmission_count = 0

    print("\n--- Iniciando Transferência ---")
    while send_base < total_packets:

        while next_seq_num < send_base + WINDOW_SIZE and next_seq_num < total_packets:
            data_segment = segments[next_seq_num]
            data_packet = create_data_packet(next_seq_num, data_segment)

            print(f"Enviando Pacote SeqNum={next_seq_num} (Janela: [{send_base}...{next_seq_num}], TamDados: {len(data_segment)})...")
            try:
                sock.sendall(data_packet)
                if send_base == next_seq_num:
                    timer_start_time = time.time()
                    retransmission_count = 0
                    print(f"Timer iniciado para SeqNum={send_base}")
                next_seq_num += 1
            except socket.error as e:
                print(f"Erro CRÍTICO ao enviar pacote {next_seq_num}: {e}")
                send_base = total_packets
                break

        if send_base == total_packets:
             break

        timer_expired = False
        if timer_start_time is not None and (time.time() - timer_start_time) > TIMEOUT_SEGUNDOS:
            timer_expired = True
            print(f"TIMEOUT DETECTADO! Nenhum ACK recebido para a base atual SeqNum={send_base}.")

        if timer_expired:
            timer_start_time = None
            retransmission_count += 1
            if retransmission_count > MAX_RETRIES:
                print(f"Máximo de {MAX_RETRIES} retentativas atingido para SeqNum={send_base}. Abortando.")
                send_base = total_packets
                break

            if send_base < total_packets:
                 print(f"Retransmitindo Pacote SeqNum={send_base} (Tentativa {retransmission_count}/{MAX_RETRIES})...")
                 try:
                     data_segment = segments[send_base]
                     data_packet = create_data_packet(send_base, data_segment)
                     sock.sendall(data_packet)
                     timer_start_time = time.time()
                 except socket.error as e:
                     print(f"Erro CRÍTICO ao retransmitir pacote {send_base}: {e}")
                     send_base = total_packets
                     break
                 except IndexError:
                     print(f"Erro LÓGICO: Tentando retransmitir índice inválido {send_base}")
                     send_base = total_packets
                     break
            continue

        try:
            sock.settimeout(0.01)
            ack_packet_bytes = recv_all(sock, ACK_PACKET_LEN)
            sock.settimeout(TIMEOUT_SEGUNDOS)

            if ack_packet_bytes:
                if not verify_packet_checksum(ack_packet_bytes):
                    print("ACK recebido com Checksum INVÁLIDO. Descartando.")
                else:
                    packet_type, ack_num, _ = parse_ack_packet(ack_packet_bytes)
                    if packet_type == PACKET_TYPE_ACK:
                        print(f"ACK Recebido (Checksum OK): AckNum={ack_num}")
                        if ack_num >= send_base:
                            old_base = send_base
                            send_base = ack_num + 1
                            print(f"Janela avançou para base={send_base}")
                            if send_base < next_seq_num:
                                 timer_start_time = time.time()
                                 retransmission_count = 0
                                 print(f"Timer reiniciado para nova base SeqNum={send_base}")
                            else:
                                 timer_start_time = None
                                 print("Todos os pacotes enviados foram confirmados. Timer parado.")
                        else:
                            print(f"ACK antigo (AckNum={ack_num} < Base={send_base}). Ignorando.")
                    else:
                        print(f"Pacote inesperado (Tipo={packet_type}) recebido. Ignorando.")
        except socket.timeout:
            pass
        except socket.error as e:
            print(f"Erro de socket ao tentar receber ACK: {e}")
            send_base = total_packets
            break

    if send_base >= total_packets:
        print("\n==> Sucesso: Transferência concluída e todos os pacotes confirmados.")
    else:
        print(f"\n==> Falha: Transferência interrompida. Base={send_base}, Total={total_packets}")

except socket.error as e:
    print(f"Erro de socket (conexão/geral): {e}")
except Exception as e:
    print(f"Ocorreu um erro inesperado no cliente: {e}")
finally:
    if sock:
        print("Fechando socket do cliente.")
        sock.close()
    print("Cliente encerrado.")