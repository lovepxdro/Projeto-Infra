# cliente.py
import socket
import time
import math
from common_utils import (
    recv_all, create_data_packet, parse_ack_packet, verify_packet_checksum,
    ACK_PACKET_LEN, MAX_DATA_SIZE, WINDOW_SIZE,
    TIMEOUT_SEGUNDOS, MAX_RETRIES, PACKET_TYPE_ACK # Importar tipo ACK
)

host = socket.gethostname()
port = 8001
address = (host, port)

sock = None
try:
    # --- Conexão Inicial ---
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Timeout geral para operações de socket (como recv)
    sock.settimeout(TIMEOUT_SEGUNDOS)
    print(f"Conectando ao servidor {host}:{port}...")
    sock.connect(address)
    print("Conectado.")

    # --- Preparação da Mensagem e Segmentação ---
    mensagem_original = input("Digite a mensagem longa para enviar ao servidor: ")
    mensagem_bytes = mensagem_original.encode('utf-8')

    # Divide a mensagem em segmentos
    segments = []
    if mensagem_bytes: # Garante que não crie um segmento vazio para mensagem vazia
        for i in range(0, len(mensagem_bytes), MAX_DATA_SIZE):
            segments.append(mensagem_bytes[i:i+MAX_DATA_SIZE])
    else:
         segments.append(b'') # Envia um pacote com dados vazios se a msg for vazia

    total_packets = len(segments)
    print(f"Mensagem dividida em {total_packets} segmentos de até {MAX_DATA_SIZE} bytes.")

    # --- Estado da Janela Deslizante e Timer ---
    send_base = 0           # SeqNum do pacote mais antigo não confirmado
    next_seq_num = 0        # Próximo SeqNum a ser enviado
    timer_start_time = None # Quando o timer para send_base foi iniciado
    retransmission_count = 0 # Contagem de retentativas para o send_base atual
    # Buffer de pacotes enviados mas não confirmados (útil para SR, mas pode ajudar a debugar GBN)
    # packets_in_flight = {} # {seq_num: packet_bytes} - Opcional para GBN

    # --- Loop Principal de Envio e Recebimento ---
    print("\n--- Iniciando Transferência ---")
    while send_base < total_packets: # Continua enquanto houver pacotes não confirmados

        # --- Parte 1: Enviar Novos Pacotes (se a janela permitir) ---
        while next_seq_num < send_base + WINDOW_SIZE and next_seq_num < total_packets:
            # Cria o pacote de dados para o próximo segmento
            data_segment = segments[next_seq_num]
            data_packet = create_data_packet(next_seq_num, data_segment)

            print(f"Enviando Pacote SeqNum={next_seq_num} (Janela: [{send_base}...{next_seq_num}], TamDados: {len(data_segment)})...")
            try:
                sock.sendall(data_packet)
                # packets_in_flight[next_seq_num] = data_packet # Opcional
                # Se este é o primeiro pacote na janela atual, inicia o timer para ele
                if send_base == next_seq_num:
                    timer_start_time = time.time()
                    retransmission_count = 0 # Reseta contagem para o novo pacote base
                    print(f"Timer iniciado para SeqNum={send_base}")
                next_seq_num += 1 # Avança para o próximo pacote a ser enviado
            except socket.error as e:
                print(f"Erro CRÍTICO ao enviar pacote {next_seq_num}: {e}")
                send_base = total_packets # Força a saída do loop principal
                break # Sai do loop de envio

        if send_base == total_packets: # Verifica se erro no envio forçou saída
             break

        # --- Parte 2: Tentar Receber ACKs e Tratar Timeout ---
        # Verifica se o timer expirou ANTES de tentar receber
        timer_expired = False
        if timer_start_time is not None and (time.time() - timer_start_time) > TIMEOUT_SEGUNDOS:
            timer_expired = True
            print(f"TIMEOUT DETECTADO! Nenhum ACK recebido para a base atual SeqNum={send_base}.")

        if timer_expired:
            timer_start_time = None # Para reprocessar
            retransmission_count += 1
            if retransmission_count > MAX_RETRIES:
                print(f"Máximo de {MAX_RETRIES} retentativas atingido para SeqNum={send_base}. Abortando.")
                send_base = total_packets # Força saída
                break # Sai do loop principal

            # Retransmite APENAS o pacote 'send_base' (Go-Back-N style)
            if send_base < total_packets:
                 print(f"Retransmitindo Pacote SeqNum={send_base} (Tentativa {retransmission_count}/{MAX_RETRIES})...")
                 try:
                     data_segment = segments[send_base]
                     data_packet = create_data_packet(send_base, data_segment)
                     sock.sendall(data_packet)
                     # Reinicia o timer
                     timer_start_time = time.time()
                 except socket.error as e:
                     print(f"Erro CRÍTICO ao retransmitir pacote {send_base}: {e}")
                     send_base = total_packets # Força saída
                     break
                 except IndexError:
                     print(f"Erro LÓGICO: Tentando retransmitir índice inválido {send_base}")
                     send_base = total_packets
                     break
            continue # Volta ao início do loop principal após retransmitir

        # Se não houve timeout, tenta receber ACK (sem bloquear por muito tempo)
        # Usamos um timeout curto aqui apenas para não bloquear se nada chegar
        # O timeout principal é gerenciado manualmente acima.
        try:
            sock.settimeout(0.01) # Timeout muito curto para recv não bloquear
            ack_packet_bytes = recv_all(sock, ACK_PACKET_LEN)
            sock.settimeout(TIMEOUT_SEGUNDOS) # Restaura timeout padrão

            if ack_packet_bytes:
                if not verify_packet_checksum(ack_packet_bytes):
                    print("ACK recebido com Checksum INVÁLIDO. Descartando.")
                else:
                    # Checksum OK
                    packet_type, ack_num, _ = parse_ack_packet(ack_packet_bytes)
                    if packet_type == PACKET_TYPE_ACK: # É um ACK
                        print(f"ACK Recebido (Checksum OK): AckNum={ack_num}")
                        # Verifica se é um ACK válido para avançar a janela
                        if ack_num >= send_base:
                            old_base = send_base
                            send_base = ack_num + 1 # Avança a base da janela
                            print(f"Janela avançou para base={send_base}")

                            # Remove pacotes confirmados do buffer opcional
                            # for i in range(old_base, send_base):
                            #     packets_in_flight.pop(i, None)

                            # Se a base avançou, o timer antigo não importa.
                            # Reinicia o timer SE ainda houver pacotes em trânsito.
                            if send_base < next_seq_num:
                                 timer_start_time = time.time()
                                 retransmission_count = 0 # Reseta contagem para o novo pacote base
                                 print(f"Timer reiniciado para nova base SeqNum={send_base}")
                            else:
                                 # Todos os pacotes enviados foram confirmados
                                 timer_start_time = None
                                 print("Todos os pacotes enviados foram confirmados. Timer parado.")
                        else:
                            print(f"ACK antigo (AckNum={ack_num} < Base={send_base}). Ignorando.")
                    else:
                        print(f"Pacote inesperado (Tipo={packet_type}) recebido. Ignorando.")
            # Se ack_packet_bytes for None (conexão fechada em recv_all), o loop principal sairá

        except socket.timeout:
            # Timeout do recv (0.01s), significa que nenhum ACK estava pronto.
            # Isso é esperado e normal, apenas continua o loop principal.
            pass
        except socket.error as e:
            print(f"Erro de socket ao tentar receber ACK: {e}")
            send_base = total_packets # Força saída
            break # Sai do loop principal

    # --- Fim do Loop Principal ---

    # Pequeno delay para garantir que o último ACK do servidor seja processado, se necessário
    # time.sleep(0.1)

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