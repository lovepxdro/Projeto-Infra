# servidor.py
import socket
import time
from common_utils import (
    recv_all, create_ack_packet, parse_data_header, verify_packet_checksum,
    DATA_HEADER_LEN, ACK_PACKET_LEN, PACKET_TYPE_DATA # Importar tipo DATA
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

    expected_seq_num = 0       # Número do próximo pacote em ordem esperado
    reassembled_data = bytearray() # Buffer para remontar a mensagem/dados

    print("\nAguardando pacotes de dados...")
    while True: # Loop para receber pacotes continuamente
        try:
            # 1. Tentar receber o cabeçalho do pacote de dados
            # Usar um timeout aqui pode ser útil se o cliente parar
            # conn.settimeout(60.0) # Ex: Espera 60s por um pacote
            header_bytes = recv_all(conn, DATA_HEADER_LEN)
            if header_bytes is None:
                # <<< MUDANÇA AQUI vvv
                if expected_seq_num > 0: # Se já recebemos algum pacote antes...
                    print("\nCliente desconectou (provavelmente fim normal da transmissão).")
                else: # Se nenhum pacote foi recebido ainda...
                    print("\nCliente desconectou ou erro fatal ao receber cabeçalho inicial.")
                # <<< FIM DA MUDANÇA ^^^
                break # Sai do loop principal

            # 2. Tenta parsear o cabeçalho para pegar o tamanho dos dados
            packet_info = parse_data_header(header_bytes)
            if packet_info is None:
                 print("Cabeçalho inválido recebido. Ignorando.")
                 # Poderia ser um ACK perdido do cliente? Difícil saber.
                 continue

            packet_type, seq_num, checksum_in_header, data_len = packet_info

            # Validação básica do tipo e tamanho
            if packet_type != PACKET_TYPE_DATA:
                print(f"Recebido tipo de pacote inesperado {packet_type}. Ignorando.")
                continue
            if data_len < 0:
                print(f"Tamanho de dados inválido ({data_len}) no cabeçalho Seq={seq_num}. Descartando.")
                continue

            # 3. Receber os dados do pacote (payload)
            data_bytes = b''
            if data_len > 0:
                data_bytes = recv_all(conn, data_len)
                if data_bytes is None:
                    print(f"\nCliente desconectou ou erro fatal ao receber dados do pacote {seq_num}.")
                    break # Sai do loop principal

            # --- Lógica Principal Go-Back-N no Receptor ---

            # 4. Verificar Checksum do pacote completo (header + data)
            full_packet_bytes = header_bytes + data_bytes
            if not verify_packet_checksum(full_packet_bytes):
                print(f"Checksum INVÁLIDO para pacote SeqNum={seq_num}. Descartando (NÃO envia ACK).")
                # GBN: Descarta silenciosamente. O timeout do cliente cuidará.
                continue

            # Checksum OK!
            print(f"Pacote Recebido (Checksum OK): SeqNum={seq_num}, TamDados={data_len}")

            # 5. Verificar Número de Sequência e Enviar ACK apropriado
            ack_num_to_send = -1 # Indica se um ACK deve ser enviado

            if seq_num == expected_seq_num:
                # --- Pacote EM ORDEM ---
                print(f"Pacote {seq_num} EM ORDEM recebido e aceito.")
                # Processar/Armazenar os dados
                if data_bytes:
                    reassembled_data.extend(data_bytes)
                # Prepara ACK para este pacote
                ack_num_to_send = seq_num
                # Avançar para o próximo número de sequência esperado
                expected_seq_num += 1

            elif seq_num < expected_seq_num:
                # --- Pacote DUPLICADO ---
                print(f"Pacote DUPLICADO SeqNum={seq_num} recebido (esperando {expected_seq_num}).")
                # Reenviar ACK para este pacote antigo (importante!)
                ack_num_to_send = seq_num
                # Não processa os dados novamente, não avança expected_seq_num

            else: # seq_num > expected_seq_num
                # --- Pacote FORA DE ORDEM (Adiantado) ---
                print(f"Pacote FORA DE ORDEM SeqNum={seq_num} recebido (esperando {expected_seq_num}). Descartando (NÃO envia ACK).")
                # GBN: Descarta silenciosamente. O cliente vai estourar o timer para expected_seq_num.
                # NÃO envia ACK para pacote fora de ordem em GBN puro.
                ack_num_to_send = -1 # Garante que não envia ACK

            # 6. Enviar ACK (se aplicável)
            if ack_num_to_send != -1:
                ack_packet = create_ack_packet(ack_num_to_send)
                action = "Enviando" if seq_num == ack_num_to_send else "Reenviando"
                print(f"{action} ACK para {ack_num_to_send}...")
                try:
                    conn.sendall(ack_packet)
                except socket.error as e:
                    print(f"Erro ao {action.lower()} ACK para {ack_num_to_send}: {e}")
                    break # Aborta se não conseguir enviar ACK

        except socket.timeout:
            print("Timeout no servidor esperando pacote. Cliente pode ter parado.")
            # Considerar fechar a conexão após vários timeouts se necessário
            continue # Continua esperando por enquanto
        except ConnectionResetError:
             print("\nCliente fechou a conexão abruptamente.")
             break
        except socket.error as e:
             print(f"Erro de socket no servidor durante recebimento: {e}")
             break # Encerra o loop para este cliente
        except Exception as e:
             print(f"Ocorreu um erro inesperado no servidor: {e}")
             import traceback
             traceback.print_exc() # Imprime mais detalhes do erro
             break # Encerra em caso de erro grave

    # --- Fim do loop de recebimento ---
    print("\n--- Comunicação com o cliente encerrada ---")
    if reassembled_data:
        print(f"Total de dados remontados: {len(reassembled_data)} bytes.")
        # Tenta decodificar como texto para exibição, mas pode falhar se não for texto
        print("Dados (início):")
        try:
            preview = reassembled_data[:200].decode('utf-8', errors='replace')
            print(preview + ('...' if len(reassembled_data) > 200 else ''))
        except Exception:
             print(f"{reassembled_data[:200]}...") # Mostra como bytes se decode falhar
    else:
        print("Nenhum dado foi remontado.")


except Exception as e:
    print(f"Ocorreu um erro GERAL no servidor antes ou durante a conexão: {e}")
finally:
    if conn:
        print(f"Fechando conexão com {client_addr}.")
        conn.close()
    if server_sock:
        print("Fechando socket do servidor.")
        server_sock.close()
    print("Servidor encerrado.")