import os
from dotenv import load_dotenv
import sqlite3
import hashlib
from datetime import date

import streamlit as st
from openai import OpenAI

load_dotenv()

# =========================
# CONFIGURAÇÃO
# =========================
st.set_page_config(
    page_title="Assistente TEA",
    page_icon="🧠",
    layout="wide"
)

# =========================
# ESTILO
# =========================
st.markdown("""
<style>
    .stApp {
        background-color: #F7F9FC;
    }

    h1, h2, h3 {
        color: #1F2937;
    }

    section[data-testid="stSidebar"] {
        background-color: #EEF2F7;
        border-right: 1px solid #D9E2EC;
    }

    .card {
        background: white;
        padding: 20px;
        border-radius: 18px;
        border: 1px solid #E5EAF1;
        box-shadow: 0 4px 14px rgba(0,0,0,0.06);
        margin-bottom: 16px;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="select"] > div {
        border-radius: 12px !important;
    }

    .small-text {
        color: #6B7280;
        font-size: 14px;
    }

    .menu-title {
        font-size: 14px;
        font-weight: 600;
        color: #4B5563;
        margin-bottom: 8px;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# BANCO DE DADOS
# =========================
conn = sqlite3.connect("app_autismo.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS criancas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    data_nascimento TEXT,
    observacoes TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    data_registro TEXT NOT NULL,
    episodio TEXT,
    antes TEXT,
    sensibilidades TEXT,
    rotina TEXT,
    analise_ia TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
)
""")
conn.commit()

# =========================
# MIGRAÇÃO DO BANCO
# =========================
cursor.execute("PRAGMA table_info(registros)")
colunas_registros = [coluna[1] for coluna in cursor.fetchall()]

if "crianca_id" not in colunas_registros:
    cursor.execute("ALTER TABLE registros ADD COLUMN crianca_id INTEGER")
    conn.commit()

cursor.execute("PRAGMA table_info(criancas)")
colunas_criancas = [coluna[1] for coluna in cursor.fetchall()]

if not colunas_criancas:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS criancas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        data_nascimento TEXT,
        observacoes TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    """)
    conn.commit()

# cria uma criança padrão para usuários que já tinham registros antigos
cursor.execute("SELECT id, nome FROM usuarios")
usuarios_existentes = cursor.fetchall()

for usuario_id_existente, nome_usuario_existente in usuarios_existentes:
    cursor.execute(
        "SELECT id FROM criancas WHERE usuario_id = ? LIMIT 1",
        (usuario_id_existente,)
    )
    crianca_existente = cursor.fetchone()

    if not crianca_existente:
        cursor.execute("""
            INSERT INTO criancas (usuario_id, nome, data_nascimento, observacoes)
            VALUES (?, ?, ?, ?)
        """, (
            usuario_id_existente,
            "Criança 1",
            None,
            f"Criança criada automaticamente para registros antigos de {nome_usuario_existente}"
        ))
        conn.commit()

# vincula registros antigos à primeira criança do usuário
cursor.execute("""
    SELECT id, usuario_id
    FROM registros
    WHERE crianca_id IS NULL
