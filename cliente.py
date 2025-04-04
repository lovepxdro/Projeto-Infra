import socket

host = socket.gethostname()
port = 8001
address = (host, port)


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(address)

tamanho_maximo = 2
tamanho_operacao = 3
modo_operacao = "GBN"
selecionado = 0

while(selecionado == 0):
    modo_operacao = input("Qual será o modo de operação?: ")
    if(modo_operacao.upper() == "GO-BACK-N" or "GOBACKN" or "BACKN" or "BACK-N" or "GBN" or "GB" or "BN" or "G"):
        modo_operacao = "GBN"
        selecionado = 1
        break
    elif(modo_operacao.upper() == "REPETIÇÃO" or "REPETION" or "REPETIÇÃO SELETIVA" or "SELECTIVE REPEAT" or "REPETE" or "REPEAT" or "SR" or "S" or "R"):
        modo_operacao = "SR"
        selecionado = 1
        break
    else:
        print("Isto não é um modo válido! Por favor tente novamente")

selecionado = 0
tamanho_operacao = int(input(f"Qual será o tamanho da mensagem? (Uma caractér será reservada para o número do tamanho em sí) (Máximo: {tamanho_maximo})  "))

while(selecionado == 0):
    if(tamanho_operacao > tamanho_maximo):
        print(f"Tamanho máximo excedido! Por favor retorne um tamanho válido")
    elif(tamanho_operacao <= 0):
        print(f"Tamanho não pode ser menor que ou igual a 0! Por favor retorne um tamanho válido")
    else:
        selecionado = 1
        break
    tamanho_operacao = int(input(f"Qual será o tamanho da mensagem? (Máximo: {tamanho_maximo})  "))

if(len(modo_operacao) > tamanho_operacao):
    modo_operacao = modo_operacao[0:tamanho_operacao]

mensagem_handshake = f"{modo_operacao}{tamanho_operacao+1}"
sock.send(mensagem_handshake.encode())

resposta = sock.recv(tamanho_maximo+1).decode()
print("Resposta do servidor:", resposta)

sock.close()