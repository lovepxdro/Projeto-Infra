#  Projeto: Infraestrutura de Comunicação

## 📚 Descrição

Projeto de implementação de comunicação entre Cliente e Servidor via **sockets TCP**, utilizando técnicas de **handshake**, **controle de fluxo** e **controle de erro** conforme as especificações da disciplina de Infraestrutura de Comunicação.

---

## 📦 Entregas Realizadas

### ✅ Entrega 1

- Conexão Cliente-Servidor via socket TCP.
- Realização de **handshake inicial** trocando informações:
  - Protocolo de operação (Go-Back-N ou Selective Repeat).
  - Tamanho máximo de dados por pacote.
  - Tamanho da janela de transmissão.

### ✅ Entrega 2

- Estabelecimento da **troca de mensagens confiável** entre Cliente e Servidor.
- Fragmentação automática das mensagens, respeitando o limite de **3 caracteres** por pacote.
- Implementação de controle de janela deslizante:
  - **Go-Back-N**: ACK cumulativo e reenvio de toda a janela em caso de falha.
  - **Selective Repeat**: ACKs individuais e reenvio apenas dos pacotes perdidos.
- Controle de **timeout** e **retransmissão automática**.

---

# 👩‍💻 Membros da Equipe
<table>
  <tr>
    <td align="center">
      <a href="https://github.com/lovepxdro">
        <img src="https://avatars.githubusercontent.com/lovepxdro" width="100px;" alt="foto de Pedro Antônio"/>
        <br>
        <sub><b>Pedro Antônio</b></sub>
      </a>
      <br>
      <sub><b>✉️ pafm@cesar.school</b></sub>
    </td>
    <td align="center">
      <a href="https://github.com/the-lazy-programmer">
        <img src="https://avatars.githubusercontent.com/the-lazy-programmer" width="100px;" alt="foto de João Marcelo"/>
        <br>
        <sub><b>João Marcelo</b></sub>
      </a>
      <br>
      <sub><b>✉️ jmpq@cesar.school</b></sub>
    </td>
    <td align="center">
      <a href="https://github.com/vitoriaregia21">
        <img src="https://avatars.githubusercontent.com/vitoriaregia21" width="100px;" alt="foto de pablo"/>
        <br>
        <sub><b>Vitória Regia</b></sub>
      </a>
      <br>
      <sub><b>✉️ vrs@cesar.school</b></sub>
    </td>
  </tr>
</table>

ᓚᘏᗢ
