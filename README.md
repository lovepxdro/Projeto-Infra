# Infraestrutura de Comunicação: Aplicação Cliente-Servidor

## 📚 Descrição

Este projeto consiste na implementação de um sistema de comunicação confiável entre Cliente e Servidor utilizando **sockets TCP**. O foco principal é a aplicação de técnicas de **handshake**, **controle de fluxo** (janela deslizante com Go-Back-N e Selective Repeat) e **controle de erro** (checksum, timeouts, retransmissões), conforme as especificações da disciplina de Infraestrutura de Comunicação.

O objetivo é simular uma camada de transporte robusta, capaz de lidar com perdas e corrupções de pacotes, garantindo a entrega íntegra e ordenada de mensagens.

---

## 📝 Índice

- [Infraestrutura de Comunicação: Aplicação Cliente-Servidor](#infraestrutura-de-comunicação-aplicação-cliente-servidor)
  - [📚 Descrição](#-descrição)
  - [📝 Índice](#-índice)
  - [✨ Funcionalidades Principais](#-funcionalidades-principais)
  - [📦 Entregas Realizadas (Evolução do Projeto)](#-entregas-realizadas-evolução-do-projeto)
    - [✅ Entrega 1: Conexão e Handshake](#-entrega-1-conexão-e-handshake)
    - [✅ Entrega 2: Troca Confiável de Mensagens e Janela Deslizante](#-entrega-2-troca-confiável-de-mensagens-e-janela-deslizante)
    - [✅ Entrega 3: Simulação de Falhas e Robustez](#-entrega-3-simulação-de-falhas-e-robustez)
  - [🛠️ Tecnologias Utilizadas](#️-tecnologias-utilizadas)
  - [⚙️ Pré-requisitos](#️-pré-requisitos)
  - [🚀 Como Executar](#-como-executar)
  - [📊 Relatório Simplificado do Projeto](#-relatório-simplificado-do-projeto)
    - [Desafios Enfrentados e Melhorias Implementadas](#desafios-enfrentados-e-melhorias-implementadas)
    - [Lições Aprendidas](#lições-aprendidas)
  - [👩‍💻 Membros da Equipe](#-membros-da-equipe)
  - [📜 Licença](#-licença)

---

## ✨ Funcionalidades Principais

*   **Comunicação Cliente-Servidor via Sockets TCP:** Base para toda a troca de dados.
*   **Handshake Inicial:** Estabelecimento de parâmetros da comunicação:
    *   Protocolo de operação (Go-Back-N ou Selective Repeat).
    *   Tamanho máximo de dados por pacote.
    *   Tamanho da janela de transmissão.
*   **Troca de Mensagens Confiável:**
    *   Fragmentação automática de mensagens (limite de 3 caracteres por pacote).
    *   Reconstrução ordenada das mensagens no receptor.
*   **Controle de Fluxo com Janela Deslizante:**
    *   **Go-Back-N (GBN):** ACK cumulativo; reenvio de toda a janela em caso de falha.
    *   **Selective Repeat (SR):** ACKs individuais; reenvio seletivo apenas dos pacotes perdidos/corrompidos.
*   **Controle de Erro:**
    *   **Checksum:** Verificação de integridade dos dados em pacotes e ACKs.
    *   **Timeout e Retransmissão Automática:** Pacotes não confirmados dentro do prazo são reenviados.
*   **Simulação de Falhas na Comunicação:**
    *   Perda de pacotes de dados.
    *   Corrupção de pacotes de dados (detectável via checksum).
    *   Perda de pacotes de ACK.
    *   Corrupção de pacotes de ACK (detectável via checksum).
*   **Menu Interativo:** Para configuração da simulação pelo usuário.

---

## 📦 Entregas Realizadas (Evolução do Projeto)

### ✅ Entrega 1: Conexão e Handshake

- Implementação da conexão Cliente-Servidor utilizando socket TCP.
- Desenvolvimento do **handshake inicial** para negociação dos seguintes parâmetros:
  - Protocolo de operação a ser utilizado (Go-Back-N ou Selective Repeat).
  - Tamanho máximo de dados permitido por pacote.
  - Tamanho da janela de transmissão.

### ✅ Entrega 2: Troca Confiável de Mensagens e Janela Deslizante

- Estabelecimento da **troca de mensagens de forma confiável** entre Cliente e Servidor.
- Implementação da fragmentação automática das mensagens, respeitando o limite de **3 caracteres** por pacote enviado.
- Implementação dos mecanismos de controle de janela deslizante:
  - **Go-Back-N (GBN)**: Utiliza ACK cumulativo e, em caso de falha (perda de pacote ou timeout), reenvia toda a janela de pacotes a partir do pacote perdido.
  - **Selective Repeat (SR)**: Utiliza ACKs individuais para cada pacote e, em caso de falha, reenvia apenas os pacotes específicos que foram perdidos ou corrompidos.
- Implementação de controle de **timeout** para detecção de pacotes perdidos e **retransmissão automática** dos mesmos.

### ✅ Entrega 3: Simulação de Falhas e Robustez

- Implementação de um sistema para **simular diversas falhas na comunicação**, permitindo testar o comportamento e a robustez dos protocolos implementados.
- **Tipos de Erros Simulados**:
  - **Perda de pacotes de dados**: Pacotes podem ser descartados aleatoriamente ou através de uma simulação forçada.
  - **Corrupção de pacotes de dados**: O conteúdo de um pacote é intencionalmente alterado. A corrupção é detectada no receptor através de um **checksum**.
  - **Perda de pacotes de ACK**: Pacotes de confirmação (ACKs) podem ser "perdidos" antes de chegarem ao transmissor, simulando falhas na rede no caminho de volta.
  - **Corrupção de pacotes de ACK**: ACKs podem ter seu conteúdo alterado durante o trânsito, fazendo com que sejam ignorados pelo transmissor ao falhar na verificação de checksum.
- **Mecanismos de Detecção e Recuperação de Erros**:
  - Uso de **checksum** para verificar a integridade dos dados recebidos em cada pacote e ACK.
  - Mecanismos de **timeout** que disparam a retransmissão automática dos pacotes que não foram confirmados dentro de um período esperado.
  - Comportamento de recuperação de falhas adaptado ao protocolo escolhido:
    - **Go-Back-N (GBN)**: Em caso de detecção de falha (timeout, NACK implícito pela falta de ACK cumulativo), toda a janela de transmissão é reenviada.
    - **Selective Repeat (SR)**: Apenas os pacotes individualmente perdidos, corrompidos ou cujos ACKs não foram recebidos são reenviados.

---

## 🛠️ Tecnologias Utilizadas

*   **Linguagem de Programação:** Python 3.x
*   **Bibliotecas Principais:**
    *   `socket` (para comunicação em rede TCP/IP)
    *   `random` (para simulação de perdas e corrupção)
    *   `threading` (para timeouts e operações concorrentes, se aplicável)
    *   `time` (para controle de tempo e timeouts)
    *   `zlib` (ou similar, para cálculo de checksum - ex: `crc32`)

---

## ⚙️ Pré-requisitos

*   Python 3.6 ou superior instalado.
*   Nenhuma biblioteca externa além das padrão do Python mencionadas acima é necessária.

---

## 🚀 Como Executar

1.  **Clone o repositório** (se aplicável) ou certifique-se de ter os arquivos `servidor.py` e `cliente.py` no mesmo diretório.

2.  **Inicie o servidor** em um terminal:
    ```bash
    python servidor.py
    ```

3.  **Inicie o cliente** em outro terminal:
    ```bash
    python cliente.py
    ```

4.  **Siga as instruções no menu interativo do cliente** para configurar a comunicação:
    *   Escolha o protocolo de controle de fluxo (Go-Back-N ou Selective Repeat).
    *   Defina o tamanho da janela de transmissão.
    *   Configure as opções de simulação de falhas (probabilidade de perda/corrupção de pacotes e ACKs).
    *   Envie mensagens e observe o comportamento do sistema.

---

## 📊 Relatório Simplificado do Projeto

### Desafios Enfrentados e Melhorias Implementadas

Durante o desenvolvimento, alguns desafios foram identificados e abordados para aprimorar a robustez e usabilidade do sistema:

*   **Inconsistências nos outputs durante a comunicação:**
    *   *Melhoria:* Realizar revisões no fluxo de logs e mensagens de status para tornar o acompanhamento da comunicação mais claro e preciso.
*   **Menu interativo complexo com opções não totalmente integradas:**
    *   *Melhoria:* Simplificar, focando nas configurações essenciais e garantindo que todas as opções tivessem impacto direto e testável na simulação.
*   **Duplicação na verificação de corrupção (checksum + probabilidade aleatória):**
    *   *Melhoria:* Unificar o sistema de verificação de integridade. A simulação de corrupção introduz o erro, e o mecanismo de checksum é o responsável por detectá-lo, tornando o processo mais realista.
*   **Falta de logs claros durante o fluxo de erros:**
    *   *Melhoria:* Aprimorar os logs de comunicação, especialmente durante a ocorrência e tratamento de erros, facilitando a depuração e a compreensão do comportamento dos protocolos.
*   **Correção do comportamento da janela deslizante:**
    *   *Melhoria:* Ajustes finos na lógica de avanço da janela, envio, recebimento de ACKs e tratamento de timeouts para garantir a conformidade com os protocolos GBN e SR.

### Lições Aprendidas

*   A importância de um handshake robusto para estabelecer corretamente os parâmetros da comunicação.
*   A complexidade inerente ao gerenciamento de múltiplos pacotes em trânsito e seus respectivos estados (enviado, confirmado, pendente).
*   A criticidade dos temporizadores (timeouts) para a detecção de perdas e a necessidade de um ajuste cuidadoso para evitar retransmissões desnecessárias ou demoras excessivas.
*   A diferença fundamental na complexidade de implementação e na eficiência de recuperação entre Go-Back-N e Selective Repeat.
*   A necessidade de mecanismos de detecção de erro (como checksum) para garantir a integridade dos dados, mesmo sobre um protocolo de transporte teoricamente confiável como o TCP (aqui simulamos erros *acima* do TCP, na nossa camada de aplicação).

---

## 👩‍💻 Membros da Equipe

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/lovepxdro">
        <img src="https://avatars.githubusercontent.com/lovepxdro" width="100px;" alt="Foto de Pedro Antônio"/>
        <br />
        <sub><b>Pedro Antônio</b></sub>
      </a>
      <br />
      <sub><b>✉️ pafm@cesar.school</b></sub>
    </td>
    <td align="center">
      <a href="https://github.com/the-lazy-programmer">
        <img src="https://avatars.githubusercontent.com/the-lazy-programmer" width="100px;" alt="Foto de João Marcelo"/>
        <br />
        <sub><b>João Marcelo</b></sub>
      </a>
      <br />
      <sub><b>✉️ jmpq@cesar.school</b></sub>
    </td>
    <td align="center">
      <a href="https://github.com/vitoriaregia21">
        <img src="https://avatars.githubusercontent.com/vitoriaregia21" width="100px;" alt="Foto de Vitória Régia"/>
        <br />
        <sub><b>Vitória Régia</b></sub>
      </a>
      <br />
      <sub><b>✉️ vrs@cesar.school</b></sub>
    </td>
  </tr>
</table>

---

## 📜 Licença

Este projeto é apenas para fins educacionais. Sinta-se à vontade para usar e modificar o código para aprendizado. Se for utilizá-lo como base para outros trabalhos, por favor, dê o devido crédito.

ᓚᘏᗢ
