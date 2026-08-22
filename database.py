import json
import math
import sqlite3
import ollama

DB_NAME = "chatbot.db"
EMBED_MODEL = "nomic-embed-text"


def criar_base_dados():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            embedding TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migração simples caso a tabela memorias já exista
    # sem a coluna embedding.
    try:
        cursor.execute("""
            ALTER TABLE memorias
            ADD COLUMN embedding TEXT
        """)
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def guardar_mensagem(role, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO mensagens (role, content)
        VALUES (?, ?)
        """,
        (role, content)
    )

    conn.commit()
    conn.close()


def carregar_historico():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, content
        FROM mensagens
        ORDER BY id
    """)

    linhas = cursor.fetchall()
    conn.close()

    return [
        {
            "role": role,
            "content": content
        }
        for role, content in linhas
    ]


def gerar_embedding(texto):
    response = ollama.embed(
        model=EMBED_MODEL,
        input=texto
    )

    return response["embeddings"][0]


def guardar_memoria(content):
    embedding = gerar_embedding(content)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO memorias (content, embedding)
        VALUES (?, ?)
        """,
        (
            content,
            json.dumps(embedding)
        )
    )

    conn.commit()
    conn.close()


def carregar_memorias():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT content
        FROM memorias
        ORDER BY id
    """)

    memorias = cursor.fetchall()
    conn.close()

    return [
        memoria[0]
        for memoria in memorias
    ]


def similaridade_cosseno(vector_a, vector_b):
    produto = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    norma_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    norma_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if norma_a == 0 or norma_b == 0:
        return 0

    return produto / (norma_a * norma_b)


def procurar_memorias(texto, limite=5):
    embedding_pergunta = gerar_embedding(texto)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT content, embedding
        FROM memorias
        WHERE embedding IS NOT NULL
    """)

    linhas = cursor.fetchall()
    conn.close()

    resultados = []

    for content, embedding_json in linhas:
        embedding_memoria = json.loads(
            embedding_json
        )

        similaridade = similaridade_cosseno(
            embedding_pergunta,
            embedding_memoria
        )

        resultados.append(
            (similaridade, content)
        )

    resultados.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        content
        for similaridade, content
        in resultados[:limite]
    ]