""")
registros_sem_crianca = cursor.fetchall()

for registro_id, usuario_id_registro in registros_sem_crianca:
    cursor.execute("""
        SELECT id
        FROM criancas
        WHERE usuario_id = ?
        ORDER BY id ASC
        LIMIT 1
    """, (usuario_id_registro,))
    primeira_crianca = cursor.fetchone()

    if primeira_crianca:
        cursor.execute("""
            UPDATE registros
            SET crianca_id = ?
            WHERE id = ?
        """, (primeira_crianca[0], registro_id))
        conn.commit()

# =========================
# SESSÃO
# =========================
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None

if "usuario_nome" not in st.session_state:
    st.session_state.usuario_nome = None

if "crianca_id_ativa" not in st.session_state:
    st.session_state.crianca_id_ativa = None

# =========================
# FUNÇÕES
# =========================
def gerar_hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def cadastrar_usuario(nome, email, senha):
    try:
        senha_hash = gerar_hash_senha(senha)
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
            (nome, email, senha_hash)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def autenticar_usuario(email, senha):
    senha_hash = gerar_hash_senha(senha)
    cursor.execute(
        "SELECT id, nome FROM usuarios WHERE email = ? AND senha = ?",
        (email, senha_hash)
    )
    return cursor.fetchone()


def cadastrar_crianca(usuario_id, nome, data_nascimento=None, observacoes=None):
    cursor.execute("""
        INSERT INTO criancas (usuario_id, nome, data_nascimento, observacoes)
        VALUES (?, ?, ?, ?)
    """, (usuario_id, nome, data_nascimento, observacoes))
    conn.commit()


def buscar_criancas(usuario_id):
    cursor.execute("""
        SELECT id, nome, data_nascimento, observacoes
        FROM criancas
        WHERE usuario_id = ?
        ORDER BY nome, id
    """, (usuario_id,))
    return cursor.fetchall()


def salvar_registro(usuario_id, crianca_id, data_registro, episodio, antes, sensibilidades, rotina, analise_ia):
    cursor.execute("""
        INSERT INTO registros (
            usuario_id, crianca_id, data_registro, episodio, antes, sensibilidades, rotina, analise_ia
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (usuario_id, crianca_id, data_registro, episodio, antes, sensibilidades, rotina, analise_ia))
    conn.commit()


def buscar_registros(usuario_id, crianca_id=None):
    if crianca_id is not None:
        cursor.execute("""
            SELECT r.data_registro, c.nome, r.episodio, r.antes, r.sensibilidades, r.rotina, r.analise_ia
            FROM registros r
            LEFT JOIN criancas c ON r.crianca_id = c.id
            WHERE r.usuario_id = ? AND r.crianca_id = ?
            ORDER BY r.data_registro DESC, r.id DESC
        """, (usuario_id, crianca_id))
    else:
        cursor.execute("""
            SELECT r.data_registro, c.nome, r.episodio, r.antes, r.sensibilidades, r.rotina, r.analise_ia
            FROM registros r
            LEFT JOIN criancas c ON r.crianca_id = c.id
            WHERE r.usuario_id = ?
            ORDER BY r.data_registro DESC, r.id DESC
        """, (usuario_id,))
    return cursor.fetchall()


def analisar_com_ia(episodio, antes, sensibilidades, rotina):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("A chave OPENAI_API_KEY não foi encontrada. Verifique o arquivo .env.")

    client = OpenAI(api_key=api_key)

    prompt = f"""
Você é um assistente de apoio para TEA.

Analise as respostas abaixo e organize em 3 partes:
1. Possíveis gatilhos
2. Orientações práticas
3. Sugestões de rotina para os próximos dias

Regras:
- Não faça diagnóstico
- Não diga que encontrou a causa exata
- Use linguagem simples, acolhedora e profissional
- Fale apenas em possíveis gatilhos
- Seja objetivo

Respostas:
1. O que aconteceu durante a crise: {episodio}
2. O que aconteceu antes da crise: {antes}
3. Sensibilidades da criança: {sensibilidades}
4. Observações sobre a rotina: {rotina}
"""

    resposta = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return resposta.output_text


def logout():
    st.session_state.usuario_id = None
    st.session_state.usuario_nome = None
    st.session_state.crianca_id_ativa = None


# =========================
# TOPO
# =========================
st.title("🧠 Assistente para TEA")
st.write("Registro diário, análise com IA e histórico personalizado por criança.")

# =========================
# TELA DE LOGIN/CADASTRO
# =========================
if st.session_state.usuario_id is None:
    aba1, aba2 = st.tabs(["Entrar", "Criar conta"])

    with aba1:
        st.subheader("Entrar")
        email_login = st.text_input("E-mail", key="login_email")
        senha_login = st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar"):
            usuario = autenticar_usuario(email_login, senha_login)
            if usuario:
                st.session_state.usuario_id = usuario[0]
                st.session_state.usuario_nome = usuario[1]
                st.success("Login realizado com sucesso.")
                st.rerun()
            else:
                st.error("E-mail ou senha inválidos.")

    with aba2:
        st.subheader("Criar conta")
        nome_cadastro = st.text_input("Nome completo")
        email_cadastro = st.text_input("E-mail", key="cadastro_email")
        senha_cadastro = st.text_input("Senha", type="password", key="cadastro_senha")

        if st.button("Cadastrar"):
            if nome_cadastro and email_cadastro and senha_cadastro:
                sucesso = cadastrar_usuario(nome_cadastro, email_cadastro, senha_cadastro)
                if sucesso:
                    st.success("Conta criada com sucesso. Agora faça login.")
                else:
                    st.error("Já existe uma conta com esse e-mail.")
            else:
                st.warning("Preencha todos os campos.")

