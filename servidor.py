import socket
from common_utils import send_message, receive_message # lógica para envio e recebimento da mensagem

host = socket.gethostname()
port = 8001
address = (host, port)

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
server_sock.bind(address)
server_sock.listen(1)

print(f"Servidor escutando em {host}:{port}")

conn = None
try:
    print("Aguardando conexão...")
    conn, client_addr = server_sock.accept()
    print(f"Conectado a {client_addr}")

    print("Aguardando mensagem do cliente...")
    mensagem_recebida = receive_message(conn)

    if mensagem_recebida is not None:
        print(f"Mensagem recebida ({len(mensagem_recebida)} bytes): '{mensagem_recebida}'")

        resposta = f"Servidor recebeu sua mensagem: '{mensagem_recebida}'"
        print(f"Enviando resposta: '{resposta}'")
        send_message(conn, resposta)
        print("Resposta enviada.")
    else:
        print("Falha ao receber mensagem ou conexão fechada pelo cliente.")

except Exception as e:
    print(f"Ocorreu um erro no servidor: {e}")

finally:
    if conn:
        print("Fechando conexão com o cliente.")
        conn.close()
    print("Fechando socket do servidor.")
    server_sock.close()
    print("Servidor encerrado.")