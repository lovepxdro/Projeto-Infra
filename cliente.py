import socket

host = socket.gethostname()
port = 8001
address = (host, port)


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(address)


tamanho_maximo = "1024"
modo_operacao = "padrao"
mensagem_handshake = f"HANDSHAKE|{modo_operacao}|{tamanho_maximo}"
sock.send(mensagem_handshake.encode())


resposta = sock.recv(1024).decode()
print("Resposta do servidor:", resposta)

sock.close()