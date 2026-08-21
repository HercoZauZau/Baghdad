# Baghdad

Assistente de Inteligência Artificial interactivo, combinando um agente de IA, um avatar e hardware dedicado baseado em Raspberry Pi e outras componentes de hardware.

## 🎯 Objectivo

Construir um assistente de IA que possa funcionar localmente e evoluir gradualmente para um dispositivo físico independente.

A versão final deverá ser capaz de:

* conversar naturalmente com o utilizador;
* receber comandos por voz;
* responder através de voz;
* manter contexto e memória;
* possuir uma personalidade configurável;
* apresentar um avatar animado;
* utilizar ferramentas e serviços externos;
* funcionar num dispositivo dedicado;
* minimizar a dependência de serviços cloud.

---

## 🧩 Componentes principais

O projecto está dividido em três componentes:

### 1. 🧠 Agente de IA

Responsável pela inteligência e comportamento do sistema.

Inclui:

* processamento das mensagens do utilizador;
* geração de respostas;
* contexto da conversa;
* memória;
* personalidade e comportamento;
* integração com o avatar.

### 2. 🏗️ Infraestrutura

Responsável pelos serviços e pela arquitectura necessária para executar o agente.

Poderá incluir:

* APIs;
* serviços locais e/ou cloud;
* modelos de IA;
* armazenamento da memória;
* comunicação entre os diferentes módulos;
* **gestão de configurações e segurança**;
* monitorização do sistema.

### 3. 🖥️ Hardware

Responsável pela materialização física do assistente.

Componentes previstos:

* Raspberry Pi;
* mini tela/display;
* microfone;
* altifalante;
* alimentação;
* estrutura física;
* possíveis sensores e periféricos adicionais.

---

## 🏛️ Arquitectura técnica actual

A primeira versão da Baghdad utiliza três camadas principais:

<img src="assets/img/baghdad arc v1.png" />

---

### 🐳 Docker

O Docker é utilizado para executar o Ollama num ambiente isolado e reproduzível.

Principais vantagens:

* instalação mais limpa;
* isolamento do sistema operativo;
* facilidade de migração para outras máquinas;
* possibilidade de adicionar novos serviços futuramente.

---

### 🦙 Ollama

O Ollama funciona como o **servidor de inferência local** do projecto.

É responsável por:

* descarregar e armazenar modelos;
* carregar modelos para a memória;
* executar inferência;
* disponibilizar uma API HTTP local;

---

### 🤖 Gemma 3 4B

O primeiro modelo seleccionado para o projecto é:

```text
gemma3:4b
```

O Gemma é uma família de modelos desenvolvida pela Google.

A versão **4B** foi escolhida por proporcionar um equilíbrio adequado entre:

* qualidade de conversação;
* suporte multilingue;
* tamanho;
* consumo de RAM;
* desempenho em CPU;
* capacidade da máquina utilizada no desenvolvimento.
