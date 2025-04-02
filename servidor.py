import socket

host = socket.gethostname()
port = 8001
address = (host, port)

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.bind(address)
server_sock.listen(1)

print("Aguardando conexão...")
conn, client_addr = server_sock.accept()
print(f"Conectado a {client_addr}")


mensagem = conn.recv(1024).decode()
print("Mensagem recebida:", mensagem)

conn.send("HANDSHAKE_OK".encode())

conn.close()
server_sock.close()
