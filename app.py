import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="JV PERFORMANCE", page_icon="💪", layout="centered")

# URL da sua planilha
URL_PLANILHA = "SUA_URL_DO_GOOGLE_SHEETS_AQUI"

# Conexão sem cache (ttl=0) para atualizações instantâneas
conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)

# --- ESTILIZAÇÃO CSS (INTERFACE ELITE) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Space+Grotesk:wght@700;900&display=swap');

    .stApp {{ background-color: #131313; color: #e5e2e1; }}

    .main-title {{
        color: #F9C03D !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 900 !important;
        letter-spacing: -1px !important;
        text-align: center !important;
        text-transform: uppercase;
        font-size: 2.5rem !important;
        margin-bottom: 0px !important;
    }}

    .sub-title {{
        text-align: center;
        color: #888;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        letter-spacing: 2px;
        margin-bottom: 30px;
    }}

    input {{
        background-color: #201f1f !important;
        color: white !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
    }}

    /* BOTÃO DE LOGIN: BRANCO E VAZADO */
    [data-testid="stVerticalBlock"] div.stButton {{
        display: flex;
        justify-content: center !important;
        width: 100% !important;
    }}
    div.stButton > button {{
        background-color: transparent !important;
        color: #ffffff !important;
        border: 1px solid #ffffff !important;
        border-radius: 8px;
        padding: 10px 60px !important;
        font-weight: bold;
        transition: 0.3s;
        margin: 0 auto !important;
        display: block !important;
    }}
    div.stButton > button:hover {{
        background-color: #ffffff !important;
        color: #131313 !important;
    }}

    /* CARDS DE EXERCÍCIO */
    .exercise-card {{
        background-color: #201f1f;
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #F9C03D;
        margin-bottom: 15px;
    }}
    </style>
""", unsafe_allow_html=True)

if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.email = ""

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.markdown("<h1 class='main-title'>TEAM JV FERREIRA</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>AESTHETIC & PERFORMANCE LAB<br>CONSULTORIA ONLINE</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        email_input = st.text_input("📧 E-mail do Atleta", placeholder="atleta@exemplo.com")
        senha_input = st.text_input("🔒 Senha", type="password", placeholder="••••••")
        
        if st.button("ACESSAR"):
            try:
                usuarios = conn.read(worksheet="usuarios")
                usuarios['email'] = usuarios['email'].astype(str).str.strip()
                usuarios['senha'] = usuarios['senha'].astype(str).str.strip()
                
                if ((usuarios['email'] == email_input) & (usuarios['senha'] == senha_input)).any():
                    st.session_state.logado = True
                    st.session_state.email = email_input
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
            except:
                st.error("Erro de conexão.")

# --- ÁREA INTERNA ---
else:
    st.markdown("<h1 class='main-title' style='font-size: 1.5rem !important; text-align: left !important;'>JV PERFORMANCE</h1>", unsafe_allow_html=True)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    st.markdown("""
        <h2 style='font-family: Space Grotesk; font-size: 2.5rem; font-weight: 900; line-height: 1;'>
        DAILY <br><span style='color: #F9C03D;'>PROTOCOL</span>
        </h2>
    """, unsafe_allow_html=True)

    try:
        df_treinos = conn.read(worksheet="planilha_treinos")
        df_treinos['email_aluno'] = df_treinos['email_aluno'].astype(str).str.strip()
        meus_treinos = df_treinos[df_treinos['email_aluno'] == st.session_state.email]

        if meus_treinos.empty:
            st.info("Nenhum protocolo ativo.")
        else:
            treinos_disponiveis = meus_treinos['treino_nome'].unique()
            selecao_treino = st.selectbox("Selecione o treino:", treinos_disponiveis)
            exercicios = meus_treinos[meus_treinos['treino_nome'] == selecao_treino]

            with st.form("registro_cargas"):
                lista_registros = []
                
                for idx, row in exercicios.iterrows():
                    # --- LIMPEZA DE DECIMAIS PARA INTEIROS ---
                    series_int = int(float(row['series'])) if pd.notnull(row['series']) else 0
                    # Para as reps, removemos o .0 se existir, mas mantemos o texto se for intervalo (ex: 10-12)
                    reps_clean = str(row['reps']).replace('.0', '') if pd.notnull(row['reps']) else "0"

                    st.markdown(f"""
                        <div class="exercise-card">
                            <p style="color: #F9C03D; font-size: 10px; font-weight: bold; margin: 0;">{selecao_treino}</p>
                            <h4 style="margin: 5px 0; color: white; font-family: Space Grotesk; text-transform: uppercase;">{row['exercicio']}</h4>
                            <p style="color: #888; font-size: 12px; margin: 0;">META: {series_int} SÉRIES x {reps_clean} REPS</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    carga = st.number_input(f"Carga (kg) - {row['exercicio']}", key=f"kg_{idx}", step=0.5, min_value=0.0)
                    
                    lista_registros.append({
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "email_aluno": st.session_state.email,
                        "treino": selecao_treino,
                        "exercicio": row['exercicio'],
                        "carga": carga
                    })
                
                notas = st.text_area("Notas do Atleta", placeholder="Dificuldade, cansaço, etc.")
                if st.form_submit_button("FINALIZAR E ENVIAR"):
                    for r in lista_registros: r["comentario"] = notas
                    
                    registros_atuais = conn.read(worksheet="registros")
                    df_final = pd.concat([registros_atuais, pd.DataFrame(lista_registros)], ignore_index=True)
                    conn.update(worksheet="registros", data=df_final)
                    st.success("Dados enviados com sucesso!")

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
