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

<img src="assets/img/baghdad arc v1.1.png" />

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

O Gemma é uma família de modelos desenvolvida pela Google.

A versão **4B** foi escolhida por proporcionar um equilíbrio adequado entre:

* qualidade de conversação;
* suporte multilingue;
* tamanho;
* consumo de RAM;
* desempenho em CPU;
* capacidade da máquina utilizada no desenvolvimento.

---

### 🐍 Aplicação Python

A lógica principal do assistente está implementada em Python.

A aplicação é responsável por coordenar os diferentes componentes do sistema.

Actualmente inclui:

* interface de terminal;
* gestão do histórico da conversa;
* extracção de memórias;
* persistência das mensagens.

---

## 🧠 Memória

A Baghdad possui actualmente dois níveis principais de memória.

#### Memória de contexto

Mantém a continuidade da conversa durante a execução do chatbot.

#### Memória persistente

As mensagens são armazenadas numa base de dados SQLite.

Isso permite que o histórico continue disponível mesmo depois de a aplicação ser encerrada.

#### Memória de longo prazo

Além do histórico completo, o sistema consegue extrair informações consideradas úteis para conversas futuras.

Exemplo:

```text
Mensagem: O meu carro preferido é Toyota Land Cruiser.
```

Pode gerar a memória:

```text
preferencia | O utilizador prefere Toyota Land Cruiser.
```

As memórias podem ser classificadas em categorias como:

* `preferencia`;
* `facto`;
* `objectivo`;
* `projecto`;
* `outro`.

Cada memória possui também um embedding que permite efectuar pesquisas semânticas.

---

## 🔎 Embeddings e recuperação semântica

Para a geração de embeddings é utilizado:

```text
nomic-embed-text
```

Ao contrário do Gemma, este modelo não é utilizado para conversar.

A sua função é transformar texto em vectores numéricos que representam aproximadamente o seu significado.

Exemplo:

```text
"O meu carro preferido é o Land Cruiser."
```

é convertido num vector semelhante a:

```text
[0.021, -0.144, 0.532, ...]
```

Quando o utilizador faz uma nova pergunta, também é criado um embedding.

Os vectores são então comparados através de **similaridade de cosseno**.

Isto permite que o assistente encontre relações semânticas mesmo quando as palavras utilizadas são diferentes.

Por exemplo:

```text
Memória: O utilizador prefere Toyota Land Cruiser.

Pergunta: Qual é o meu jipe favorito?
```

A pesquisa tradicional por palavras poderia falhar.

A pesquisa semântica consegue identificar que as duas frases possuem significados relacionados.

---

## 🗄️ SQLite

O SQLite é utilizado para persistência local.

Actualmente existem duas estruturas principais:

### Tabela `mensagens`

Responsável pelo histórico da conversa.

Campos principais:

```text
id
role
content
created_at
```

### Tabela `memorias`

Responsável pela memória de longo prazo.

Campos principais:

```text
id
content
categoria
embedding
created_at
updated_at
```

A memória inclui mecanismos básicos para:

* detectar memórias semelhantes;
* reduzir duplicações;
* actualizar informações existentes;
* recuperar apenas memórias com relevância suficiente.

---

## 🔄 Fluxo actual de uma mensagem

Quando o utilizador envia uma mensagem, o sistema executa aproximadamente o seguinte fluxo:

```text
1. Utilizador envia mensagem
            │
            ▼
2. Python gera embedding da pergunta
            │
            ▼
3. Memórias são pesquisadas por similaridade
            │
            ▼
4. Memórias relevantes são adicionadas ao contexto
            │
            ▼
5. Gemma gera a resposta
            │
            ▼
6. Pergunta e resposta são armazenadas no SQLite
            │
            ▼
7. Gemma analisa se a mensagem contém algo a memorizar
            │
            ▼
8. Se necessário:
      ├── cria nova memória
      └── ou actualiza memória semelhante
```
