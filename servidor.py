import socket
import time
from common_utils import (
    recv_all, create_ack_packet, parse_data_header, verify_packet_checksum,
    DATA_HEADER_LEN, ACK_PACKET_LEN, PACKET_TYPE_DATA
)

host = socket.gethostname()
port = 8001
address = (host, port)

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind(address)
server_sock.listen(1)

print(f"Servidor Go-Back-N escutando em {host}:{port}")

conn = None
client_addr = None
try:
    print("Aguardando conexão...")
    conn, client_addr = server_sock.accept()
    print(f"Conectado a {client_addr}")

    expected_seq_num = 0
    reassembled_data = bytearray()

    print("\nAguardando pacotes de dados...")
    while True:
        try:
            header_bytes = recv_all(conn, DATA_HEADER_LEN)
            if header_bytes is None:
                if expected_seq_num > 0:
                    print("\nCliente desconectou (provavelmente fim normal da transmissão).")
                else:
                    print("\nCliente desconectou ou erro fatal ao receber cabeçalho inicial.")
                break

            packet_info = parse_data_header(header_bytes)
            if packet_info is None:
                continue

            packet_type, seq_num, checksum_in_header, data_len = packet_info

            if packet_type != PACKET_TYPE_DATA:
                continue
            if data_len < 0:
                continue

            data_bytes = b''
            if data_len > 0:
                data_bytes = recv_all(conn, data_len)
                if data_bytes is None:
                    break

            full_packet_bytes = header_bytes + data_bytes
            if not verify_packet_checksum(full_packet_bytes):
                continue

            print(f"Pacote Recebido: SeqNum={seq_num}, TamDados={data_len}")

            ack_num_to_send = -1

            if seq_num == expected_seq_num:
                if data_bytes:
                    reassembled_data.extend(data_bytes)
                ack_num_to_send = seq_num
                expected_seq_num += 1
            elif seq_num < expected_seq_num:
                ack_num_to_send = seq_num
            else:
                ack_num_to_send = -1

            if ack_num_to_send != -1:
                ack_packet = create_ack_packet(ack_num_to_send)
                action = "Enviando" if seq_num == ack_num_to_send else "Reenviando"
                print(f"{action} ACK para {ack_num_to_send}...")
                try:
                    conn.sendall(ack_packet)
                except socket.error as e:
                    print(f"Erro ao {action.lower()} ACK para {ack_num_to_send}: {e}")
                    break

        except socket.timeout:
            print("Timeout no servidor esperando pacote.")
            continue
        except ConnectionResetError:
            print("\nCliente fechou a conexão abruptamente.")
            break
        except socket.error as e:
            print(f"Erro de socket: {e}")
            break
        except Exception as e:
            print(f"Erro inesperado: {e}")
            import traceback
            traceback.print_exc()
            break

    print("\n--- Comunicação com o cliente encerrada ---")
    if reassembled_data:
        print(f"Total de dados remontados: {len(reassembled_data)} bytes.")
        print("Dados (início):")
        try:
            preview = reassembled_data[:200].decode('utf-8', errors='replace')
            print(preview + ('...' if len(reassembled_data) > 200 else ''))
        except Exception:
            print(f"{reassembled_data[:200]}...")
    else:
        print("Nenhum dado foi remontado.")

except Exception as e:
    print(f"Erro geral no servidor: {e}")
finally:
    if conn:
        print(f"Fechando conexão com {client_addr}.")
        conn.close()
    if server_sock:
        print("Fechando socket do servidor.")
        server_sock.close()
    print("Servidor encerrado.")