import socket
from common_utils import send_message, receive_message # lógica para envio e recebimento

host = socket.gethostname()
port = 8001
address = (host, port)

sock = None
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"Conectando ao servidor {host}:{port}...")
    sock.connect(address)
    print("Conectado.")

    mensagem_para_enviar = input("Digite a mensagem para enviar ao servidor: ")
    
    print(f"Enviando mensagem: '{mensagem_para_enviar}'")
    send_message(sock, mensagem_para_enviar)
    print("Mensagem enviada.")

    print("Aguardando resposta do servidor...")
    resposta_servidor = receive_message(sock)

    if resposta_servidor is not None:
        print(f"Resposta recebida do servidor: '{resposta_servidor}'")
    else:
        print("Falha ao receber resposta ou conexão fechada pelo servidor.")

except socket.error as e:
    print(f"Erro de socket: {e}")
except Exception as e:
    print(f"Ocorreu um erro no cliente: {e}")
finally:
    if sock:
        print("Fechando socket do cliente.")
        sock.close()
    print("Cliente encerrado.")