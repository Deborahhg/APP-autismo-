import os
import re
import sqlite3
import hashlib
from datetime import date, datetime
from io import BytesIO
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# PDF
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    PDF_DISPONIVEL = True
except Exception:
    PDF_DISPONIVEL = False

load_dotenv()

# =========================
# CONFIGURAÇÃO
# =========================
st.set_page_config(
    page_title="Calmi",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# ESTILO
# =========================
st.markdown("""
<style>
    .stApp {
        background-color: #F7F9FC;
    }

    .block-container {
        padding-top: 1.2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-bottom: 1.5rem !important;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #D9ECFF 0%, #EAF4FF 100%);
        border-right: 1px solid #D9E2EC;
        min-width: 320px !important;
        max-width: 320px !important;
        padding-top: 10px !important;
    }

    .sidebar-top-card {
        background: rgba(255,255,255,0.82);
        border: 1px solid #D7E6F5;
        border-radius: 18px;
        padding: 14px;
        margin-bottom: 16px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.04);
    }

    .sidebar-user {
        font-size: 16px;
        font-weight: 700;
        color: #1F2937;
        margin-bottom: 6px;
    }

    .sidebar-sub {
        font-size: 13px;
        color: #64748B;
        margin-bottom: 0;
    }

    /* CARD BRANCO DO MENU */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF !important;
        border: 1px solid #D7E6F5 !important;
        border-radius: 24px !important;
        padding: 14px !important;
        box-shadow: 0 8px 22px rgba(0,0,0,0.05) !important;
        margin-bottom: 16px !important;
    }

    .menu-title {
        font-size: 24px;
        font-weight: 700;
        color: #1F2937;
        margin-bottom: 4px;
    }

    .menu-subtitle {
        font-size: 13px;
        color: #64748B;
        margin-bottom: 14px;
    }

    .menu-divider {
        height: 1px;
        background: #DCE7F2;
        margin: 8px 0 14px 0;
    }

    .main-header {
        background: white;
        padding: 22px;
        border-radius: 22px;
        border: 1px solid #E5EAF1;
        box-shadow: 0 8px 24px rgba(0,0,0,0.05);
        margin-bottom: 18px;
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

    .prof-card {
        background: white;
        border: 1px solid #E5EAF1;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.04);
        margin-bottom: 12px;
    }

    .prof-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 6px;
        color: #111827;
    }

    .prof-line {
        color: #4B5563;
        margin-bottom: 4px;
        font-size: 14px;
    }

    .assistente-alert {
        background: #EAF4FF;
        padding: 18px;
        border-radius: 14px;
        margin-bottom: 20px;
        color: #2B5A8A;
        border: 1px solid #D9EAFE;
    }

    .welcome-banner {
        background: linear-gradient(90deg, #2563EB 0%, #3B82F6 100%);
        color: white;
        padding: 18px 22px;
        border-radius: 18px;
        margin-bottom: 18px;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.18);
        border: none;
    }

    .welcome-title {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .welcome-subtitle {
        font-size: 14px;
        opacity: 0.95;
    }

    .section-title {
        font-size: 24px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 6px;
    }

    .section-subtitle {
        font-size: 14px;
        color: #6B7280;
        margin-bottom: 18px;
    }

    .soft-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #FBFDFF 100%);
        border: 1px solid #E6EDF5;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        margin-bottom: 16px;
    }

    .mini-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 999px;
        background: #EFF6FF;
        color: #1D4ED8;
        font-size: 12px;
        font-weight: 700;
        margin-bottom: 10px;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="select"] > div,
    div[data-testid="stDateInputField"] {
        border-radius: 12px !important;
    }

    /* BOTÕES DO MENU */
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
        width: 100%;
        min-height: 46px;
        border-radius: 14px !important;
        border: none !important;
        background: transparent !important;
        color: #1F2937 !important;
        text-align: left !important;
        font-weight: 600 !important;
        padding: 12px 14px !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
        background: #F3F7FB !important;
    }

    /* BOTÃO VERMELHO DO ASSISTENTE IA */
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] {
        background: #D94B5C !important;
        color: white !important;
        text-align: left !important;
        font-weight: 700 !important;
        border-radius: 14px !important;
        border: none !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"]:hover {
        background: #C73E50 !important;
        color: white !important;
    }

    .btn-logout button {
        background: rgba(255,255,255,0.82) !important;
        border: 1px solid #D7E6F5 !important;
        color: #1F2937 !important;
        text-align: center !important;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 1rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-bottom: 1rem !important;
        }

        .main-header {
            padding: 16px;
            border-radius: 16px;
        }

        section[data-testid="stSidebar"] {
            min-width: 78vw !important;
            max-width: 78vw !important;
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
    crianca_id INTEGER,
    data_registro TEXT NOT NULL,
    episodio TEXT,
    antes TEXT,
    sensibilidades TEXT,
    rotina TEXT,
    analise_ia TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (crianca_id) REFERENCES criancas(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS profissionais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    especialidade TEXT NOT NULL,
    cidade TEXT,
    estado TEXT,
    telefone TEXT,
    email TEXT,
    endereco TEXT,
    observacoes TEXT
)
""")
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
if "pagina" not in st.session_state:
    st.session_state.pagina = "Dashboard"
if "mostrar_boas_vindas" not in st.session_state:
    st.session_state.mostrar_boas_vindas = False

# =========================
# FUNÇÕES
# =========================
def gerar_hash_senha(senha: str) -> str:
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
        ORDER BY nome ASC
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
    if crianca_id:
        cursor.execute("""
            SELECT r.id, r.data_registro, c.nome, r.episodio, r.antes, r.sensibilidades, r.rotina, r.analise_ia
            FROM registros r
            LEFT JOIN criancas c ON r.crianca_id = c.id
            WHERE r.usuario_id = ? AND r.crianca_id = ?
            ORDER BY r.data_registro DESC, r.id DESC
        """, (usuario_id, crianca_id))
    else:
        cursor.execute("""
            SELECT r.id, r.data_registro, c.nome, r.episodio, r.antes, r.sensibilidades, r.rotina, r.analise_ia
            FROM registros r
            LEFT JOIN criancas c ON r.crianca_id = c.id
            WHERE r.usuario_id = ?
            ORDER BY r.data_registro DESC, r.id DESC
        """, (usuario_id,))
    return cursor.fetchall()

def cadastrar_profissional(nome, especialidade, cidade, estado, telefone, email, endereco, observacoes):
    cursor.execute("""
        INSERT INTO profissionais (
            nome, especialidade, cidade, estado, telefone, email, endereco, observacoes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (nome, especialidade, cidade, estado, telefone, email, endereco, observacoes))
    conn.commit()

def buscar_profissionais(filtro_nome="", filtro_especialidade="", filtro_cidade="", filtro_estado=""):
    query = """
        SELECT id, nome, especialidade, cidade, estado, telefone, email, endereco, observacoes
        FROM profissionais
        WHERE 1=1
    """
    params = []
    if filtro_nome.strip():
        query += " AND nome LIKE ?"
        params.append(f"%{filtro_nome.strip()}%")
    if filtro_especialidade.strip():
        query += " AND especialidade LIKE ?"
        params.append(f"%{filtro_especialidade.strip()}%")
    if filtro_cidade.strip():
        query += " AND cidade LIKE ?"
        params.append(f"%{filtro_cidade.strip()}%")
    if filtro_estado.strip():
        query += " AND estado LIKE ?"
        params.append(f"%{filtro_estado.strip()}%")
    query += " ORDER BY nome ASC"
    cursor.execute(query, params)
    return cursor.fetchall()

def gerar_links_busca_profissionais(especialidade, cidade, estado):
    texto_base = f"{especialidade} em {cidade} {estado}".strip()
    if not texto_base:
        texto_base = "profissional TEA"
    consulta_maps = quote_plus(texto_base)
    consulta_google = quote_plus(texto_base + " autismo")
    return (
        f"https://www.google.com/maps/search/{consulta_maps}",
        f"https://www.google.com/search?q={consulta_google}"
    )

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
- Seja objetivo
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
    gatilhos = extrair_secao(texto, "POSSIVEIS_GATILHOS:", ["ORIENTACOES_PRATICAS:", "SUGESTOES_DE_ROTINA:"])
    orientacoes = extrair_secao(texto, "ORIENTACOES_PRATICAS:", ["SUGESTOES_DE_ROTINA:"])
    rotina = extrair_secao(texto, "SUGESTOES_DE_ROTINA:", [])
    return {"gatilhos": gatilhos, "orientacoes": orientacoes, "rotina": rotina}

def formatar_topicos_html(texto):
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    if not linhas:
        return "<p>Não disponível.</p>"
    itens = [linha for linha in linhas if linha.startswith("-")]
    if itens:
        lista = "".join([f"<li>{linha[1:].strip()}</li>" for linha in itens])
        return f"<ul>{lista}</ul>"
    return "".join([f"<p>{linha}</p>" for linha in linhas])

def exibir_analise_topicos(texto_analise):
    secoes = organizar_analise_ia(texto_analise)

    with st.expander("🔎 Possíveis gatilhos", expanded=True):
        st.markdown(f"""
        <div class="topic-box trigger-box">
            <div class="topic-title">Possíveis gatilhos</div>
            <div class="topic-content">{formatar_topicos_html(secoes["gatilhos"])}</div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🛠️ Orientações práticas", expanded=True):
        st.markdown(f"""
        <div class="topic-box practical-box">
            <div class="topic-title">Orientações práticas</div>
            <div class="topic-content">{formatar_topicos_html(secoes["orientacoes"])}</div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📅 Sugestões de rotina", expanded=True):
        st.markdown(f"""
        <div class="topic-box routine-box">
            <div class="topic-title">Sugestões de rotina</div>
            <div class="topic-content">{formatar_topicos_html(secoes["rotina"])}</div>
        </div>
        """, unsafe_allow_html=True)

def exibir_boas_vindas():
    if st.session_state.mostrar_boas_vindas:
        st.markdown(f"""
        <div class="welcome-banner">
            <div class="welcome-title">Bem-vinda, {st.session_state.usuario_nome} ✨</div>
            <div class="welcome-subtitle">
                Que bom ter você de volta ao Calmi. Vamos acompanhar os registros com mais clareza e organização.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.mostrar_boas_vindas = False

def logout():
    st.session_state.usuario_id = None
    st.session_state.usuario_nome = None
    st.session_state.crianca_id_ativa = None
    st.session_state.pagina = "Dashboard"
    st.session_state.mostrar_boas_vindas = False

def montar_dataframe_registros(registros):
    dados = []
    for r in registros:
        _, data_r, nome_crianca_r, episodio_r, antes_r, sensibilidades_r, rotina_r, analise_r = r
        dados.append({
            "data_registro": data_r,
            "crianca": nome_crianca_r if nome_crianca_r else "Não informado",
            "episodio": episodio_r or "",
            "antes": antes_r or "",
            "sensibilidades": sensibilidades_r or "",
            "rotina": rotina_r or "",
            "analise_ia": analise_r or ""
        })
    if not dados:
        return pd.DataFrame()
    df = pd.DataFrame(dados)
    df["data_registro"] = pd.to_datetime(df["data_registro"], errors="coerce")
    return df

def exibir_metricas(df):
    total_registros = len(df)
    total_criancas = df["crianca"].nunique() if not df.empty else 0
    com_rotina = int((df["rotina"].fillna("").str.strip() != "").sum()) if not df.empty else 0
    com_sensibilidades = int((df["sensibilidades"].fillna("").str.strip() != "").sum()) if not df.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    for col, valor, label in [
        (c1, total_registros, "Registros"),
        (c2, total_criancas, "Crianças"),
        (c3, com_rotina, "Com rotina"),
        (c4, com_sensibilidades, "Com sensibilidades"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number">{valor}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

def exibir_graficos(df):
    if df.empty:
        st.info("Sem dados suficientes para gráficos.")
        return

    registros_por_dia = (
        df.groupby("data_registro").size().reset_index(name="Quantidade").sort_values("data_registro").set_index("data_registro")
    )
    st.subheader("Registros por dia")
    st.line_chart(registros_por_dia)

    registros_por_crianca = (
        df.groupby("crianca").size().reset_index(name="Quantidade").set_index("crianca")
    )
    st.subheader("Registros por criança")
    st.bar_chart(registros_por_crianca)

def gerar_pdf_relatorio(nome_usuario, crianca_nome, registros):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    y = altura - 50
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, "Relatório Calmi")
    y -= 25

    pdf.setFont("Helvetica", 11)
    pdf.drawString(40, y, f"Usuário: {nome_usuario}")
    y -= 18
    pdf.drawString(40, y, f"Criança: {crianca_nome}")
    y -= 18
    pdf.drawString(40, y, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 28

    for r in registros:
        _, data_r, nome_crianca_r, episodio_r, antes_r, sensibilidades_r, rotina_r, _ = r
        blocos = [
            f"Data: {data_r}",
            f"Criança: {nome_crianca_r or '-'}",
            f"Episódio: {episodio_r or '-'}",
            f"Antes: {antes_r or '-'}",
            f"Sensibilidades: {sensibilidades_r or '-'}",
            f"Rotina: {rotina_r or '-'}",
            "-" * 90
        ]
        for linha in blocos:
            partes = [linha[i:i+95] for i in range(0, len(linha), 95)]
            for parte in partes:
                if y < 50:
                    pdf.showPage()
                    y = altura - 50
                    pdf.setFont("Helvetica", 11)
                pdf.drawString(40, y, parte)
                y -= 15
        y -= 5

    pdf.save()
    buffer.seek(0)
    return buffer

# =========================
# TOPO
# =========================
st.markdown("""
<div class="main-header">
    <div style="display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap;">
        <div style="display:flex; align-items:center; gap:16px;">
            <div style="
                width:58px;
                height:58px;
                border-radius:16px;
                background:linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%);
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:30px;
            ">🧩</div>
            <div>
                <h2 style="margin:0; font-size:30px; color:#111827;">Calmi</h2>
                <p style="margin:4px 0 0 0; color:#6B7280; font-size:15px;">
                    Prevenindo crises, compreendendo comportamentos
                </p>
            </div>
        </div>
        <div style="
            background:#F8FAFC;
            border:1px solid #E5EAF1;
            padding:10px 14px;
            border-radius:14px;
            color:#475569;
            font-size:14px;
            font-weight:600;
        ">
            Cuidado, organização e apoio diário
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================
# LOGIN / CADASTRO
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
                st.session_state.mostrar_boas_vindas = True
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
# APP PRINCIPAL
# =========================
else:
    criancas_usuario = buscar_criancas(st.session_state.usuario_id)

    if criancas_usuario and st.session_state.crianca_id_ativa is None:
        st.session_state.crianca_id_ativa = criancas_usuario[0][0]

    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-top-card">
                <div class="sidebar-user">👤 {st.session_state.usuario_nome}</div>
                <div class="sidebar-sub">Conta conectada</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if criancas_usuario:
            opcoes = {crianca[1]: crianca[0] for crianca in criancas_usuario}
            nomes = list(opcoes.keys())
            nome_atual = nomes[0]
            for nome, cid in opcoes.items():
                if cid == st.session_state.crianca_id_ativa:
                    nome_atual = nome
                    break

            crianca_escolhida = st.selectbox(
                "Criança monitorada",
                nomes,
                index=nomes.index(nome_atual)
            )
            st.session_state.crianca_id_ativa = opcoes[crianca_escolhida]
        else:
            st.info("Cadastre uma criança no perfil para começar.")

        with st.container(border=True):
            st.markdown('<div class="menu-title">Menu</div>', unsafe_allow_html=True)
            st.markdown('<div class="menu-subtitle">Navegue pelas áreas do app</div>', unsafe_allow_html=True)
            st.markdown('<div class="menu-divider"></div>', unsafe_allow_html=True)

            if st.button("📊   Dashboard", key="menu_dashboard", use_container_width=True):
                st.session_state.pagina = "Dashboard"

            if st.button("📝   Registrar comportamento", key="menu_registrar", use_container_width=True):
                st.session_state.pagina = "Registrar comportamento"

            if st.button("💡   Análise de gatilhos", key="menu_gatilhos", use_container_width=True):
                st.session_state.pagina = "Análise de gatilhos"

            if st.button("⚠️   Previsão de crises", key="menu_previsao", use_container_width=True):
                st.session_state.pagina = "Previsão de crises"

            if st.button("📄   Relatório", key="menu_relatorio", use_container_width=True):
                st.session_state.pagina = "Relatório"

            if st.button("👩‍⚕️   Buscar profissionais", key="menu_profissionais", use_container_width=True):
                st.session_state.pagina = "Buscar profissionais"

            if st.button("👤   Perfil", key="menu_perfil", use_container_width=True):
                st.session_state.pagina = "Perfil"

            if st.button("🤖 Assistente IA", key="menu_ia", type="primary", use_container_width=True):
                st.session_state.pagina = "Assistente IA"

        st.markdown('<div class="btn-logout">', unsafe_allow_html=True)
        if st.button("🚪 Sair", key="menu_sair", use_container_width=True):
            logout()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    pagina = st.session_state.pagina
    exibir_boas_vindas()

    # DASHBOARD
    if pagina == "Dashboard":
        registros = buscar_registros(st.session_state.usuario_id)

        st.markdown("""
        <div class="soft-card">
            <div class="mini-badge">VISÃO GERAL</div>
            <div class="section-title">Dashboard</div>
            <div class="section-subtitle">
                Acompanhe os registros, identifique padrões e visualize informações importantes de forma simples.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not registros:
            st.markdown("""
            <div class="highlight-box blue-box">
                <strong>📊 Nenhum registro encontrado</strong><br>
                Comece registrando comportamentos para desbloquear análises, gráficos e relatórios.
            </div>
            """, unsafe_allow_html=True)
        else:
            df_registros = montar_dataframe_registros(registros)

            st.markdown("""
            <div class="highlight-box blue-box">
                <strong>📈 Acompanhamento inteligente</strong><br>
                Veja abaixo os indicadores principais da rotina monitorada.
            </div>
            """, unsafe_allow_html=True)

            exibir_metricas(df_registros)
            st.markdown("---")
            exibir_graficos(df_registros)

    # REGISTRAR COMPORTAMENTO
    elif pagina == "Registrar comportamento":
        st.subheader("Registrar comportamento")

        st.markdown("""
        <div class="highlight-box green-box">
            <strong>📝 Novo registro</strong><br>
            Preencha as informações do dia e gere uma análise com IA.
        </div>
        """, unsafe_allow_html=True)

        if not criancas_usuario:
            st.warning("Cadastre uma criança primeiro na aba Perfil.")
        else:
            crianca_nome = next((c[1] for c in criancas_usuario if c[0] == st.session_state.crianca_id_ativa), "-")
            st.info(f"Registrando para: **{crianca_nome}**")

            data_registro = st.date_input("Data", value=date.today())
            episodio = st.text_area("O que aconteceu durante a crise?")
            antes = st.text_area("O que aconteceu antes?")
            sensibilidades = st.text_area("Quais sensibilidades a criança tem?")
            rotina = st.text_area("Observações sobre a rotina")

            if st.button("📌 Analisar e salvar"):
                if not episodio.strip():
                    st.warning("Preencha pelo menos o campo do episódio.")
                else:
                    try:
                        with st.spinner("Analisando com IA..."):
                            analise = analisar_com_ia(episodio, antes, sensibilidades, rotina)

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
                        exibir_analise_topicos(analise)
                    except Exception as e:
                        st.error("Erro ao analisar com IA.")
                        st.code(str(e))

    # ANÁLISE DE GATILHOS
    elif pagina == "Análise de gatilhos":
        st.subheader("Análise de gatilhos")

        registros = buscar_registros(st.session_state.usuario_id, st.session_state.crianca_id_ativa)

        if not registros:
            st.info("Ainda não há registros suficientes.")
        else:
            df = montar_dataframe_registros(registros)

            st.markdown("""
            <div class="highlight-box pink-box">
                <strong>💡 Padrões observados</strong><br>
                Esta área ajuda a identificar fatores que aparecem com mais frequência.
            </div>
            """, unsafe_allow_html=True)

            palavras = []
            for col in ["episodio", "antes", "sensibilidades", "rotina"]:
                if col in df.columns:
                    for texto in df[col].fillna("").tolist():
                        palavras.extend(re.findall(r"\\b[a-zA-ZÀ-ÿ]{4,}\\b", texto.lower()))

            stop = {
                "para", "com", "mais", "menos", "sobre", "antes", "depois", "durante",
                "crise", "rotina", "muito", "pouco", "teve", "estava", "quando",
                "porque", "tambem", "entre", "pelos", "pelas", "uma", "umas", "uns",
                "isso", "essa", "esse", "naquela", "aquela", "aquele"
            }
            palavras_filtradas = [p for p in palavras if p not in stop]

            if palavras_filtradas:
                freq = pd.Series(palavras_filtradas).value_counts().head(10)
                st.subheader("Palavras mais frequentes")
                st.bar_chart(freq)
            else:
                st.info("Não foi possível identificar palavras frequentes ainda.")

            st.subheader("Últimas análises geradas")
            for r in registros[:5]:
                _, data_r, nome_crianca_r, _, _, _, _, analise_r = r
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.write(f"**Data:** {data_r}")
                st.write(f"**Criança:** {nome_crianca_r}")
                if analise_r:
                    exibir_analise_topicos(analise_r)
                else:
                    st.info("Sem análise IA.")
                st.markdown("</div>", unsafe_allow_html=True)

    # PREVISÃO DE CRISES
    elif pagina == "Previsão de crises":
        st.subheader("Previsão de crises")

        registros = buscar_registros(st.session_state.usuario_id, st.session_state.crianca_id_ativa)

        st.markdown("""
        <div class="highlight-box yellow-box">
            <strong>⚠️ Indicador de atenção</strong><br>
            Esta previsão é apenas um apoio simples com base nos registros anteriores.
        </div>
        """, unsafe_allow_html=True)

        if len(registros) < 3:
            st.info("São necessários mais registros para uma previsão simples.")
        else:
            ultimos = registros[:5]
            score = 0

            for r in ultimos:
                _, _, _, episodio_r, antes_r, sensibilidades_r, rotina_r, _ = r
                texto = " ".join([
                    episodio_r or "", antes_r or "", sensibilidades_r or "", rotina_r or ""
                ]).lower()

                gatilhos_risco = [
                    "barulho", "mudança", "mudanca", "supermercado", "agitado",
                    "sono", "cansado", "lotado", "espera", "frustração", "frustracao"
                ]
                for g in gatilhos_risco:
                    if g in texto:
                        score += 1

            if score >= 8:
                st.error("Risco mais elevado observado nos últimos registros.")
            elif score >= 4:
                st.warning("Risco moderado observado nos últimos registros.")
            else:
                st.success("Risco mais baixo com base nos registros recentes.")

            st.write(f"Pontuação observada: **{score}**")

    # RELATÓRIO
    elif pagina == "Relatório":
        st.subheader("Relatório")

        filtro_id = st.session_state.crianca_id_ativa
        registros = buscar_registros(st.session_state.usuario_id, filtro_id)

        crianca_nome = "Todas"
        if filtro_id and criancas_usuario:
            crianca_nome = next((c[1] for c in criancas_usuario if c[0] == filtro_id), "Selecionada")

        st.markdown("""
        <div class="highlight-box blue-box">
            <strong>📄 Exportação</strong><br>
            Gere um relatório com os registros salvos e exporte em PDF.
        </div>
        """, unsafe_allow_html=True)

        if not registros:
            st.info("Não há registros para gerar relatório.")
        else:
            df = montar_dataframe_registros(registros)
            exibir_metricas(df)
            st.dataframe(df, use_container_width=True)

            if PDF_DISPONIVEL:
                pdf_buffer = gerar_pdf_relatorio(
                    st.session_state.usuario_nome,
                    crianca_nome,
                    registros
                )
                st.download_button(
                    "📥 Exportar PDF",
                    data=pdf_buffer,
                    file_name=f"relatorio_calmi_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("Biblioteca de PDF não encontrada. Instale reportlab para exportar em PDF.")

    # BUSCAR PROFISSIONAIS
    elif pagina == "Buscar profissionais":
        st.subheader("Buscar profissionais")

        st.markdown("""
        <div class="highlight-box blue-box">
            <strong>👩‍⚕️ Rede de apoio</strong><br>
            Pesquise profissionais cadastrados no app ou abra uma busca externa.
        </div>
        """, unsafe_allow_html=True)

        aba_busca, aba_cadastro = st.tabs(["Buscar", "Cadastrar profissional"])

        with aba_busca:
            col1, col2 = st.columns(2)
            with col1:
                filtro_nome = st.text_input("Nome do profissional")
                filtro_especialidade = st.selectbox(
                    "Especialidade",
                    ["", "Psicólogo", "Psiquiatra", "Fonoaudiólogo", "Terapeuta Ocupacional", "Neuropediatra", "Pedagogo", "Psicopedagogo", "Outro"]
                )
            with col2:
                filtro_cidade = st.text_input("Cidade")
                filtro_estado = st.text_input("Estado (UF)")

            profissionais = buscar_profissionais(
                filtro_nome, filtro_especialidade, filtro_cidade, filtro_estado
            )

            st.markdown("### Resultados")
            if not profissionais:
                st.info("Nenhum profissional encontrado no cadastro local.")
            else:
                for prof in profissionais:
                    _, nome, especialidade, cidade, estado, telefone, email, endereco, observacoes = prof
                    st.markdown('<div class="prof-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="prof-title">{nome}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="prof-line"><strong>Especialidade:</strong> {especialidade}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="prof-line"><strong>Cidade/UF:</strong> {cidade or "-"} / {estado or "-"}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="prof-line"><strong>Telefone:</strong> {telefone or "-"}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="prof-line"><strong>E-mail:</strong> {email or "-"}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="prof-line"><strong>Endereço:</strong> {endereco or "-"}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="prof-line"><strong>Observações:</strong> {observacoes or "-"}</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")
            link_maps, link_google = gerar_links_busca_profissionais(
                filtro_especialidade if filtro_especialidade else "profissional TEA",
                filtro_cidade,
                filtro_estado
            )
            c1, c2 = st.columns(2)
            with c1:
                st.link_button("📍 Buscar no Google Maps", link_maps, use_container_width=True)
            with c2:
                st.link_button("🌐 Buscar no Google", link_google, use_container_width=True)

        with aba_cadastro:
            nome_prof = st.text_input("Nome do profissional", key="nome_prof")
            especialidade_prof = st.selectbox(
                "Especialidade",
                ["Psicólogo", "Psiquiatra", "Fonoaudiólogo", "Terapeuta Ocupacional", "Neuropediatra", "Pedagogo", "Psicopedagogo", "Outro"],
                key="esp_prof"
            )
            col1, col2 = st.columns(2)
            with col1:
                cidade_prof = st.text_input("Cidade", key="cidade_prof")
                telefone_prof = st.text_input("Telefone", key="telefone_prof")
                endereco_prof = st.text_input("Endereço", key="endereco_prof")
            with col2:
                estado_prof = st.text_input("Estado (UF)", key="estado_prof")
                email_prof = st.text_input("E-mail", key="email_prof")
                observacoes_prof = st.text_area("Observações", key="obs_prof")

            if st.button("Salvar profissional"):
                if not nome_prof.strip():
                    st.warning("Digite o nome do profissional.")
                else:
                    cadastrar_profissional(
                        nome_prof.strip(),
                        especialidade_prof,
                        cidade_prof.strip(),
                        estado_prof.strip(),
                        telefone_prof.strip(),
                        email_prof.strip(),
                        endereco_prof.strip(),
                        observacoes_prof.strip()
                    )
                    st.success("Profissional cadastrado com sucesso.")
                    st.rerun()

    # PERFIL
    elif pagina == "Perfil":
        st.subheader("Perfil")

        st.markdown("""
        <div class="highlight-box blue-box">
            <strong>👤 Dados da conta</strong><br>
            Aqui você vê seus dados e cadastra crianças.
        </div>
        """, unsafe_allow_html=True)

        st.write(f"**Nome:** {st.session_state.usuario_nome}")

        cursor.execute("SELECT email FROM usuarios WHERE id = ?", (st.session_state.usuario_id,))
        email_usuario = cursor.fetchone()
        if email_usuario:
            st.write(f"**E-mail:** {email_usuario[0]}")

        st.markdown("---")
        st.subheader("Cadastrar criança")

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
                    observacoes_crianca.strip()
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
                ativa = " ✅ Selecionada" if cid == st.session_state.crianca_id_ativa else ""
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.write(f"**Nome:** {nome}{ativa}")
                st.write(f"**Data de nascimento:** {nascimento or '-'}")
                st.write(f"**Observações:** {observacoes or '-'}")
                st.markdown("</div>", unsafe_allow_html=True)

    # ASSISTENTE IA
    elif pagina == "Assistente IA":
        st.subheader("Assistente IA")

        st.markdown("""
        <div class="assistente-alert">
            Este assistente utiliza inteligência artificial para fornecer orientações gerais.<br><br>
            ⚠️ Não substitui profissionais de saúde.
        </div>
        """, unsafe_allow_html=True)

        texto = st.text_area("Descreva a situação", height=180)

        if st.button("Conversar com IA"):
            if texto.strip():
                try:
                    with st.spinner("Analisando..."):
                        resposta = analisar_com_ia(texto, "", "", "")
                    exibir_analise_topicos(resposta)
                except Exception as e:
                    st.error("Erro ao consultar a IA.")
                    st.code(str(e))
            else:
                st.warning("Descreva a situação primeiro.")