import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="JV PERFORMANCE", page_icon="💪", layout="centered")

# URL da sua planilha (Mantenha a sua URL aqui)
URL_PLANILHA = "SUA_URL_DO_GOOGLE_SHEETS_AQUI"
EMAIL_COACH = "jaaovictor96@gmail.com"

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

# --- TELA DE LOGIN ---
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

# --- ÁREA INTERNA ---
else:
    # --- BARRA LATERAL (SIDEBAR) ---
    st.sidebar.markdown(f"**Logado como:**\n{st.session_state.email}")
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # Lógica de Segurança para o Painel do Coach
    ativar_dashboard = False
    if st.session_state.email == EMAIL_COACH:
        st.sidebar.divider()
        st.sidebar.subheader("🛠 PAINEL DO COACH")
        ativar_dashboard = st.sidebar.checkbox("Visualizar Métricas")

    # --- ESCOLHA DE TELA ---
    if ativar_dashboard:
        # ==========================================
        # TELA A: DASHBOARD (SOMENTE COACH)
        # ==========================================
        st.markdown("## 📊 CENTRAL DE PERFORMANCE JV")
        
        try:
            df_coach = conn.read(worksheet="registros", ttl=0)
            if not df_coach.empty:
                lista_alunos = df_coach['email_aluno'].unique()
                aluno_sel = st.selectbox("Selecione o Aluno:", lista_alunos)
                
                df_aluno = df_coach[df_coach['email_aluno'] == aluno_sel].copy()
                df_aluno['data'] = pd.to_datetime(df_aluno['data'], dayfirst=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Treinos Realizados", df_aluno['data'].dt.date.nunique())
                with col2:
                    st.metric("Última Carga", f"{df_aluno['carga'].max()} kg")

                exercicio_sel = st.selectbox("Escolha o Exercício:", df_aluno['exercicio'].unique())
                df_prog = df_aluno[df_aluno['exercicio'] == exercicio_sel].sort_values('data')
                
                fig = px.line(df_prog, x='data', y='carga', title=f'Progressão: {exercicio_sel}', markers=True)
                fig.update_traces(line_color='#F9C03D')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum registro para analisar.")
        except Exception as e:
            st.error(f"Erro no dashboard: {e}")

    else:
        # ==========================================
        # TELA B: PROTOCOLO (ALUNOS E COACH TREINANDO)
        # ==========================================
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

                        series_int = int(float(row['series'])) if pd.notnull(row['series']) else 0
                        reps_clean = str(row['reps']).replace('.0', '') if pd.notnull(row['reps']) else "0"

                        st.markdown(f"""
                            <div class="exercise-card">
                                <p style="color: #F9C03D; font-size: 10px; font-weight: bold; margin: 0;">{selecao_treino}</p>
                                <h4 style="margin: 5px 0; color: white; font-family: Space Grotesk; text-transform: uppercase;">{row['exercicio']}</h4>
                                <p style="color: #888; font-size: 12px; margin: 0;">META: {series_int} SÉRIES x {reps_clean} REPS</p>
                                <p style="color: #F9C03D; font-size: 11px; margin-top: 5px; opacity: 0.8;">Última carga: {carga_anterior} kg</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        video_url = row.get('video_url', '') 
                        if pd.notnull(video_url) and str(video_url).startswith('http'):
                            video_embed = video_url.split('?')[0].replace('/view', '/preview').replace('/edit', '/preview')
                            with st.expander("🎬 VER EXECUÇÃO"):
                                st.components.v1.html(f'<iframe src="{video_embed}" width="100%" height="200" frameborder="0" style="border-radius: 8px;" allow="autoplay"></iframe>', height=210)

                        carga = st.number_input(f"Carga (kg) - {row['exercicio']}", key=f"kg_{idx}", step=0.5, min_value=0.0, value=carga_anterior)
                    
                        lista_registros.append({
                            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "email_aluno": st.session_state.email,
                            "treino": selecao_treino,
                            "exercicio": row['exercicio'],
                            "carga": carga
                        })

                    notas = st.text_area("Notas do Atleta", placeholder="Como foi o treino hoje?")

                    if st.form_submit_button("FINALIZAR TREINO"):
                        try:
                            df_envio = pd.DataFrame(lista_registros)
                            df_envio["comentario"] = notas
                            colunas_padrao = ["data", "email_aluno", "treino", "exercicio", "carga", "comentario"]
                            df_envio = df_envio.reindex(columns=colunas_padrao)

                            existente = conn.read(worksheet="registros", ttl=0)
                            if existente is not None and not existente.empty:
                                existente = existente[colunas_padrao].dropna(how='all')
                                df_final = pd.concat([existente, df_envio], ignore_index=True)
                            else: df_final = df_envio

                            conn.update(worksheet="registros", data=df_final)
                            st.cache_data.clear()
                            st.success("✅ TREINO REGISTRADO!")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        except Exception as e: st.error(f"Erro ao gravar: {e}")

        except Exception as e: st.error(f"Erro ao carregar dados: {e}")
