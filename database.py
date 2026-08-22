import json
import math
import sqlite3
import ollama

DB_NAME = "chatbot.db"

EMBED_MODEL = "nomic-embed-text"

LIMIAR_RECUPERACAO = 0.55
LIMIAR_DUPLICADO = 0.88


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
            categoria TEXT,
            embedding TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migrações para bases já existentes
    colunas = {
        row[1]
        for row in cursor.execute("PRAGMA table_info(memorias)")
    }

    if "categoria" not in colunas:
        cursor.execute(
            "ALTER TABLE memorias ADD COLUMN categoria TEXT"
        )

    if "embedding" not in colunas:
        cursor.execute(
            "ALTER TABLE memorias ADD COLUMN embedding TEXT"
        )

    if "updated_at" not in colunas:
        cursor.execute(
            "ALTER TABLE memorias ADD COLUMN updated_at DATETIME"
        )

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


def carregar_todas_memorias():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, content, categoria, embedding
        FROM memorias
        WHERE embedding IS NOT NULL
    """)

    linhas = cursor.fetchall()
    conn.close()

    return linhas


def procurar_memoria_mais_semelhante(texto):
    embedding_novo = gerar_embedding(texto)

    memorias = carregar_todas_memorias()

    melhor = None
    melhor_similaridade = -1

    for memoria_id, content, categoria, embedding_json in memorias:
        embedding_memoria = json.loads(
            embedding_json
        )

        similaridade = similaridade_cosseno(
            embedding_novo,
            embedding_memoria
        )

        if similaridade > melhor_similaridade:
            melhor_similaridade = similaridade

            melhor = {
                "id": memoria_id,
                "content": content,
                "categoria": categoria,
                "similaridade": similaridade
            }

    return melhor


def guardar_ou_actualizar_memoria(content, categoria):
    embedding = gerar_embedding(content)

    memoria_existente = procurar_memoria_mais_semelhante(
        content
    )

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if (
        memoria_existente
        and memoria_existente["similaridade"] >= LIMIAR_DUPLICADO
    ):
        cursor.execute(
            """
            UPDATE memorias
            SET content = ?,
                categoria = ?,
                embedding = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                content,
                categoria,
                json.dumps(embedding),
                memoria_existente["id"]
            )
        )

        resultado = "actualizada"

    else:
        cursor.execute(
            """
            INSERT INTO memorias (
                content,
                categoria,
                embedding
            )
            VALUES (?, ?, ?)
            """,
            (
                content,
                categoria,
                json.dumps(embedding)
            )
        )

        resultado = "criada"

    conn.commit()
    conn.close()

    return resultado


def procurar_memorias(
    texto,
    limite=5,
    limiar=LIMIAR_RECUPERACAO
):
    embedding_pergunta = gerar_embedding(texto)

    memorias = carregar_todas_memorias()

    resultados = []

    for memoria_id, content, categoria, embedding_json in memorias:
        embedding_memoria = json.loads(
            embedding_json
        )

        similaridade = similaridade_cosseno(
            embedding_pergunta,
            embedding_memoria
        )

        if similaridade >= limiar:
            resultados.append(
                {
                    "id": memoria_id,
                    "content": content,
                    "categoria": categoria,
                    "similaridade": similaridade
                }
            )

    resultados.sort(
        key=lambda item: item["similaridade"],
        reverse=True
    )

    return resultados[:limite]
