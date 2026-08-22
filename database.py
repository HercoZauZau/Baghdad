import sqlite3

DB_NAME = "chatbot.db"


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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

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


def guardar_memoria(content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO memorias (content)
        VALUES (?)
        """,
        (content,)
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


def procurar_memorias(texto, limite=5):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    palavras = texto.lower().split()

    if not palavras:
        conn.close()
        return []

    condicoes = " OR ".join(
        ["LOWER(content) LIKE ?" for _ in palavras]
    )

    parametros = [
        f"%{palavra}%"
        for palavra in palavras
    ]

    query = f"""
        SELECT content
        FROM memorias
        WHERE {condicoes}
        ORDER BY id DESC
        LIMIT ?
    """

    parametros.append(limite)

    cursor.execute(
        query,
        parametros
    )

    resultados = cursor.fetchall()

    conn.close()

    return [
        resultado[0]
        for resultado in resultados
    ]
