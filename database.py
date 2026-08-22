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

    conn.commit()
    conn.close()


def guardar_mensagem(role, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO mensagens (role, content) VALUES (?, ?)",
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
