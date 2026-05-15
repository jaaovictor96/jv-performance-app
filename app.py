import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import time
import base64
import extra_streamlit_components as stx

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="JV PERFORMANCE", page_icon="💪", layout="centered")

# --- 2. COOKIE MANAGER ---
cookie_manager = stx.CookieManager()

# --- 3. INICIALIZAÇÃO DE ESTADO ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.email = ""

if 'ex_index' not in st.session_state:
    st.session_state.ex_index = 0

if 'cargas_sessao' not in st.session_state:
    st.session_state.cargas_sessao = {}

if 'treino_finalizado' not in st.session_state:
    st.session_state.treino_finalizado = False

if 'notas_sessao' not in st.session_state:
    st.session_state.notas_sessao = ""

# --- 4. PERSISTÊNCIA POR COOKIE ---
if not st.session_state.logado:
    token = cookie_manager.get(cookie="jv_ferreira_login")
    if token:
        st.session_state.logado = True
        st.session_state.email = token

# --- 5. LOGO ---
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

img_data = get_base64_image("JV Ferreira logo.jpeg")
if img_data:
    logo_url = f"data:image/jpeg;base64,{img_data}"
else:
    logo_url = "https://drive.google.com/uc?export=view&id=1oIpYQkIp4Y0M0vumaR5Tpa0yVDwSF7mc"

# --- 6. CONFIGURAÇÃO ---
URL_PLANILHA = "SUA_URL_AQUI"
EMAIL_COACH = "jaaovictor96@gmail.com"

conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)

