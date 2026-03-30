import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="JV PERFORMANCE", page_icon="💪", layout="centered")

# URL da sua planilha (Mantenha a sua URL aqui)
URL_PLANILHA = "SUA_URL_DO_GOOGLE_SHEETS_AQUI"

conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)

# --- ESTILIZAÇÃO CSS (INTERFACE ELITE - MANTIDA ORIGINAL) ---
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
        text-align: center; color: #888; font-family: 'Inter', sans-serif;
        font-size: 0.8rem; letter-spacing: 2px; margin-bottom: 30px;
    }}
    input {{ background-color: #201f1f !important; color: white !important; border: 1px solid #333 !important; border-radius: 8px !important; }}
    [data-testid="stVerticalBlock"] div.stButton {{ display: flex; justify-content: center !important; width: 100% !important; }}
    div.stButton > button {{
        background-color: transparent !important; color: #ffffff !important; border: 1px solid #ffffff !important;
        border-radius: 8px; padding: 10px 60px !important; font-weight: bold; transition: 0.3s; margin: 0 auto !important; display: block !important;
    }}
    div.stButton > button:hover {{ background-color: #ffffff !important; color: #131313 !important; }}
    .exercise-card {{ background-color: #201f1f; padding: 20px; border-radius: 12px; border-left: 4px solid #F9C03D; margin-bottom: 15px; }}
    </style>
""", unsafe_allow_html=True)

if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.email = ""

# --- TELA DE LOGIN (MANTIDA ORIGINAL) ---
if not st.session_state.logado:
    st.markdown("<h1 class='main-title'>TEAM JV FERREIRA</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>AESTHETIC & PERFORMANCE LAB<br>CONSULTORIA ONLINE</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        email_input = st.text_input("📧 E-mail do Atleta", placeholder="atleta@exemplo.com").strip().lower()
        senha_input = st.text_input("🔒 Senha", type="password", placeholder="••••••").strip()
        
        if st.button("ACESSAR"):
            try:
                usuarios = conn.read(worksheet="usuarios")
                usuarios['email'] = usuarios['email'].astype(str).str.strip().str.lower()
                usuarios['senha'] = usuarios['senha'].astype(str).str.strip()
                if ((usuarios['email'] == email_input) & (usuarios['senha'] == senha_input)).any():
                    st.session_state.logado = True
                    st.session_state.email = email_input
                    st.rerun()
                else: st.error("Credenciais inválidas.")
            except: st.error("Erro de conexão.")

# --- ÁREA INTERNA (ÁREA DO ALUNO) ---
else:
    st.markdown("<h1 class='main-title' style='font-size: 1.5rem !important; text-align: left !important;'>JV PERFORMANCE</h1>", unsafe_allow_html=True)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    st.markdown("<h2 style='font-family: Space Grotesk; font-size: 2.5rem; font-weight: 900; line-height: 1;'>PROTOCOLO <br><span style='color: #F9C03D;'>DIÁRIO</span></h2>", unsafe_allow_html=True)

    try:
        df_treinos = conn.read(worksheet="planilha_treinos")
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
                
# --- DENTRO DO LOOP DE EXERCÍCIOS (for idx, row in exercicios.iterrows():) ---

                for idx, row in exercicios.iterrows():
                    # Lógica da última carga
                    carga_anterior = 0.0
                    if not historico_geral.empty:
                        filtro_hist = historico_geral[(historico_geral['email_aluno'] == st.session_state.email) & (historico_geral['exercicio'] == row['exercicio'])]
                        if not filtro_hist.empty:
                            carga_anterior = float(filtro_hist.iloc[-1]['carga'])

                    series_int = int(float(row['series'])) if pd.notnull(row['series']) else 0
                    reps_clean = str(row['reps']).replace('.0', '') if pd.notnull(row['reps']) else "0"

                    # 1. CARD DO EXERCÍCIO (Visual Elite)
                    st.markdown(f"""
                        <div class="exercise-card">
                            <p style="color: #F9C03D; font-size: 10px; font-weight: bold; margin: 0;">{selecao_treino}</p>
                            <h4 style="margin: 5px 0; color: white; font-family: Space Grotesk; text-transform: uppercase;">{row['exercicio']}</h4>
                            <p style="color: #888; font-size: 12px; margin: 0;">META: {series_int} SÉRIES x {reps_clean} REPS</p>
                            <p style="color: #F9C03D; font-size: 11px; margin-top: 5px; opacity: 0.8;">Última carga: {carga_anterior} kg</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # --- LÓGICA DO VÍDEO EMBUTIDO COM IFRAME (ROBUSTO) ---
                    video_url = row.get('video_url', '') 
                    if pd.notnull(video_url) and str(video_url).startswith('http'):
                        # Transformamos o link para o formato de PREVIEW que aceita embutimento
                        video_embed = video_url.split('?')[0].replace('/view', '/preview').replace('/edit', '/preview')
                        
                        with st.expander("🎬 VER EXECUÇÃO"):
                            # Usamos HTML para forçar o player dentro do app
                            st.components.v1.html(
                                f"""
                                <iframe src="{video_embed}" width="100%" height="200" 
                                frameborder="0" style="border-radius: 8px;" 
                                allow="autoplay"></iframe>
                                """,
                                height=210,
                            )

                    # 3. CAMPO DE CARGA
                    carga = st.number_input(f"Carga (kg) - {row['exercicio']}", key=f"kg_{idx}", step=0.5, min_value=0.0, value=carga_anterior)
                    
                    # ... (resto da lógica de lista_registros permanece igual)
                
                notas = st.text_area("Notas do Atleta", placeholder="Dificuldade, cansaço, etc.")
                if st.form_submit_button("FINALIZAR E ENVIAR"):
                    registros_atuais = conn.read(worksheet="registros")
                    for r in lista_registros: r["comentario"] = notas
                    df_final = pd.concat([registros_atuais, pd.DataFrame(lista_registros)], ignore_index=True)
                    conn.update(worksheet="registros", data=df_final)
                    st.success("Dados enviados com sucesso!")
                    st.rerun()

    except Exception as e: st.error(f"Erro ao carregar dados: {e}")
