import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
import time

# --- 1. CONFIGURAÇÃO E CSS ---
st.set_page_config(page_title="JV PERFORMANCE", page_icon="💪", layout="centered")

# URL e Email Mestre
URL_PLANILHA = "SUA_URL_AQUI"
EMAIL_COACH = "jaaovictor96@gmail.com"

conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Space+Grotesk:wght@700;900&display=swap');
    .stApp { background-color: #131313; color: #e5e2e1; }
    .main-title { color: #F9C03D !important; font-family: 'Space Grotesk', sans-serif !important; font-weight: 900 !important; text-align: center !important; text-transform: uppercase; font-size: 2.5rem !important; }
    .exercise-card { background-color: #201f1f; padding: 20px; border-radius: 12px; border-left: 4px solid #F9C03D; margin-bottom: 15px; }
    div.stButton > button { background-color: transparent !important; color: #ffffff !important; border: 1px solid #ffffff !important; border-radius: 8px; width: 100%; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNÇÃO: TELA DO ALUNO (TREINO) ---
def mostrar_tela_treino():
    st.markdown("<h1 class='main-title' style='font-size: 1.5rem !important; text-align: left !important;'>JV PERFORMANCE</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='font-family: Space Grotesk; font-size: 2.5rem; font-weight: 900; line-height: 1;'>PROTOCOLO <br><span style='color: #F9C03D;'>DIÁRIO</span></h2>", unsafe_allow_html=True)
    
    if st.button("🔄 ATUALIZAR PLANILHA"):
        st.cache_data.clear()
        st.rerun()

    try:
        df_treinos = conn.read(worksheet="planilha_treinos", ttl=0)
        df_treinos['email_aluno'] = df_treinos['email_aluno'].astype(str).str.strip().str.lower()
        meus_treinos = df_treinos[df_treinos['email_aluno'] == st.session_state.email]

        try:
            historico_geral = conn.read(worksheet="registros")
            historico_geral['email_aluno'] = historico_geral['email_aluno'].astype(str).str.strip().str.lower()
        except: historico_geral = pd.DataFrame()

        if meus_treinos.empty:
            st.info("Nenhum protocolo ativo.")
        else:
            treinos_disponiveis = meus_treinos['treino_nome'].unique()
            selecao_treino = st.selectbox("Selecione o treino:", treinos_disponiveis)
            exercicios = meus_treinos[meus_treinos['treino_nome'] == selecao_treino]

            with st.form("registro_cargas"):
                lista_registros = []
                for idx, row in exercicios.iterrows():
                    carga_anterior = 0.0
                    if not historico_geral.empty:
                        filtro_hist = historico_geral[(historico_geral['email_aluno'] == st.session_state.email) & (historico_geral['exercicio'] == row['exercicio'])]
                        if not filtro_hist.empty:
                            carga_anterior = float(filtro_hist.iloc[-1]['carga'])

                    st.markdown(f'<div class="exercise-card"><b>{row["exercicio"]}</b><br>Última: {carga_anterior}kg</div>', unsafe_allow_html=True)
                    
                    video_url = row.get('video_url', '') 
                    if pd.notnull(video_url) and str(video_url).startswith('http'):
                        video_embed = video_url.split('?')[0].replace('/view', '/preview').replace('/edit', '/preview')
                        with st.expander("🎬 VER EXECUÇÃO"):
                            st.components.v1.html(f'<iframe src="{video_embed}" width="100%" height="200" frameborder="0"></iframe>', height=210)

                    carga = st.number_input(f"Carga (kg) - {row['exercicio']}", key=f"kg_{idx}", value=carga_anterior)
                    lista_registros.append({"data": datetime.now().strftime("%d/%m/%Y %H:%M"), "email_aluno": st.session_state.email, "treino": selecao_treino, "exercicio": row['exercicio'], "carga": carga})

                notas = st.text_area("Notas do Atleta")
                if st.form_submit_button("FINALIZAR TREINO"):
                    df_envio = pd.DataFrame(lista_registros)
                    df_envio["comentario"] = notas
                    existente = conn.read(worksheet="registros", ttl=0)
                    df_final = pd.concat([existente, df_envio], ignore_index=True)
                    conn.update(worksheet="registros", data=df_final)
                    st.cache_data.clear()
                    st.success("✅ SALVO!")
                    time.sleep(1)
                    st.rerun()
    except Exception as e: st.error(f"Erro: {e}")

# --- 3. FUNÇÃO: TELA DO COACH (DASHBOARD) ---
def mostrar_tela_coach():
    st.markdown("<h1 class='main-title'>PAINEL DO COACH</h1>", unsafe_allow_html=True)
    st.info("Visualizando métricas e progresso dos alunos.")
    
    df_coach = conn.read(worksheet="registros", ttl=0)
    if not df_coach.empty:
        aluno_sel = st.selectbox("Selecione o Aluno:", df_coach['email_aluno'].unique())
        df_aluno = df_coach[df_coach['email_aluno'] == aluno_sel].copy()
        df_aluno['data'] = pd.to_datetime(df_aluno['data'], dayfirst=True)
        
        exercicio_sel = st.selectbox("Exercício:", df_aluno['exercicio'].unique())
        df_prog = df_aluno[df_aluno['exercicio'] == exercicio_sel].sort_values('data')
        
        fig = px.line(df_prog, x='data', y='carga', title=f'Evolução: {exercicio_sel}', markers=True)
        fig.update_traces(line_color='#F9C03D')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Sem dados na planilha de registros.")

# --- 4. LÓGICA DE LOGIN E NAVEGAÇÃO ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.email = ""

if not st.session_state.logado:
    # TELA DE LOGIN (Código original mantido aqui dentro)
    st.markdown("<h1 class='main-title'>TEAM JV FERREIRA</h1>", unsafe_allow_html=True)
    email_input = st.text_input("📧 E-mail").strip().lower()
    senha_input = st.text_input("🔒 Senha", type="password").strip()
    if st.button("ACESSAR"):
        usuarios = conn.read(worksheet="usuarios")
        if ((usuarios['email'].str.lower() == email_input) & (usuarios['senha'].astype(str) == senha_input)).any():
            st.session_state.logado = True
            st.session_state.email = email_input
            st.rerun()
else:
    # USUÁRIO LOGADO
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # Checa se é o Coach
    ativar_dashboard = False
    if st.session_state.email == EMAIL_COACH:
        st.sidebar.divider()
        ativar_dashboard = st.sidebar.checkbox("🔒 MODO COACH (Métricas)")

    # O GRANDE FINAL: ESCOLHA DE TELA
    if ativar_dashboard:
        mostrar_tela_coach()  # Se o botão estiver ligado, chama a função do Coach
    else:
        mostrar_tela_treino() # Se estiver desligado, chama a função do Aluno
