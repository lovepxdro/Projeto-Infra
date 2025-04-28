import common_utils

MAX_PAYLOAD_SIZE = 3
BUFFER_SIZE = 1024

def start_server(host='localhost', port=12345):
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

                campos = handshake_info.split(';')
                for campo in campos:
                    if "PROTOCOLO" in campo:
                        protocolo = campo.split(":")[1]
                    elif "TAMANHO_JANELA" in campo:
                        janela = int(campo.split(":")[1])

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
                            break

                        seq_num, checksum_received, data = common_utils.parse_packet(packet)
                        checksum_calculated = common_utils.calculate_checksum(data)

                        print(f"Pacote recebido: Seq={seq_num}, Dados='{data}', Checksum={checksum_received}")

                        if checksum_received != checksum_calculated:
                            print("Checksum inválido! Ignorando pacote.")
                            continue

                        if protocolo == "GBN":
                            if seq_num == expected_sequence % 256:
                                print(f"Pacote esperado (Seq={seq_num}).")
                                full_message += data
                                ack = common_utils.create_ack(seq_num)
                                client_socket.sendall(ack)
                                print(f"ACK enviado para Seq={seq_num}")
                                expected_sequence = (expected_sequence + 1) % 256
                            else:
                                print(f"Pacote fora de ordem (esperado {expected_sequence % 256}). Ignorado.")
                                last_ack = common_utils.create_ack((expected_sequence - 1) % 256)
                                client_socket.sendall(last_ack)
                        elif protocolo == "SR":
                            if seq_num not in received_packets:
                                received_packets[seq_num] = data
                                print(f"Pacote armazenado (SR) Seq={seq_num}.")

                            ack = common_utils.create_ack(seq_num)
                            client_socket.sendall(ack)
                            print(f"ACK individual enviado para Seq={seq_num}")

                    except Exception as e:
                        print(f"Erro na recepção do pacote: {e}")
                        break

                if protocolo == "SR":
                    for i in sorted(received_packets.keys()):
                        full_message += received_packets[i]

                print(f"\nMensagem completa recebida do cliente: {full_message}")

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
