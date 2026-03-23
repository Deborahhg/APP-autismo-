import os
import re
from dotenv import load_dotenv
import sqlite3
import hashlib
from datetime import date

import pandas as pd
import streamlit as st
from openai import OpenAI

load_dotenv()

# =========================
# CONFIGURAÇÃO
# =========================
st.set_page_config(
    page_title="Assistente TEA",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
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
        width: 100%;
        box-sizing: border-box;
    }

    .highlight-box {
        padding: 16px;
        border-radius: 16px;
        margin-bottom: 14px;
        border-left: 6px solid;
        box-shadow: 0 4px 14px rgba(0,0,0,0.04);
    }

    .blue-box {
        background: #EAF4FF;
        border-left-color: #3B82F6;
    }

    .green-box {
        background: #ECFDF3;
        border-left-color: #10B981;
    }

    .yellow-box {
        background: #FFF8E6;
        border-left-color: #F59E0B;
    }

    .pink-box {
        background: #FDF2F8;
        border-left-color: #EC4899;
    }

    .metric-card {
        background: white;
        padding: 16px;
        border-radius: 16px;
        border: 1px solid #E5EAF1;
        text-align: center;
        box-shadow: 0 4px 14px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }

    .metric-number {
        font-size: 28px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 4px;
    }

    .metric-label {
        font-size: 14px;
        color: #6B7280;
    }

    .analysis-box {
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 14px;
        margin-top: 8px;
    }

    .topic-box {
        padding: 16px;
        border-radius: 16px;
        margin: 10px 0 14px 0;
        border: 1px solid #E5E7EB;
        box-shadow: 0 4px 14px rgba(0,0,0,0.05);
        background: white;
    }

    .topic-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .trigger-box {
        background: #FEF2F2;
        border-left: 6px solid #EF4444;
    }

    .practical-box {
        background: #ECFDF5;
        border-left: 6px solid #10B981;
    }

    .routine-box {
        background: #EFF6FF;
        border-left: 6px solid #3B82F6;
    }

    .topic-content {
        color: #374151;
        line-height: 1.6;
        font-size: 15px;
    }

    .topic-content ul {
        margin-top: 8px;
        padding-left: 20px;
    }

    .topic-content li {
        margin-bottom: 6px;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="select"] > div,
    div[data-testid="stDateInputField"] {
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

    .main-header {
        background: linear-gradient(135deg, #ffffff, #f3f6fb);
        padding: 18px;
        border-radius: 18px;
        border: 1px solid #E5EAF1;
        box-shadow: 0 4px 14px rgba(0,0,0,0.05);
        margin-bottom: 18px;
    }

    .mobile-info {
        font-size: 14px;
        color: #4B5563;
        background: #ffffff;
        border: 1px solid #E5EAF1;
        padding: 12px;
        border-radius: 14px;
        margin-bottom: 14px;
    }

    div[data-testid="stButton"] > button {
        border-radius: 12px !important;
        min-height: 44px;
        font-weight: 600;
        width: 100%;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 1rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-bottom: 1rem !important;
        }

        h1 {
            font-size: 1.6rem !important;
        }

        h2 {
            font-size: 1.25rem !important;
        }

        h3 {
            font-size: 1.05rem !important;
        }

        .card, .highlight-box, .metric-card, .analysis-box, .topic-box {
            padding: 14px;
            border-radius: 14px;
        }

        .main-header {
            padding: 14px;
            border-radius: 14px;
        }

        .small-text {
            font-size: 13px;
        }

        section[data-testid="stSidebar"] {
            min-width: 75vw !important;
            max-width: 75vw !important;
        }
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

Analise as respostas abaixo e responda EXATAMENTE em 3 seções, usando estes títulos:

POSSIVEIS_GATILHOS:
- item 1
- item 2

ORIENTACOES_PRATICAS:
- item 1
- item 2

SUGESTOES_DE_ROTINA:
- item 1
- item 2

Regras:
- Não faça diagnóstico
- Não diga que encontrou a causa exata
- Use linguagem simples, acolhedora e profissional
- Fale apenas em possíveis gatilhos
- Seja objetivo
- Em cada seção, traga orientações em tópicos curtos
- Não escreva nenhuma quarta seção
- Não mude os títulos

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


def extrair_secao(texto, inicio, proximos_titulos):
    padrao_fim = "|".join([re.escape(t) for t in proximos_titulos]) if proximos_titulos else r"$"
    padrao = rf"{re.escape(inicio)}\s*(.*?)(?=\n(?:{padrao_fim})|\Z)"
    match = re.search(padrao, texto, re.DOTALL | re.IGNORECASE)

    if match:
        return match.group(1).strip()
    return "Não disponível."


def organizar_analise_ia(texto):
    gatilhos = extrair_secao(
        texto,
        "POSSIVEIS_GATILHOS:",
        ["ORIENTACOES_PRATICAS:", "SUGESTOES_DE_ROTINA:"]
    )

    orientacoes = extrair_secao(
        texto,
        "ORIENTACOES_PRATICAS:",
        ["SUGESTOES_DE_ROTINA:"]
    )

    rotina = extrair_secao(
        texto,
        "SUGESTOES_DE_ROTINA:",
        []
    )

    return {
        "gatilhos": gatilhos,
        "orientacoes": orientacoes,
        "rotina": rotina
    }


def formatar_topicos_html(texto):
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]

    if not linhas:
        return "<p>Não disponível.</p>"

    possui_topicos = any(linha.startswith("-") for linha in linhas)

    textos_soltos = "".join(
        [f"<p>{linha}</p>" for linha in linhas if not linha.startswith("-")]
    )

    if possui_topicos:
        itens = "".join(
            [f"<li>{linha[1:].strip()}</li>" for linha in linhas if linha.startswith("-")]
        )
        return textos_soltos + f"<ul>{itens}</ul>"

    return "".join([f"<p>{linha}</p>" for linha in linhas])


def exibir_analise_topicos(texto_analise):
    secoes = organizar_analise_ia(texto_analise)

    with st.expander("🔎 Possíveis gatilhos", expanded=True):
        st.markdown(f"""
        <div class="topic-box trigger-box">
            <div class="topic-title">Possíveis gatilhos</div>
            <div class="topic-content">
                {formatar_topicos_html(secoes["gatilhos"])}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🛠️ Orientações práticas", expanded=True):
        st.markdown(f"""
        <div class="topic-box practical-box">
            <div class="topic-title">Orientações práticas</div>
            <div class="topic-content">
                {formatar_topicos_html(secoes["orientacoes"])}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📅 Sugestões de rotina para os próximos dias", expanded=True):
        st.markdown(f"""
        <div class="topic-box routine-box">
            <div class="topic-title">Sugestões de rotina para os próximos dias</div>
            <div class="topic-content">
                {formatar_topicos_html(secoes["rotina"])}
            </div>
        </div>
        """, unsafe_allow_html=True)


def logout():
    st.session_state.usuario_id = None
    st.session_state.usuario_nome = None
    st.session_state.crianca_id_ativa = None


def montar_dataframe_registros(registros):
    dados = []
    for registro in registros:
        data_r, nome_crianca_r, episodio_r, antes_r, sensibilidades_r, rotina_r, analise_r = registro
        dados.append({
            "data_registro": data_r,
            "crianca": nome_crianca_r if nome_crianca_r else "Não informado",
            "episodio": episodio_r if episodio_r else "",
            "antes": antes_r if antes_r else "",
            "sensibilidades": sensibilidades_r if sensibilidades_r else "",
            "rotina": rotina_r if rotina_r else "",
            "analise_ia": analise_r if analise_r else ""
        })

    if not dados:
        return pd.DataFrame()

    df = pd.DataFrame(dados)
    df["data_registro"] = pd.to_datetime(df["data_registro"], errors="coerce")
    return df


def exibir_metricas(df):
    total_registros = len(df)
    total_criancas = df["crianca"].nunique() if not df.empty else 0
    com_rotina = int((df["rotina"].str.strip() != "").sum()) if "rotina" in df.columns else 0
    com_sensibilidades = int((df["sensibilidades"].str.strip() != "").sum()) if "sensibilidades" in df.columns else 0

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{total_registros}</div>
            <div class="metric-label">Registros</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{total_criancas}</div>
            <div class="metric-label">Crianças</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{com_rotina}</div>
            <div class="metric-label">Com rotina</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{com_sensibilidades}</div>
            <div class="metric-label">Com sensibilidades</div>
        </div>
        """, unsafe_allow_html=True)


def exibir_graficos(df):
    if df.empty:
        return

    st.markdown("""
    <div class="highlight-box blue-box">
        <strong>📊 Resumo visual</strong><br>
        Abaixo você acompanha a frequência dos registros e o preenchimento das informações.
    </div>
    """, unsafe_allow_html=True)

    registros_por_dia = (
        df.groupby("data_registro")
        .size()
        .reset_index(name="Quantidade")
        .sort_values("data_registro")
        .set_index("data_registro")
    )

    st.subheader("Registros por dia")
    st.line_chart(registros_por_dia)

    registros_por_crianca = (
        df.groupby("crianca")
        .size()
        .reset_index(name="Quantidade")
        .set_index("crianca")
    )

    st.subheader("Registros por criança")
    st.bar_chart(registros_por_crianca)

    preenchimento = pd.DataFrame({
        "Campo": ["Episódio", "Antes da crise", "Sensibilidades", "Rotina", "Análise IA"],
        "Quantidade": [
            int((df["episodio"].str.strip() != "").sum()),
            int((df["antes"].str.strip() != "").sum()),
            int((df["sensibilidades"].str.strip() != "").sum()),
            int((df["rotina"].str.strip() != "").sum()),
            int((df["analise_ia"].str.strip() != "").sum()),
        ]
    }).set_index("Campo")

    st.subheader("Preenchimento dos campos")
    st.bar_chart(preenchimento)


# =========================
# TOPO
# =========================
st.markdown("""
<div class="main-header">
    <h1 style="margin-bottom: 8px;">🧠 Assistente para TEA</h1>
    <p style="margin: 0; color: #4B5563;">
        Registro diário, análise com IA e histórico personalizado por criança.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="mobile-info">
    📱 Este app também pode ser usado no celular. Abra o menu lateral para escolher a criança e navegar entre as páginas.
</div>
""", unsafe_allow_html=True)

# =========================
# TELA DE LOGIN/CADASTRO
# =========================
if st.session_state.usuario_id is None:
    aba1, aba2 = st.tabs(["Entrar", "Criar conta"])

    with aba1:
        st.subheader("Entrar")
        email_login = st.text_input("E-mail", key="login_email")
        senha_login = st.text_input("Senha", type="password", key="login_senha")

        if st.button("🔐 Entrar"):
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

        if st.button("📝 Cadastrar"):
            if nome_cadastro and email_cadastro and senha_cadastro:
                sucesso = cadastrar_usuario(nome_cadastro, email_cadastro, senha_cadastro)
                if sucesso:
                    st.success("Conta criada com sucesso. Agora faça login.")
                else:
                    st.error("Já existe uma conta com esse e-mail.")
            else:
                st.warning("Preencha todos os campos.")

# =========================
# TELA PRINCIPAL
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
            label_visibility="visible"
        )

        st.markdown("---")

        if st.button("Sair", use_container_width=True):
            logout()
            st.rerun()

    if pagina == "Crianças":
        st.subheader("Cadastrar criança")

        st.markdown("""
        <div class="highlight-box yellow-box">
            <strong>👶 Cadastro de perfil</strong><br>
            Adicione cada criança separadamente para ter um histórico mais organizado.
        </div>
        """, unsafe_allow_html=True)

        nome_crianca = st.text_input("Nome da criança")
        data_nascimento = st.date_input("Data de nascimento", value=date.today(), key="data_nascimento_crianca")
        observacoes_crianca = st.text_area("Observações", key="obs_crianca")

        if st.button("➕ Salvar criança"):
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

        st.markdown("""
        <div class="highlight-box green-box">
            <strong>📝 Registro do dia</strong><br>
            Preencha os campos com calma. Quanto mais contexto, melhor a organização do histórico e da análise.
        </div>
        """, unsafe_allow_html=True)

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

            if st.button("📌 Analisar e salvar"):
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

                        st.markdown("""
                        <div class="highlight-box blue-box">
                            <strong>🤖 Resultado da análise</strong><br>
                            Abaixo está a resposta gerada pela IA com possíveis gatilhos, orientações e sugestões.
                        </div>
                        """, unsafe_allow_html=True)

                        exibir_analise_topicos(analise)

                    except Exception as e:
                        st.error("Erro ao analisar com IA.")
                        st.code(str(e))

    elif pagina == "Histórico":
        st.subheader("Histórico de registros")

        st.markdown("""
        <div class="highlight-box pink-box">
            <strong>📚 Acompanhamento visual</strong><br>
            Aqui você encontra os registros salvos e um resumo em gráficos para facilitar a observação de padrões.
        </div>
        """, unsafe_allow_html=True)

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
                df_registros = montar_dataframe_registros(registros)

                exibir_metricas(df_registros)
                st.markdown("---")
                exibir_graficos(df_registros)
                st.markdown("---")

                st.subheader("Registros detalhados")

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

                    if analise_r:
                        exibir_analise_topicos(analise_r)
                    else:
                        st.markdown("""
                        <div class="analysis-box">
                            Nenhuma análise disponível.
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

    elif pagina == "Perfil":
        st.subheader("Perfil")

        st.markdown("""
        <div class="highlight-box blue-box">
            <strong>👤 Dados da conta</strong><br>
            Aqui você visualiza as informações básicas do seu perfil e da criança em monitoramento.
        </div>
        """, unsafe_allow_html=True)

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