# --- 7. CSS GLOBAL ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@700;900&display=swap');

    /* ---- FUNDO ---- */
    .stApp {{
        background: linear-gradient(rgba(13, 13, 13, 0.96), rgba(13, 13, 13, 0.96)),
                    url('{logo_url}');
        background-size: contain !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }}
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: transparent !important;
    }}

    /* ---- TIPOGRAFIA ---- */
    .main-title {{
        color: #F9C03D;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 900;
        letter-spacing: -1px;
        text-align: center;
        text-transform: uppercase;
        font-size: 2.5rem;
        margin-bottom: 0;
        line-height: 1;
    }}
    .sub-title {{
        text-align: center;
        color: #666;
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        letter-spacing: 3px;
        margin-bottom: 32px;
        text-transform: uppercase;
    }}

    /* ---- CARD DO EXERCÍCIO ---- */
    .ex-card {{
        background: rgba(28, 27, 27, 0.95);
        border-radius: 16px;
        border-left: 4px solid #F9C03D;
        padding: 24px 20px 20px 20px;
        margin-bottom: 12px;
        position: relative;
    }}
    .ex-label {{
        color: #F9C03D;
        font-family: 'Inter', sans-serif;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin: 0 0 4px 0;
    }}
    .ex-name {{
        color: #FFFFFF;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 1.5rem;
        text-transform: uppercase;
        margin: 0 0 8px 0;
        line-height: 1.1;
    }}
    .ex-meta {{
        color: #777;
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        margin: 0;
        letter-spacing: 1px;
    }}
    .ex-pr {{
        color: #F9C03D;
        font-family: 'Inter', sans-serif;
        font-size: 11px;
        opacity: 0.85;
        margin-top: 6px;
    }}

    /* ---- BARRA DE PROGRESSO ---- */
    .progress-bar-bg {{
        background: rgba(255,255,255,0.08);
        border-radius: 99px;
        height: 6px;
        margin: 12px 0 4px 0;
        overflow: hidden;
    }}
    .progress-bar-fill {{
        background: #F9C03D;
        border-radius: 99px;
        height: 6px;
        transition: width 0.4s ease;
    }}
    .progress-label {{
        color: #555;
        font-family: 'Inter', sans-serif;
        font-size: 10px;
        letter-spacing: 1px;
        text-align: right;
        margin-bottom: 16px;
    }}

    /* ---- DISPLAY DE CARGA ---- */
    .carga-display {{
        text-align: center;
        margin: 8px 0 4px 0;
    }}
    .carga-valor {{
        color: #FFFFFF;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 900;
        font-size: 3rem;
        line-height: 1;
    }}
    .carga-unit {{
        color: #555;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        letter-spacing: 1px;
    }}

    /* ---- BOTÕES DE AJUSTE ---- */
    div.stButton > button {{
        background-color: rgba(32, 31, 31, 0.9) !important;
        color: #FFFFFF !important;
        border: 1px solid #333 !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 10px 4px !important;
        width: 100% !important;
        transition: all 0.15s ease !important;
    }}
    div.stButton > button:hover {{
        border-color: #F9C03D !important;
        color: #F9C03D !important;
        background-color: rgba(249,192,61,0.08) !important;
    }}

    /* ---- BOTÃO PRIMÁRIO (AÇÃO PRINCIPAL) ---- */
    .btn-primary > div.stButton > button {{
        background-color: #F9C03D !important;
        color: #0D0D0D !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        letter-spacing: 1.5px !important;
        padding: 14px 12px !important;
        text-transform: uppercase;
    }}
    .btn-primary > div.stButton > button:hover {{
        background-color: #FFD166 !important;
        color: #0D0D0D !important;
    }}

    /* ---- TELA DE CONCLUSÃO ---- */
    .conclusao-card {{
        background: rgba(28, 27, 27, 0.95);
        border-radius: 16px;
        padding: 32px 24px;
        text-align: center;
        border: 1px solid rgba(249,192,61,0.2);
        margin-bottom: 16px;
    }}
    .conclusao-emoji {{
        font-size: 3rem;
        margin-bottom: 8px;
    }}
    .conclusao-titulo {{
        color: #F9C03D;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 900;
        font-size: 1.8rem;
        text-transform: uppercase;
        margin: 0 0 8px 0;
    }}
    .conclusao-sub {{
        color: #666;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        letter-spacing: 1px;
    }}
    .record-badge {{
        display: inline-block;
        background: rgba(249,192,61,0.12);
        border: 1px solid rgba(249,192,61,0.3);
        border-radius: 8px;
        padding: 8px 14px;
        margin: 4px;
        color: #F9C03D;
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 600;
    }}
    .record-badge span {{
        color: #FFFFFF;
        font-size: 11px;
        font-weight: 400;
    }}

    /* ---- INPUTS ---- */
    input {{
        background-color: #1c1b1b !important;
        color: white !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 8px !important;
    }}
    textarea {{
        background-color: #1c1b1b !important;
        color: white !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 8px !important;
    }}

    /* ---- SIDEBAR ---- */
    [data-testid="stSidebar"] {{
        background-color: rgba(16,16,16,0.97) !important;
    }}
    </style>
