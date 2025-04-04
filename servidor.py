import socket

host = socket.gethostname()
port = 8001
address = (host, port)

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.bind(address)
server_sock.listen(1)

tamanho_maximo = 3
resposta = "OK"

print("Aguardando conexão...")
conn, client_addr = server_sock.accept()
print(f"Conectado a {client_addr}")

mensagem = conn.recv(tamanho_maximo).decode()
print("Mensagem recebida:", mensagem)

if(mensagem[-1].isdigit() == True):
    tamanho_maximo = int(mensagem[-1])

if(len(resposta) > tamanho_maximo):
    resposta = resposta[tamanho_maximo-1]

conn.send(resposta.encode())

conn.close()
server_sock.close()