# =========================
# TELA PRINCIPAL COM ABAS VERTICAIS
# =========================
else:
    criancas_usuario = buscar_criancas(st.session_state.usuario_id)

    if criancas_usuario and st.session_state.crianca_id_ativa is None:
        st.session_state.crianca_id_ativa = criancas_usuario[0][0]

    with st.sidebar:
        st.subheader(f"Olá, {st.session_state.usuario_nome} 👋")

        st.markdown('<div class="menu-title">Perfil monitorado</div>', unsafe_allow_html=True)

        if criancas_usuario:
            opcoes_criancas_sidebar = {
                f"{crianca[1]}": crianca[0]
                for crianca in criancas_usuario
            }

            nomes_sidebar = list(opcoes_criancas_sidebar.keys())
            nome_atual = None

            for nome, cid in opcoes_criancas_sidebar.items():
                if cid == st.session_state.crianca_id_ativa:
                    nome_atual = nome
                    break

            if nome_atual is None:
                nome_atual = nomes_sidebar[0]
                st.session_state.crianca_id_ativa = opcoes_criancas_sidebar[nome_atual]

            crianca_escolhida = st.selectbox(
                "Escolha a criança",
                nomes_sidebar,
                index=nomes_sidebar.index(nome_atual)
            )

            st.session_state.crianca_id_ativa = opcoes_criancas_sidebar[crianca_escolhida]
        else:
            st.info("Cadastre uma criança para começar.")

        st.markdown("---")
        st.markdown('<div class="menu-title">Navegação</div>', unsafe_allow_html=True)

        pagina = st.radio(
            "Ir para",
            ["Novo registro", "Histórico", "Crianças", "Perfil"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        if st.button("Sair", use_container_width=True):
            logout()
            st.rerun()

    if pagina == "Crianças":
        st.subheader("Cadastrar criança")

        nome_crianca = st.text_input("Nome da criança")
        data_nascimento = st.date_input("Data de nascimento", value=date.today(), key="data_nascimento_crianca")
        observacoes_crianca = st.text_area("Observações", key="obs_crianca")

        if st.button("Salvar criança"):
            if not nome_crianca.strip():
                st.warning("Digite o nome da criança.")
            else:
                cadastrar_crianca(
                    st.session_state.usuario_id,
                    nome_crianca.strip(),
                    str(data_nascimento),
                    observacoes_crianca
                )
                st.success("Criança cadastrada com sucesso.")
                st.rerun()

        st.markdown("---")
        st.subheader("Crianças cadastradas")

        criancas_lista = buscar_criancas(st.session_state.usuario_id)
        if not criancas_lista:
            st.info("Nenhuma criança cadastrada ainda.")
        else:
            for crianca in criancas_lista:
                cid, nome, nascimento, observacoes = crianca
                ativa = " ✅ Perfil em monitoramento" if cid == st.session_state.crianca_id_ativa else ""

                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.write(f"**Nome:** {nome}{ativa}")
                st.write(f"**Data de nascimento:** {nascimento if nascimento else '-'}")
                st.write(f"**Observações:** {observacoes if observacoes else '-'}")
                st.markdown("</div>", unsafe_allow_html=True)

    elif pagina == "Novo registro":
        st.subheader("Novo registro diário")

        criancas = buscar_criancas(st.session_state.usuario_id)

        if not criancas:
            st.warning("Cadastre pelo menos uma criança antes de criar um registro.")
        else:
            crianca_ativa = None
            for crianca in criancas:
                if crianca[0] == st.session_state.crianca_id_ativa:
                    crianca_ativa = crianca
                    break

            if crianca_ativa:
                st.info(f"Registrando informações para: **{crianca_ativa[1]}**")

            data_registro = st.date_input("Data", value=date.today(), key="data_registro")
            episodio = st.text_area("O que aconteceu durante a crise?")
            antes = st.text_area("O que aconteceu antes da crise?")
            sensibilidades = st.text_area("Quais sensibilidades a criança tem?")
            rotina = st.text_area("Observações sobre a rotina")

            if st.button("Analisar e salvar"):
                if not episodio.strip():
                    st.warning("Preencha pelo menos o campo do episódio.")
                elif st.session_state.crianca_id_ativa is None:
                    st.warning("Selecione uma criança para monitorar.")
                else:
                    try:
                        with st.spinner("Analisando com IA..."):
                            analise = analisar_com_ia(
                                episodio,
                                antes,
                                sensibilidades,
                                rotina
                            )

                        salvar_registro(
                            st.session_state.usuario_id,
                            st.session_state.crianca_id_ativa,
                            str(data_registro),
                            episodio,
                            antes,
                            sensibilidades,
                            rotina,
                            analise
                        )

                        st.success("Registro salvo com sucesso.")
                        st.subheader("Resultado da análise")
                        st.write(analise)

                    except Exception as e:
                        st.error("Erro ao analisar com IA.")
                        st.code(str(e))

    elif pagina == "Histórico":
        st.subheader("Histórico de registros")

        criancas = buscar_criancas(st.session_state.usuario_id)

        if not criancas:
            st.info("Nenhuma criança cadastrada ainda.")
        else:
            filtro_opcoes = {"Todas": None}
            for crianca in criancas:
                filtro_opcoes[f"{crianca[1]}"] = crianca[0]

            nome_padrao = "Todas"
            for nome, cid in filtro_opcoes.items():
                if cid == st.session_state.crianca_id_ativa:
                    nome_padrao = nome
                    break

            lista_nomes = list(filtro_opcoes.keys())

            filtro_nome = st.selectbox(
                "Filtrar por criança",
                lista_nomes,
                index=lista_nomes.index(nome_padrao)
            )

            filtro_crianca_id = filtro_opcoes[filtro_nome]
            registros = buscar_registros(st.session_state.usuario_id, filtro_crianca_id)

            if not registros:
                st.info("Ainda não há registros salvos.")
            else:
                for registro in registros:
                    data_r, nome_crianca_r, episodio_r, antes_r, sensibilidades_r, rotina_r, analise_r = registro

                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown(f"### 📅 {data_r}")
                    st.write(f"**Criança:** {nome_crianca_r if nome_crianca_r else '-'}")
                    st.write(f"**Episódio:** {episodio_r}")
                    st.write(f"**Antes da crise:** {antes_r}")
                    st.write(f"**Sensibilidades:** {sensibilidades_r}")
                    st.write(f"**Rotina:** {rotina_r}")
                    st.write("**Análise da IA:**")
                    st.write(analise_r)
                    st.markdown("</div>", unsafe_allow_html=True)

    elif pagina == "Perfil":
        st.subheader("Perfil")
        st.write(f"**Nome:** {st.session_state.usuario_nome}")

        cursor.execute(
            "SELECT email FROM usuarios WHERE id = ?",
            (st.session_state.usuario_id,)
        )
        email_usuario = cursor.fetchone()

        if email_usuario:
            st.write(f"**E-mail:** {email_usuario[0]}")

        if st.session_state.crianca_id_ativa is not None:
            criancas = buscar_criancas(st.session_state.usuario_id)
            nome_crianca_ativa = None

            for crianca in criancas:
                if crianca[0] == st.session_state.crianca_id_ativa:
                    nome_crianca_ativa = crianca[1]
                    break

            if nome_crianca_ativa:
                st.write(f"**Criança monitorada atualmente:** {nome_crianca_ativa}")

        st.markdown(
            '<p class="small-text">Os registros ficam salvos no banco local do aplicativo.</p>',
            unsafe_allow_html=True
        )