""", unsafe_allow_html=True)


# ==========================================================
# TELA DE LOGIN
# ==========================================================
if not st.session_state.logado:
    st.markdown("<h1 class='main-title'>TEAM <br> JV FERREIRA</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Aesthetic & Performance Lab<br>Consultoria Online</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        email_input = st.text_input("E-mail do Atleta", placeholder="atleta@exemplo.com").strip().lower()
        senha_input = st.text_input("Senha", type="password", placeholder="••••••").strip()

        with st.container():
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("ACESSAR", use_container_width=True):
                try:
                    try:
                        usuarios = conn.read(worksheet="usuarios")
                    except:
                        time.sleep(1)
                        usuarios = conn.read(worksheet="usuarios")

                    usuarios['email'] = usuarios['email'].astype(str).str.strip().str.lower()
                    usuarios['senha'] = usuarios['senha'].astype(str).str.strip()

                    if ((usuarios['email'] == email_input) & (usuarios['senha'] == senha_input)).any():
                        st.session_state.logado = True
                        st.session_state.email = email_input
                        try:
                            cookie_manager.set(
                                cookie="jv_ferreira_login",
                                val=email_input,
                                expires_at=datetime.now() + timedelta(days=30)
                            )
                        except:
                            pass
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
                except Exception as e:
                    st.error("Instabilidade na rede. Tente novamente em 1 segundo.")
            st.markdown('</div>', unsafe_allow_html=True)


# ==========================================================
# ÁREA LOGADA
# ==========================================================
else:
    # ---- SIDEBAR ----
    st.sidebar.markdown(
        "<p style='color:#F9C03D; font-family:Space Grotesk; font-weight:900; font-size:1rem; letter-spacing:2px; text-transform:uppercase;'>JV Performance</p>",
        unsafe_allow_html=True
    )
    st.sidebar.markdown(
        f"<p style='color:#555; font-family:Inter; font-size:11px; margin-top:-12px;'>{st.session_state.email}</p>",
        unsafe_allow_html=True
    )
    st.sidebar.divider()

    if st.sidebar.button("↩ Sair", use_container_width=True):
        todos_cookies = cookie_manager.get_all()
        if "jv_ferreira_login" in todos_cookies:
            try:
                cookie_manager.delete("jv_ferreira_login")
            except:
                pass
        st.session_state.logado = False
        st.session_state.email = ""
        st.session_state.ex_index = 0
        st.session_state.cargas_sessao = {}
        st.session_state.treino_finalizado = False
        time.sleep(0.5)
        st.rerun()

    st.sidebar.divider()

    with st.sidebar.expander("🔑 Alterar Minha Senha"):
        nova_senha = st.text_input("Nova Senha", type="password", key="new_pass")
        confirma_senha = st.text_input("Confirme", type="password", key="conf_pass")
        if st.button("ATUALIZAR SENHA"):
            if nova_senha == confirma_senha and len(nova_senha) >= 4:
                try:
                    df_usuarios = conn.read(worksheet="usuarios", ttl=0)
                    mask = df_usuarios['email'].astype(str).str.strip().str.lower() == st.session_state.email.lower()
                    if mask.any():
                        df_usuarios.loc[mask, 'senha'] = str(nova_senha).strip()
                        conn.update(worksheet="usuarios", data=df_usuarios)
                        st.sidebar.success("Senha alterada!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.sidebar.error("Usuário não encontrado.")
                except Exception as e:
                    st.sidebar.error(f"Erro: {e}")
            elif len(nova_senha) < 4:
                st.sidebar.warning("Mínimo 4 caracteres.")
            else:
                st.sidebar.error("As senhas não coincidem.")

    with st.sidebar.expander("📝 Check-in Quinzenal"):
        with st.form("form_checkin", clear_on_submit=True):
            st.markdown("##### Relatório de Evolução")
            peso_atual = st.number_input("Peso Atual (kg)", min_value=30.0, step=0.1)
            feedback = st.text_area("Como se sentiu (Fome, Sono, Treino)?")
            enviar_checkin = st.form_submit_button("ENVIAR PARA O COACH")
            if enviar_checkin:
                try:
                    try:
                        df_existente = conn.read(worksheet="checkins", ttl=0)
                    except:
                        df_existente = pd.DataFrame(columns=["data", "email", "peso", "feedback"])
                    novo = pd.DataFrame([{
                        "data": datetime.now().strftime("%d/%m/%Y"),
                        "email": st.session_state.email,
                        "peso": peso_atual,
                        "feedback": feedback
                    }])
                    df_atualizado = pd.concat([df_existente, novo], ignore_index=True)
                    conn.update(worksheet="checkins", data=df_atualizado)
                    st.sidebar.success("Check-in enviado! 🚀")
                except Exception as e:
                    st.sidebar.error(f"Erro: {e}")

    # ---- PAINEL DO COACH ----
    ativar_dashboard = False
    if st.session_state.email == EMAIL_COACH:
        st.sidebar.divider()
        st.sidebar.subheader("🛠 PAINEL DO COACH")
        ativar_dashboard = st.sidebar.checkbox("Visualizar Métricas")

    # ==========================================================
    # DASHBOARD DO COACH
    # ==========================================================
    if ativar_dashboard:
        st.markdown("<h2 style='font-family: Space Grotesk; color: #F9C03D;'>ANÁLISE DE PERFORMANCE</h2>", unsafe_allow_html=True)

        df_usuarios = conn.read(worksheet="usuarios", ttl=0)
        df_coach = conn.read(worksheet="registros", ttl=0)

        if not df_usuarios.empty:
            lista_nomes = df_usuarios['nome'].dropna().unique().tolist()
            nome_sel = st.selectbox("Selecione o Aluno:", lista_nomes)
            email_vinculado = df_usuarios[df_usuarios['nome'] == nome_sel]['email'].iloc[0].strip().lower()

            if not df_coach.empty:
                df_coach['email_aluno'] = df_coach['email_aluno'].astype(str).str.strip().str.lower()
                df_aluno = df_coach[df_coach['email_aluno'] == email_vinculado].copy()

                if not df_aluno.empty:
                    df_aluno['data'] = pd.to_datetime(df_aluno['data'], dayfirst=True)
                    exercicio_sel = st.selectbox("Exercício:", df_aluno['exercicio'].unique())
                    df_prog = df_aluno[df_aluno['exercicio'] == exercicio_sel].sort_values('data')
                    df_prog['data_display'] = df_prog['data'].dt.strftime('%d/%m/%Y')

                    fig = px.line(df_prog, x='data_display', y='carga', title=f'Progressão: {exercicio_sel}', markers=True)
                    fig.update_traces(line_color='#F9C03D')
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
                    fig.update_xaxes(type='category', title="Data do Treino")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"{nome_sel} ainda não registrou treinos.")

            st.divider()
            st.markdown("### 📋 Histórico de Check-ins")
            try:
                df_checkins = conn.read(worksheet="checkins", ttl=0)
                if not df_checkins.empty:
                    df_checkins['email'] = df_checkins['email'].astype(str).str.strip().str.lower()
                    df_checkins['data'] = pd.to_datetime(df_checkins['data'], dayfirst=True)
                    df_filtrado = df_checkins[df_checkins['email'] == email_vinculado].sort_values('data')

                    if not df_filtrado.empty:
                        st.dataframe(
                            df_filtrado.sort_values('data', ascending=False),
                            column_config={
                                "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                                "email": None,
                                "peso": st.column_config.NumberColumn("Peso (kg)", format="%.1f"),
                                "feedback": "Relato do Aluno"
                            },
                            hide_index=True,
                            use_container_width=True
                        )
                        df_filtrado['data_display'] = df_filtrado['data'].dt.strftime('%d/%m/%Y')
                        fig_peso = px.line(df_filtrado, x='data_display', y='peso', markers=True, title=f"Evolução de Peso — {nome_sel}")
                        fig_peso.update_traces(line_color='#F9C03D')
                        fig_peso.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
                        fig_peso.update_xaxes(type='category', title="Data do Check-in")
                        st.plotly_chart(fig_peso, use_container_width=True)
                    else:
                        st.info(f"Nenhum check-in para {nome_sel}.")
                else:
                    st.info("Aba de check-ins está vazia.")
            except Exception as e:
                st.error(f"Erro ao carregar check-ins: {e}")

    # ==========================================================
    # PROTOCOLO DIÁRIO — FLUXO PASSO A PASSO
    # ==========================================================
    else:
        st.markdown(
            "<h2 style='font-family: Space Grotesk; font-size: 2rem; font-weight: 900; line-height: 1; margin-bottom: 4px;'>"
            "PROTOCOLO <span style='color: #F9C03D;'>DIÁRIO</span></h2>",
            unsafe_allow_html=True
        )

        try:
            df_treinos = conn.read(worksheet="planilha_treinos", ttl=0)
            df_treinos['email_aluno'] = df_treinos['email_aluno'].astype(str).str.strip().str.lower()
            meus_treinos = df_treinos[df_treinos['email_aluno'] == st.session_state.email]

            try:
                historico_geral = conn.read(worksheet="registros")
                historico_geral['email_aluno'] = historico_geral['email_aluno'].astype(str).str.strip().str.lower()
            except:
                historico_geral = pd.DataFrame()

            if meus_treinos.empty:
                st.info("Nenhum protocolo ativo. Aguarde seu coach configurar seu treino.")
            else:
                treinos_disponiveis = meus_treinos['treino_nome'].unique()
                selecao_treino = st.selectbox("Selecione o treino:", treinos_disponiveis)

                # Resetar progresso se trocou de treino
                if 'treino_ativo' not in st.session_state or st.session_state.treino_ativo != selecao_treino:
                    st.session_state.treino_ativo = selecao_treino
                    st.session_state.ex_index = 0
                    st.session_state.cargas_sessao = {}
                    st.session_state.treino_finalizado = False
                    st.session_state.notas_sessao = ""

                exercicios_df = meus_treinos[meus_treinos['treino_nome'] == selecao_treino].reset_index(drop=True)
                total_ex = len(exercicios_df)

                # Pré-carrega cargas anteriores na primeira vez
                for idx, row in exercicios_df.iterrows():
                    chave = f"carga_{idx}"
                    if chave not in st.session_state.cargas_sessao:
                        carga_ant = 0.0
                        if not historico_geral.empty:
                            filtro = historico_geral[
                                (historico_geral['email_aluno'] == st.session_state.email) &
                                (historico_geral['exercicio'] == row['exercicio'])
                            ]
                            if not filtro.empty:
                                carga_ant = float(filtro.iloc[-1]['carga'])
                        st.session_state.cargas_sessao[chave] = carga_ant

                # ---- TELA DE CONCLUSÃO ----
                if st.session_state.treino_finalizado:
                    # Detecta recordes
                    recordes = []
                    for idx, row in exercicios_df.iterrows():
                        chave = f"carga_{idx}"
                        carga_hoje = st.session_state.cargas_sessao.get(chave, 0)
                        carga_ant = 0.0
                        if not historico_geral.empty:
                            filtro = historico_geral[
                                (historico_geral['email_aluno'] == st.session_state.email) &
                                (historico_geral['exercicio'] == row['exercicio'])
                            ]
                            if not filtro.empty:
                                carga_ant = float(filtro.iloc[-1]['carga'])
                        if carga_hoje > carga_ant and carga_ant > 0:
                            recordes.append({
                                "exercicio": row['exercicio'],
                                "antes": carga_ant,
                                "depois": carga_hoje,
                                "diff": carga_hoje - carga_ant
                            })

                    st.markdown("""
                        <div class='conclusao-card'>
                            <div class='conclusao-emoji'>🏆</div>
                            <p class='conclusao-titulo'>Treino Concluído!</p>
                            <p class='conclusao-sub'>Mais um passo para o seu melhor.</p>
                        </div>
                    """, unsafe_allow_html=True)

                    if recordes:
                        st.markdown(
                            "<p style='color:#F9C03D; font-family:Inter; font-size:11px; letter-spacing:2px; text-align:center; text-transform:uppercase; margin-bottom:8px;'>🔥 Recordes Pessoais Quebrados</p>",
                            unsafe_allow_html=True
                        )
                        badges_html = ""
                        for r in recordes:
                            badges_html += f"<div class='record-badge'>{r['exercicio']}<br><span>{r['antes']} → {r['depois']} kg (+{r['diff']:.1f})</span></div>"
                        st.markdown(badges_html, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    col_novo, col_hist = st.columns(2)
                    with col_novo:
                        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
                        if st.button("+ Novo Treino", use_container_width=True):
                            st.session_state.ex_index = 0
                            st.session_state.cargas_sessao = {}
                            st.session_state.treino_finalizado = False
                            st.session_state.notas_sessao = ""
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                # ---- FLUXO PASSO A PASSO ----
                else:
                    idx_atual = st.session_state.ex_index
                    row = exercicios_df.iloc[idx_atual]
                    chave = f"carga_{idx_atual}"
                    carga_atual = st.session_state.cargas_sessao[chave]

                    # Barra de progresso
                    pct = int((idx_atual / total_ex) * 100)
                    st.markdown(f"""
                        <div class='progress-bar-bg'>
                            <div class='progress-bar-fill' style='width:{pct}%;'></div>
                        </div>
                        <p class='progress-label'>Exercício {idx_atual + 1} de {total_ex}</p>
                    """, unsafe_allow_html=True)

                    # Card do exercício
                    series = int(float(row['series'])) if pd.notnull(row['series']) else 0
                    reps = int(float(row['reps'])) if pd.notnull(row['reps']) else 0

                    st.markdown(f"""
                        <div class='ex-card'>
                            <p class='ex-label'>{selecao_treino}</p>
                            <p class='ex-name'>{row['exercicio']}</p>
                            <p class='ex-meta'>{series} SÉRIES × {reps} REPS</p>
                            <p class='ex-pr'>Última carga: {carga_atual:.1f} kg</p>
                        </div>
                    """, unsafe_allow_html=True)

                    # Vídeo de execução
                    video_url = row.get('video_url', '')
                    if pd.notnull(video_url) and str(video_url).startswith('http'):
                        video_embed = video_url.split('?')[0].replace('/view', '/preview').replace('/edit', '/preview')
                        with st.expander("🎬 Ver Execução"):
                            st.components.v1.html(f'<iframe src="{video_embed}" width="100%" height="200" frameborder="0"></iframe>', height=210)

                    # Display da carga
                    st.markdown(f"""
                        <div class='carga-display'>
                            <p class='carga-valor'>{carga_atual:.1f}</p>
                            <p class='carga-unit'>KG</p>
                        </div>
                    """, unsafe_allow_html=True)

                    # Botões de ajuste de carga
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        if st.button("−2.5", key=f"m25_{idx_atual}", use_container_width=True):
                            st.session_state.cargas_sessao[chave] = max(0.0, carga_atual - 2.5)
                            st.rerun()
                    with c2:
                        if st.button("−0.5", key=f"m05_{idx_atual}", use_container_width=True):
                            st.session_state.cargas_sessao[chave] = max(0.0, carga_atual - 0.5)
                            st.rerun()
                    with c3:
                        if st.button("+0.5", key=f"p05_{idx_atual}", use_container_width=True):
                            st.session_state.cargas_sessao[chave] = carga_atual + 0.5
                            st.rerun()
                    with c4:
                        if st.button("+2.5", key=f"p25_{idx_atual}", use_container_width=True):
                            st.session_state.cargas_sessao[chave] = carga_atual + 2.5
                            st.rerun()

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Navegação
                    eh_ultimo = (idx_atual == total_ex - 1)

                    if eh_ultimo:
                        # Notas antes de finalizar
                        notas = st.text_area(
                            "💬 Feedback do Atleta (opcional)",
                            value=st.session_state.notas_sessao,
                            placeholder="Como foi o treino? Alguma dor, cansaço, observação...",
                            key="notas_final"
                        )
                        st.session_state.notas_sessao = notas

                        col_ant, col_fin = st.columns([1, 2])
                        with col_ant:
                            if st.button("← Anterior", key="btn_ant_final", use_container_width=True):
                                st.session_state.ex_index -= 1
                                st.rerun()
                        with col_fin:
                            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
                            if st.button("FINALIZAR TREINO ✓", key="btn_finalizar", use_container_width=True):
                                # Monta lista de registros
                                lista_registros = []
                                for i, r in exercicios_df.iterrows():
                                    lista_registros.append({
                                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                        "email_aluno": st.session_state.email,
                                        "treino": selecao_treino,
                                        "exercicio": r['exercicio'],
                                        "carga": st.session_state.cargas_sessao.get(f"carga_{i}", 0),
                                        "comentario": st.session_state.notas_sessao
                                    })
                                df_envio = pd.DataFrame(lista_registros)
                                existente = conn.read(worksheet="registros", ttl=0)
                                df_final = pd.concat([existente, df_envio], ignore_index=True)
                                conn.update(worksheet="registros", data=df_final)
                                st.cache_data.clear()
                                st.session_state.treino_finalizado = True
                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        col_ant, col_prox = st.columns([1, 2])
                        with col_ant:
                            if idx_atual > 0:
                                if st.button("← Anterior", key=f"btn_ant_{idx_atual}", use_container_width=True):
                                    st.session_state.ex_index -= 1
                                    st.rerun()
                        with col_prox:
                            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
                            if st.button("Próximo →", key=f"btn_prox_{idx_atual}", use_container_width=True):
                                st.session_state.ex_index += 1
                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Erro: {e}")
