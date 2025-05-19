import common_utils
import socket
import random

MAX_PAYLOAD_SIZE = 3
BUFFER_SIZE = 1024

LOSS_PROBABILITY = 0.2
CORRUPTION_PROBABILITY = 0.1
ACK_LOSS_PROBABILITY = 0.1
ACK_CORRUPTION_PROBABILITY = 0.1

def start_server(host='localhost', port=12345):
    global MAX_PAYLOAD_SIZE, BUFFER_SIZE, LOSS_PROBABILITY, ACK_LOSS_PROBABILITY, CORRUPTION_PROBABILITY, ACK_CORRUPTION_PROBABILITY
    server_socket = common_utils.create_socket()
    if server_socket is None:
        print("Não foi possível iniciar o servidor.")
        return

    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Servidor ouvindo em {host}:{port}")

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(f"\nConexão estabelecida com {addr}")

            try:
                handshake = client_socket.recv(BUFFER_SIZE)
                handshake_info = handshake.decode()
                print(f"Handshake recebido: {handshake_info}")

                protocolo = None
                janela = 1
                sem_perdas = "False"
                sem_corrupcoes = "False"

                campos = handshake_info.split(';')
                for campo in campos:
                    if "PROTOCOLO" in campo:
                        protocolo = campo.split(":")[1]
                    elif "TAMANHO_JANELA" in campo:
                        janela = int(campo.split(":")[1])
                    elif "sem_perdas" in campo:
                        sem_perdas = campo.split(":")[1]
                    elif "sem_corrupções" in campo:
                        sem_corrupcoes = campo.split(":")[1]


                client_socket.sendall(b"Handshake OK")
                print(f"Protocolo escolhido: {protocolo}")
                print(f"Tamanho da janela: {janela}")

                expected_sequence = 0
                full_message = ''
                received_packets = {}

                while True:
                    try:
                        packet = client_socket.recv(BUFFER_SIZE)
                        if not packet:
                            raise ConnectionError("Cliente desconectado.")

                        seq_num, checksum_received, data = common_utils.parse_packet(packet)
                        checksum_calculated = common_utils.calculate_checksum(data)

                        print(f"Pacote recebido: Seq={seq_num}, Dados='{data}', Checksum={checksum_received}")

                        # Corrupção simulada
                        if (sem_corrupcoes == "False") and (random.random() < CORRUPTION_PROBABILITY):
                            print(f"❌ Pacote Seq={seq_num} CORROMPIDO (simulação)")
                            nack = common_utils.create_nack(seq_num)
                            client_socket.sendall(nack)
                            print(f"📢 NACK enviado para Seq={seq_num}")
                            continue

                        # Verificação de checksum
                        if (sem_corrupcoes == "False") and (checksum_received != checksum_calculated):
                            print("⚠️ Checksum inválido! Ignorando pacote.")
                            nack = common_utils.create_nack(seq_num)
                            client_socket.sendall(nack)
                            print(f"📢 NACK enviado para Seq={seq_num}")
                            continue

                        # Simula perda do pacote (ignorado com NACK)
                        if (sem_perdas == "False") and (random.random() < LOSS_PROBABILITY):
                            print(f"⚠️ Pacote Seq={seq_num} PERDIDO (simulação)")
                            nack = common_utils.create_nack(seq_num)
                            client_socket.sendall(nack)
                            print(f"📢 NACK enviado para Seq={seq_num}")
                            continue

                        if protocolo == "GBN":
                            if seq_num == expected_sequence % 256:
                                print(f"✔️ Pacote esperado (Seq={seq_num}).")
                                full_message += data
                                ack = common_utils.create_ack(seq_num)

                                # Simulação de perda/corrupção de ACK
                                if (sem_perdas == "False") and (random.random() < ACK_LOSS_PROBABILITY):
                                    print(f"⚠️ ACK para Seq={seq_num} PERDIDO (simulação)")
                                    continue
                                if (sem_corrupcoes == "False") and (random.random() < ACK_CORRUPTION_PROBABILITY):
                                    print(f"❌ ACK para Seq={seq_num} CORROMPIDO (simulação)")
                                    client_socket.sendall(b"CORRUPTED_ACK")
                                    continue

                                client_socket.sendall(ack)
                                print(f"✅ ACK enviado para Seq={seq_num}")
                                expected_sequence = (expected_sequence + 1) % 256
                            else:
                                print(f"⚠️ Pacote fora de ordem (esperado {expected_sequence % 256}).")
                                nack = common_utils.create_nack(expected_sequence % 256)
                                client_socket.sendall(nack)
                                print(f"📢 NACK enviado (esperado {expected_sequence % 256})")

                        elif protocolo == "SR":
                            if seq_num not in received_packets:
                                received_packets[seq_num] = data
                                print(f"✔️ Pacote armazenado (SR) Seq={seq_num}.")
                            else:
                                print(f"⚠️ Pacote duplicado Seq={seq_num}. Enviando ACK mesmo assim.")

                            ack = common_utils.create_ack(seq_num)

                            if (sem_perdas == "False") and (random.random() < ACK_LOSS_PROBABILITY):
                                print(f"⚠️ ACK para Seq={seq_num} PERDIDO (simulação)")
                                continue
                            if (sem_corrupcoes == "False") and (random.random() < ACK_CORRUPTION_PROBABILITY):
                                print(f"❌ ACK para Seq={seq_num} CORROMPIDO (simulação)")
                                client_socket.sendall(b"CORRUPTED_ACK")
                                continue

                            client_socket.sendall(ack)
                            print(f"✅ ACK individual enviado para Seq={seq_num}")

                    except Exception as e:
                        print(f"Erro na recepção do pacote: {e}")
                        break

                if protocolo == "GBN" and full_message.strip():
                    print(f"\nMensagem completa recebida do cliente (GBN): {full_message}")

                elif protocolo == "SR":
                    mensagem_final = ''.join(received_packets[i] for i in sorted(received_packets.keys()))
                    if mensagem_final.strip():
                        print(f"\nMensagem completa recebida do cliente (SR): {mensagem_final}")

            except Exception as e:
                print(f"Erro na conexão com {addr}: {e}")
            finally:
                client_socket.close()
                print(f"Conexão encerrada com {addr}")

    except KeyboardInterrupt:
        print("\nServidor encerrado manualmente.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()