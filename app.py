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
defaults = {
    'logado': False, 'email': '', 'saindo': False,
    'ex_index': 0, 'cargas_sessao': {}, 'treino_finalizado': False,
    'notas_sessao': '', 'aba_ativa': 'treino'
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 4. PERSISTÊNCIA POR COOKIE ---
if not st.session_state.logado and not st.session_state.saindo:
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
logo_url = f"data:image/jpeg;base64,{img_data}" if img_data else \
    "https://drive.google.com/uc?export=view&id=1oIpYQkIp4Y0M0vumaR5Tpa0yVDwSF7mc"

# --- 6. CONFIGURAÇÃO ---
EMAIL_COACH = "jaaovictor96@gmail.com"
conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)

@st.cache_data(ttl=30)
def ler_planilha(worksheet: str):
    return conn.read(worksheet=worksheet)

def ler_sem_cache(worksheet: str):
    return conn.read(worksheet=worksheet, ttl=0)

# --- 7. FUNÇÕES DE ENGAJAMENTO ---

def calcular_streak(historico: pd.DataFrame, email: str) -> int:
    if historico.empty:
        return 0
    df = historico[historico['email_aluno'] == email].copy()
    if df.empty:
        return 0
    try:
        df['data_dt'] = pd.to_datetime(df['data'], dayfirst=True).dt.date
        dias = sorted(df['data_dt'].unique(), reverse=True)
        hoje = datetime.now().date()
        ontem = hoje - timedelta(days=1)
        if dias[0] not in (hoje, ontem):
            return 0
        streak = 1
        for i in range(1, len(dias)):
            if (dias[i - 1] - dias[i]).days == 1:
                streak += 1
            else:
                break
        return streak
    except:
        return 0

def frases_streak(streak: int) -> tuple:
    if streak == 0:
        return "💤", "Hora de voltar à ação!"
    elif streak == 1:
        return "🔥", "Primeiro passo dado. Não pare agora!"
    elif streak <= 3:
        return "⚡", f"{streak} dias seguidos. O hábito está se formando."
    elif streak <= 7:
        return "🚀", f"{streak} dias consecutivos. Você está em chamas!"
    elif streak <= 14:
        return "💎", f"{streak} dias! Consistência de atleta de elite."
    else:
        return "🏆", f"{streak} dias seguidos. Você é imparável!"

def calcular_volume(exercicios_df: pd.DataFrame, cargas: dict) -> float:
    total = 0.0
    for idx, row in exercicios_df.iterrows():
        carga = cargas.get(f"carga_{idx}", 0)
        series = int(float(row['series'])) if pd.notnull(row.get('series')) else 0
        reps = int(float(row['reps'])) if pd.notnull(row.get('reps')) else 0
        total += carga * series * reps
    return total

def volume_anterior(historico: pd.DataFrame, email: str, treino: str,
                    exercicios_df: pd.DataFrame) -> float:
    if historico.empty:
        return 0.0
    df = historico[(historico['email_aluno'] == email) &
                   (historico['treino'] == treino)].copy()
    if df.empty:
        return 0.0
    try:
        df['data_dt'] = pd.to_datetime(df['data'], dayfirst=True)
        ultima_data = df['data_dt'].max()
        df_ult = df[df['data_dt'] == ultima_data]
        total = 0.0
        for _, row in exercicios_df.iterrows():
            filtro = df_ult[df_ult['exercicio'] == row['exercicio']]
            if not filtro.empty:
                carga = float(filtro.iloc[-1]['carga'])
                series = int(float(row['series'])) if pd.notnull(row.get('series')) else 0
                reps = int(float(row['reps'])) if pd.notnull(row.get('reps')) else 0
                total += carga * series * reps
        return total
    except:
        return 0.0

# --- 8. CSS GLOBAL ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;700;900&display=swap');

    @keyframes fadeSlideUp {{
        from {{ opacity: 0; transform: translateY(14px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes goldPulse {{
        0%, 100% {{ box-shadow: 0 0 0 0 rgba(249,192,61,0); }}
        50%        {{ box-shadow: 0 0 18px 4px rgba(249,192,61,0.18); }}
    }}
    @keyframes shimmer {{
        0%   {{ background-position: -200% center; }}
        100% {{ background-position: 200% center; }}
    }}
    @keyframes barGrow {{
        from {{ width: 0%; }}
    }}

    .stApp {{
        background: linear-gradient(rgba(10,10,10,0.97), rgba(10,10,10,0.97)),
                    url('{logo_url}');
        background-size: contain !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }}
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: transparent !important;
    }}
    .block-container {{
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 2rem !important;
    }}

    .main-title {{
        color: #F9C03D; font-family: 'Space Grotesk', sans-serif;
        font-weight: 900; letter-spacing: -2px; text-align: center;
        text-transform: uppercase; font-size: clamp(2.2rem, 8vw, 3.5rem);
        margin-bottom: 0; line-height: 0.95;
        text-shadow: 0 0 40px rgba(249,192,61,0.25);
    }}
    .sub-title {{
        text-align: center; color: #444; font-family: 'Inter', sans-serif;
        font-size: 0.65rem; letter-spacing: 4px; margin: 10px 0 36px;
        text-transform: uppercase;
    }}

    .streak-card {{
        background: linear-gradient(135deg, rgba(249,192,61,0.10), rgba(249,192,61,0.03));
        border: 1px solid rgba(249,192,61,0.22); border-radius: 18px;
        padding: 18px 20px; display: flex; align-items: center; gap: 16px;
        margin-bottom: 16px;
        animation: fadeSlideUp 0.4s ease both, goldPulse 3s ease-in-out infinite;
    }}
    .streak-emoji {{ font-size: 2.2rem; line-height: 1; flex-shrink: 0; }}
    .streak-numero {{
        color: #F9C03D; font-family: 'Space Grotesk', sans-serif;
        font-weight: 900; font-size: 2.4rem; line-height: 1;
        text-shadow: 0 0 20px rgba(249,192,61,0.4);
    }}
    .streak-label {{
        color: #4a4a4a; font-family: 'Inter', sans-serif;
        font-size: 9px; letter-spacing: 2.5px; text-transform: uppercase; margin-left: 4px;
    }}
    .streak-frase {{
        color: #888; font-family: 'Inter', sans-serif;
        font-size: 12px; margin-top: 3px; font-style: italic;
    }}

    .coach-alert {{
        background: linear-gradient(135deg, rgba(249,192,61,0.12), rgba(249,192,61,0.05));
        border: 1px solid rgba(249,192,61,0.35); border-radius: 16px;
        padding: 18px 20px; margin-bottom: 16px;
        animation: fadeSlideUp 0.4s ease both, goldPulse 2.5s ease-in-out infinite;
    }}
    .coach-alert-header {{ display:flex; align-items:center; gap:8px; margin-bottom:8px; }}
    .coach-alert-label {{
        color: #F9C03D; font-family: 'Inter', sans-serif;
        font-size: 9px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase;
    }}
    .coach-alert-dot {{
        width: 7px; height: 7px; border-radius: 50%; background: #F9C03D;
        box-shadow: 0 0 6px rgba(249,192,61,0.8);
        animation: goldPulse 1.2s ease-in-out infinite; flex-shrink: 0;
    }}
    .coach-alert-texto {{
        color: #ddd; font-family: 'Inter', sans-serif; font-size: 14px; line-height: 1.6;
    }}
    
    .coach-msg {{
        background: rgba(22,21,21,0.95); border-left: 3px solid #F9C03D;
        border-radius: 0 14px 14px 0; padding: 14px 18px; margin-bottom: 16px;
        animation: fadeSlideUp 0.45s ease both;
        box-shadow: inset 0 0 30px rgba(249,192,61,0.03);
    }}
    .coach-msg-label {{
        color: #F9C03D; font-family: 'Inter', sans-serif;
        font-size: 8px; font-weight: 700; letter-spacing: 3px;
        text-transform: uppercase; margin-bottom: 6px; opacity: 0.8;
    }}
    .coach-msg-texto {{
        color: #bbb; font-family: 'Inter', sans-serif; font-size: 13px; line-height: 1.6;
    }}

    .ex-card {{
        background: linear-gradient(145deg, rgba(26,25,25,0.98), rgba(20,19,19,0.98));
        border-radius: 20px; border-left: 4px solid #F9C03D;
        padding: 22px 20px 18px; margin-bottom: 14px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04);
        animation: fadeSlideUp 0.35s ease both;
    }}
    .ex-label {{
        color: #F9C03D; font-family: 'Inter', sans-serif;
        font-size: 9px; font-weight: 700; letter-spacing: 3px;
        text-transform: uppercase; margin: 0 0 6px; opacity: 0.75;
    }}
    .ex-name {{
        color: #FFFFFF; font-family: 'Space Grotesk', sans-serif;
        font-weight: 900; font-size: clamp(1.3rem, 5vw, 1.7rem);
        text-transform: uppercase; margin: 0 0 10px; line-height: 1.05; letter-spacing: -0.5px;
    }}
    .ex-meta {{
        color: #505050; font-family: 'Inter', sans-serif;
        font-size: 11px; margin: 0; letter-spacing: 1.5px; text-transform: uppercase;
    }}
    .ex-pr {{
        color: #F9C03D; font-family: 'Inter', sans-serif;
        font-size: 11px; opacity: 0.7; margin-top: 8px;
    }}

    .progress-bar-bg {{
        background: rgba(255,255,255,0.06); border-radius: 99px;
        height: 5px; overflow: hidden; margin: 12px 0 4px;
    }}
    .progress-bar-fill {{
        background: linear-gradient(90deg, #c98a1a, #F9C03D, #ffe085);
        border-radius: 99px; height: 5px;
        animation: barGrow 0.5s cubic-bezier(.4,0,.2,1) both;
        box-shadow: 0 0 8px rgba(249,192,61,0.5);
    }}
    .progress-label {{
        color: #3a3a3a; font-family: 'Inter', sans-serif;
        font-size: 10px; letter-spacing: 1px; text-align: right; margin: 5px 0 14px;
    }}

    .carga-display {{ text-align: center; margin: 16px 0 12px; animation: fadeSlideUp 0.3s ease both; }}
    .carga-valor {{
        color: #FFFFFF; font-family: 'Space Grotesk', sans-serif;
        font-weight: 900; font-size: clamp(3rem, 14vw, 4.5rem);
        line-height: 1; letter-spacing: -2px;
        text-shadow: 0 0 30px rgba(255,255,255,0.08);
    }}
    .carga-unit {{
        color: #3a3a3a; font-family: 'Inter', sans-serif;
        font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-top: 2px;
    }}

    div.stButton > button {{
        background-color: rgba(24,23,23,0.95) !important; color: #FFFFFF !important;
        border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 14px !important;
        font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
        font-size: 16px !important; padding: 14px 4px !important;
        min-height: 52px !important; width: 100% !important;
        transition: all 0.18s cubic-bezier(.4,0,.2,1) !important;
    }}
    div.stButton > button:hover {{
        border-color: rgba(249,192,61,0.4) !important; color: #F9C03D !important;
        background-color: rgba(249,192,61,0.06) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(249,192,61,0.08) !important;
    }}
    div.stButton > button:active {{
        transform: scale(0.97) !important; transition: transform 0.08s ease !important;
    }}
    div.stButton > button:disabled {{
        opacity: 0.18 !important; cursor: not-allowed !important; transform: none !important;
    }}
    .btn-primary > div.stButton > button {{
        background: linear-gradient(135deg, #e8ac2a, #F9C03D, #ffd166) !important;
        background-size: 200% auto !important; color: #0A0A0A !important;
        border: none !important; font-weight: 800 !important;
        font-size: 13px !important; letter-spacing: 2px !important;
        padding: 16px 12px !important; min-height: 54px !important;
        text-transform: uppercase;
        box-shadow: 0 4px 20px rgba(249,192,61,0.25) !important;
        transition: all 0.25s ease !important;
    }}
    .btn-primary > div.stButton > button:hover {{
        animation: shimmer 1.2s linear infinite !important;
        box-shadow: 0 6px 28px rgba(249,192,61,0.4) !important;
        transform: translateY(-2px) !important; color: #0A0A0A !important;
    }}
    .btn-primary > div.stButton > button:active {{
        transform: scale(0.97) translateY(0) !important;
        box-shadow: 0 2px 10px rgba(249,192,61,0.2) !important;
    }}

    .conclusao-card {{
        background: linear-gradient(160deg, rgba(26,25,25,0.98), rgba(18,17,17,0.98));
        border-radius: 20px; padding: 36px 24px; text-align: center;
        border: 1px solid rgba(249,192,61,0.15); margin-bottom: 16px;
        box-shadow: 0 8px 40px rgba(0,0,0,0.5), 0 0 60px rgba(249,192,61,0.04);
        animation: fadeSlideUp 0.4s ease both;
    }}
    .conclusao-titulo {{
        color: #F9C03D; font-family: 'Space Grotesk', sans-serif;
        font-weight: 900; font-size: clamp(1.5rem, 6vw, 2rem);
        text-transform: uppercase; margin: 10px 0 6px; letter-spacing: -0.5px;
        text-shadow: 0 0 30px rgba(249,192,61,0.3);
    }}
    .conclusao-sub {{
        color: #444; font-family: 'Inter', sans-serif;
        font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase;
    }}
    .record-badge {{
        display: inline-block; background: rgba(249,192,61,0.08);
        border: 1px solid rgba(249,192,61,0.25); border-radius: 10px;
        padding: 10px 16px; margin: 5px; color: #F9C03D;
        font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 700;
        animation: fadeSlideUp 0.4s ease both;
    }}
    .record-badge span {{ color: #888; font-size: 11px; font-weight: 400; }}

    .stat-row {{ display: flex; gap: 8px; margin: 16px 0; }}
    .stat-box {{
        flex: 1; background: rgba(20,19,19,0.95); border-radius: 14px;
        padding: 16px 10px; text-align: center;
        border: 1px solid rgba(255,255,255,0.05);
        box-shadow: 0 2px 12px rgba(0,0,0,0.3);
        animation: fadeSlideUp 0.4s ease both;
    }}
    .stat-val {{ color: #FFF; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.25rem; line-height: 1; }}
    .stat-val.up  {{ color: #4ade80; text-shadow: 0 0 12px rgba(74,222,128,0.3); }}
    .stat-val.down {{ color: #f87171; text-shadow: 0 0 12px rgba(248,113,113,0.3); }}
    .stat-lbl {{ color: #383838; font-family: 'Inter', sans-serif; font-size: 8px; letter-spacing: 1.5px; text-transform: uppercase; margin-top: 5px; }}

    .pr-row {{
        display: flex; justify-content: space-between; align-items: center;
        padding: 14px 18px; border-bottom: 1px solid rgba(255,255,255,0.04);
        transition: background 0.15s ease;
    }}
    .pr-row:last-child {{ border-bottom: none; }}
    .pr-row:hover {{ background: rgba(249,192,61,0.03); }}
    .pr-nome {{ color: #bbb; font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 500; }}
    .pr-carga {{ color: #F9C03D; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.05rem; }}
    .pr-data {{ color: #333; font-family: 'Inter', sans-serif; font-size: 9px; letter-spacing: 0.5px; margin-top: 2px; }}

    input, textarea {{
        background-color: #141313 !important; color: #ddd !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important; font-family: 'Inter', sans-serif !important;
    }}
    input:focus, textarea:focus {{
        border-color: rgba(249,192,61,0.35) !important;
        box-shadow: 0 0 0 2px rgba(249,192,61,0.08) !important;
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, rgba(12,11,11,0.99), rgba(10,9,9,0.99)) !important;
        border-right: 1px solid rgba(255,255,255,0.04) !important;
    }}

    hr {{ border-color: rgba(255,255,255,0.06) !important; margin: 20px 0 !important; }}

    ::-webkit-scrollbar {{ width: 3px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: rgba(249,192,61,0.2); border-radius: 99px; }}
    </style>
""", unsafe_allow_html=True)


# ==========================================================
# TELA DE LOGIN
# ==========================================================
if not st.session_state.logado:
    st.markdown("<h1 class='main-title' style='color:#F9C03D;'>TEAM<br>JV FERREIRA</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Aesthetic & Performance Lab<br>Consultoria Online</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        email_input = st.text_input("E-mail do Atleta", placeholder="atleta@exemplo.com").strip().lower()
        senha_input = st.text_input("Senha", type="password", placeholder="••••••").strip()

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
                    st.session_state.saindo = False
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
            except:
                st.error("Instabilidade na rede. Tente novamente em 1 segundo.")
        st.markdown('</div>', unsafe_allow_html=True)


# ==========================================================
# ÁREA LOGADA
# ==========================================================
else:
    # ---- SIDEBAR ----
    st.sidebar.markdown(
        "<p style='color:#F9C03D;font-family:Space Grotesk;font-weight:900;font-size:1rem;letter-spacing:2px;text-transform:uppercase;'>JV Performance</p>",
        unsafe_allow_html=True
    )
    st.sidebar.markdown(
        f"<p style='color:#555;font-family:Inter;font-size:11px;margin-top:-12px;'>{st.session_state.email}</p>",
        unsafe_allow_html=True
    )
    st.sidebar.divider()

    if st.sidebar.button("↩ Sair", use_container_width=True):
        # 1. Deleta o cookie
        try:
            todos_cookies = cookie_manager.get_all()
            if "jv_ferreira_login" in todos_cookies:
                cookie_manager.delete("jv_ferreira_login")
        except:
            pass
        # 2. Reseta estado para defaults
        for k, v in defaults.items():
            st.session_state[k] = v
        # 3. saindo=True DEPOIS do reset (impede cookie de relogar)
        st.session_state.saindo = True
        time.sleep(0.3)
        st.rerun()

    st.sidebar.divider()

    with st.sidebar.expander("🔑 Alterar Minha Senha"):
        nova_senha = st.text_input("Nova Senha", type="password", key="new_pass")
        confirma_senha = st.text_input("Confirme", type="password", key="conf_pass")
        if st.button("ATUALIZAR SENHA"):
            if nova_senha == confirma_senha and len(nova_senha) >= 4:
                try:
                    df_u = ler_sem_cache("usuarios")
                    mask = df_u['email'].astype(str).str.strip().str.lower() == st.session_state.email.lower()
                    if mask.any():
                        df_u.loc[mask, 'senha'] = str(nova_senha).strip()
                        conn.update(worksheet="usuarios", data=df_u)
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
            if st.form_submit_button("ENVIAR PARA O COACH"):
                try:
                    try:
                        df_ci = ler_sem_cache("checkins")
                    except:
                        df_ci = pd.DataFrame(columns=["data", "email", "peso", "feedback"])
                    novo = pd.DataFrame([{"data": datetime.now().strftime("%d/%m/%Y"),
                                          "email": st.session_state.email,
                                          "peso": peso_atual, "feedback": feedback}])
                    conn.update(worksheet="checkins", data=pd.concat([df_ci, novo], ignore_index=True))
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
        st.markdown("<h2 style='font-family:Space Grotesk;color:#F9C03D;'>ANÁLISE DE PERFORMANCE</h2>", unsafe_allow_html=True)

        df_usuarios = ler_sem_cache("usuarios")
        df_coach = ler_sem_cache("registros")

        if not df_usuarios.empty:
            df_usuarios['email'] = df_usuarios['email'].astype(str).str.strip().str.lower()
            nome_sel = st.selectbox("Selecione o Aluno:", df_usuarios['nome'].dropna().unique().tolist())
            email_vinculado = df_usuarios[df_usuarios['nome'] == nome_sel]['email'].iloc[0]

            if not df_coach.empty:
                df_coach['email_aluno'] = df_coach['email_aluno'].astype(str).str.strip().str.lower()
                df_aluno = df_coach[df_coach['email_aluno'] == email_vinculado].copy()

                with st.expander("🔍 Debug (remova após confirmar)"):
                    st.write(f"Email buscado: `{email_vinculado}`")
                    st.write(f"Emails em registros: {df_coach['email_aluno'].unique().tolist()}")
                    st.write(f"Linhas encontradas: {len(df_aluno)}")

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
                df_ci = ler_sem_cache("checkins")
                if not df_ci.empty:
                    df_ci['email'] = df_ci['email'].astype(str).str.strip().str.lower()
                    df_ci['data'] = pd.to_datetime(df_ci['data'], dayfirst=True)
                    df_f = df_ci[df_ci['email'] == email_vinculado].sort_values('data')
                    if not df_f.empty:
                        st.dataframe(df_f.sort_values('data', ascending=False),
                            column_config={
                                "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                                "email": None,
                                "peso": st.column_config.NumberColumn("Peso (kg)", format="%.1f"),
                                "feedback": "Relato do Aluno"
                            }, hide_index=True, use_container_width=True)
                        df_f['data_display'] = df_f['data'].dt.strftime('%d/%m/%Y')
                        fig_p = px.line(df_f, x='data_display', y='peso', markers=True, title=f"Evolução de Peso — {nome_sel}")
                        fig_p.update_traces(line_color='#F9C03D')
                        fig_p.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
                        fig_p.update_xaxes(type='category', title="Data do Check-in")
                        st.plotly_chart(fig_p, use_container_width=True)
                    else:
                        st.info(f"Nenhum check-in para {nome_sel}.")
                else:
                    st.info("Aba de check-ins está vazia.")
            except Exception as e:
                st.error(f"Erro check-ins: {e}")

    # ==========================================================
    # ÁREA DO ATLETA
    # ==========================================================
    else:
        # Carrega histórico uma vez para toda a área do atleta
        try:
            historico_geral = ler_planilha("registros")
            historico_geral['email_aluno'] = historico_geral['email_aluno'].astype(str).str.strip().str.lower()
        except:
            historico_geral = pd.DataFrame()

        # ---- STREAK ----
        streak = calcular_streak(historico_geral, st.session_state.email)
        emoji_s, frase_s = frases_streak(streak)
        st.markdown(f"""
            <div class='streak-card'>
                <div class='streak-emoji'>{emoji_s}</div>
                <div>
                    <div style='display:flex;align-items:baseline;gap:6px;'>
                        <span class='streak-numero'>{streak}</span>
                        <span class='streak-label'>dias seguidos</span>
                    </div>
                    <div class='streak-frase'>{frase_s}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # ---- ALERTA IN-APP: MENSAGEM DO COACH ----
        try:
            df_u = ler_planilha("usuarios")
            df_u['email'] = df_u['email'].astype(str).str.strip().str.lower()
            linha_u = df_u[df_u['email'] == st.session_state.email]
            if not linha_u.empty and 'mensagem_coach' in df_u.columns:
                msg = str(linha_u.iloc[0].get('mensagem_coach', '')).strip()
                if msg and msg.lower() not in ('nan', ''):
                    # Chave única por conteúdo da mensagem — nova msg = novo alerta
                    msg_key = f"msg_lida_{hash(msg)}"
                    if msg_key not in st.session_state:
                        st.session_state[msg_key] = False

                    if not st.session_state[msg_key]:
                        st.markdown(f"""
                            <div class='coach-alert'>
                                <div class='coach-alert-header'>
                                    <span class='coach-alert-label'>📣 Mensagem do Coach</span>
                                    <span class='coach-alert-dot'></span>
                                </div>
                                <div class='coach-alert-texto'>{msg}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        col_ok, _ = st.columns([1, 3])
                        with col_ok:
                            if st.button("✓ Entendido", key="dismiss_msg", use_container_width=True):
                                st.session_state[msg_key] = True
                                st.rerun()
                    else:
                        # Versão compacta após leitura
                        st.markdown(f"""
                            <div class='coach-msg'>
                                <div class='coach-msg-label'>📣 Coach</div>
                                <div class='coach-msg-texto'>{msg}</div>
                            </div>
                        """, unsafe_allow_html=True)
        except:
            pass

        # ---- ABAS: TREINO | MINHA EVOLUÇÃO ----
        col_t, col_e = st.columns(2)
        with col_t:
            is_treino = st.session_state.aba_ativa == 'treino'
            st.markdown(f'<div class="{"btn-primary" if is_treino else ""}">', unsafe_allow_html=True)
            if st.button("🏋️ Treino", key="tab_treino", use_container_width=True):
                st.session_state.aba_ativa = 'treino'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_e:
            is_evolucao = st.session_state.aba_ativa == 'evolucao'
            st.markdown(f'<div class="{"btn-primary" if is_evolucao else ""}">', unsafe_allow_html=True)
            if st.button("📈 Minha Evolução", key="tab_evolucao", use_container_width=True):
                st.session_state.aba_ativa = 'evolucao'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # ==========================================================
        # ABA: MINHA EVOLUÇÃO
        # ==========================================================
        if st.session_state.aba_ativa == 'evolucao':
            st.markdown(
                "<h2 style='font-family:Space Grotesk;font-size:1.8rem;font-weight:900;line-height:1;margin-bottom:16px;'>"
                "MINHA <span style='color:#F9C03D;'>EVOLUÇÃO</span></h2>",
                unsafe_allow_html=True
            )

            meu_hist = historico_geral[historico_geral['email_aluno'] == st.session_state.email].copy() \
                if not historico_geral.empty else pd.DataFrame()

            if meu_hist.empty:
                st.info("Nenhum treino registrado ainda. Complete seu primeiro treino para ver sua evolução aqui.")
            else:
                meu_hist['data'] = pd.to_datetime(meu_hist['data'], dayfirst=True)

                # Recordes Pessoais
                st.markdown(
                    "<p style='color:#F9C03D;font-family:Inter;font-size:10px;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;'>🏆 Recordes Pessoais</p>",
                    unsafe_allow_html=True
                )
                prs = meu_hist.groupby('exercicio').agg(
                    carga_max=('carga', 'max'),
                    ultima_data=('data', 'max')
                ).reset_index().sort_values('carga_max', ascending=False)

                pr_html = "<div style='background:rgba(28,27,27,0.9);border-radius:14px;overflow:hidden;margin-bottom:20px;'>"
                for _, r in prs.iterrows():
                    pr_html += f"""
                        <div class='pr-row'>
                            <div>
                                <div class='pr-nome'>{r['exercicio']}</div>
                                <div class='pr-data'>{r['ultima_data'].strftime('%d/%m/%Y')}</div>
                            </div>
                            <div class='pr-carga'>{r['carga_max']:.1f} kg</div>
                        </div>"""
                pr_html += "</div>"
                st.markdown(pr_html, unsafe_allow_html=True)

                # Calendário de treinos
                st.markdown(
                    "<p style='color:#F9C03D;font-family:Inter;font-size:10px;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;'>📅 Calendário de Treinos</p>",
                    unsafe_allow_html=True
                )

                # Navegação de mês
                if 'cal_mes' not in st.session_state:
                    st.session_state.cal_mes = datetime.now().replace(day=1)

                col_prev, col_mes_label, col_next = st.columns([1, 3, 1])
                with col_prev:
                    if st.button("←", key="cal_prev", use_container_width=True):
                        primeiro = st.session_state.cal_mes
                        st.session_state.cal_mes = (primeiro - timedelta(days=1)).replace(day=1)
                        st.rerun()
                with col_mes_label:
                    st.markdown(
                        f"<p style='text-align:center;color:#ccc;font-family:Inter;font-size:13px;font-weight:600;letter-spacing:1px;margin:10px 0;'>"
                        f"{st.session_state.cal_mes.strftime('%B %Y').upper()}</p>",
                        unsafe_allow_html=True
                    )
                with col_next:
                    hoje_dt = datetime.now().replace(day=1)
                    if st.session_state.cal_mes < hoje_dt:
                        if st.button("→", key="cal_next", use_container_width=True):
                            ultimo_dia = (st.session_state.cal_mes.replace(day=28) + timedelta(days=4)).replace(day=1)
                            st.session_state.cal_mes = ultimo_dia
                            st.rerun()

                # Monta dados do mês
                mes_ref = st.session_state.cal_mes
                ano, mes = mes_ref.year, mes_ref.month
                primeiro_dia_semana = mes_ref.weekday()  # 0=segunda
                import calendar as cal_lib
                total_dias = cal_lib.monthrange(ano, mes)[1]

                # Volume por dia no mês
                meu_hist['data_date'] = meu_hist['data'].dt.date
                vol_por_dia = {}
                for _, row_h in meu_hist.iterrows():
                    d = row_h['data_date']
                    if d.year == ano and d.month == mes:
                        vol = float(row_h.get('carga', 0))
                        vol_por_dia[d.day] = vol_por_dia.get(d.day, 0) + vol

                max_vol = max(vol_por_dia.values()) if vol_por_dia else 1

                # HTML do calendário
                dias_semana = ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM']
                cal_html = "<div style='background:rgba(18,17,17,0.95);border-radius:16px;padding:16px;margin-bottom:20px;border:1px solid rgba(255,255,255,0.05);'>"
                # Header dias da semana
                cal_html += "<div style='display:grid;grid-template-columns:repeat(7,1fr);gap:4px;margin-bottom:8px;'>"
                for d in dias_semana:
                    cal_html += f"<div style='text-align:center;color:#333;font-family:Inter;font-size:9px;letter-spacing:1px;font-weight:600;'>{d}</div>"
                cal_html += "</div>"
                # Grid de dias
                cal_html += "<div style='display:grid;grid-template-columns:repeat(7,1fr);gap:4px;'>"
                # Células vazias antes do dia 1
                for _ in range(primeiro_dia_semana):
                    cal_html += "<div></div>"
                hoje_date = datetime.now().date()
                for dia in range(1, total_dias + 1):
                    data_dia = datetime(ano, mes, dia).date()
                    vol = vol_por_dia.get(dia, 0)
                    is_hoje = data_dia == hoje_date
                    if vol > 0:
                        intensidade = vol / max_vol
                        opacity = 0.3 + 0.7 * intensidade
                        bg = f"rgba(249,192,61,{opacity:.2f})"
                        cor_txt = "#0A0A0A" if intensidade > 0.5 else "#F9C03D"
                        borda = "1px solid rgba(249,192,61,0.5)"
                    else:
                        bg = "rgba(255,255,255,0.03)"
                        cor_txt = "#333"
                        borda = "1px solid rgba(255,255,255,0.04)"
                    anel = "box-shadow:0 0 0 2px #F9C03D;" if is_hoje else ""
                    cal_html += (
                        f"<div style='aspect-ratio:1;display:flex;align-items:center;justify-content:center;"
                        f"border-radius:8px;background:{bg};border:{borda};{anel}"
                        f"font-family:Space Grotesk;font-size:11px;font-weight:700;color:{cor_txt};'>{dia}</div>"
                    )
                cal_html += "</div>"
                # Legenda
                cal_html += """
                    <div style='display:flex;align-items:center;gap:8px;margin-top:12px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.04);'>
                        <div style='width:10px;height:10px;border-radius:3px;background:rgba(249,192,61,0.3);'></div>
                        <span style='color:#444;font-family:Inter;font-size:9px;letter-spacing:1px;'>Volume baixo</span>
                        <div style='width:10px;height:10px;border-radius:3px;background:rgba(249,192,61,1);margin-left:8px;'></div>
                        <span style='color:#444;font-family:Inter;font-size:9px;letter-spacing:1px;'>Volume alto</span>
                    </div>
                """
                cal_html += "</div>"
                st.markdown(cal_html, unsafe_allow_html=True)

                # Gráfico de progressão
                st.markdown(
                    "<p style='color:#F9C03D;font-family:Inter;font-size:10px;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;'>📊 Progressão de Carga</p>",
                    unsafe_allow_html=True
                )
                ex_sel = st.selectbox("Selecione o exercício:", meu_hist['exercicio'].unique().tolist(), key="ev_ex")
                df_prog = meu_hist[meu_hist['exercicio'] == ex_sel].sort_values('data')
                df_prog['data_display'] = df_prog['data'].dt.strftime('%d/%m/%Y')
                fig = px.line(df_prog, x='data_display', y='carga', markers=True)
                fig.update_traces(line_color='#F9C03D', marker=dict(color='#F9C03D', size=8))
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font_color="white", margin=dict(l=0, r=0, t=10, b=0),
                    xaxis_title="", yaxis_title="kg"
                )
                fig.update_xaxes(type='category', gridcolor='rgba(255,255,255,0.05)')
                fig.update_yaxes(gridcolor='rgba(255,255,255,0.05)')
                st.plotly_chart(fig, use_container_width=True)

        # ==========================================================
        # ABA: TREINO
        # ==========================================================
        else:
            st.markdown(
                "<h2 style='font-family:Space Grotesk;font-size:2rem;font-weight:900;line-height:1;margin-bottom:4px;'>"
                "PROTOCOLO <span style='color:#F9C03D;'>DIÁRIO</span></h2>",
                unsafe_allow_html=True
            )

            try:
                df_treinos = ler_sem_cache("planilha_treinos")
                df_treinos['email_aluno'] = df_treinos['email_aluno'].astype(str).str.strip().str.lower()
                meus_treinos = df_treinos[df_treinos['email_aluno'] == st.session_state.email]

                if meus_treinos.empty:
                    st.info("Nenhum protocolo ativo. Aguarde seu coach configurar seu treino.")
                else:
                    treinos_disponiveis = meus_treinos['treino_nome'].unique()
                    selecao_treino = st.selectbox("Selecione o treino:", treinos_disponiveis)

                    if 'treino_ativo' not in st.session_state or st.session_state.treino_ativo != selecao_treino:
                        st.session_state.treino_ativo = selecao_treino
                        st.session_state.ex_index = 0
                        st.session_state.cargas_sessao = {}
                        st.session_state.treino_finalizado = False
                        st.session_state.notas_sessao = ""

                    exercicios_df = meus_treinos[meus_treinos['treino_nome'] == selecao_treino].reset_index(drop=True)
                    total_ex = len(exercicios_df)

                    # Pré-carrega cargas
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
                        vol_hoje = calcular_volume(exercicios_df, st.session_state.cargas_sessao)
                        vol_ant = volume_anterior(historico_geral, st.session_state.email,
                                                  selecao_treino, exercicios_df)
                        diff_vol = vol_hoje - vol_ant
                        diff_pct = (diff_vol / vol_ant * 100) if vol_ant > 0 else 0

                        recordes = []
                        for idx, row in exercicios_df.iterrows():
                            carga_hoje = st.session_state.cargas_sessao.get(f"carga_{idx}", 0)
                            carga_ant = 0.0
                            if not historico_geral.empty:
                                f2 = historico_geral[
                                    (historico_geral['email_aluno'] == st.session_state.email) &
                                    (historico_geral['exercicio'] == row['exercicio'])
                                ]
                                if not f2.empty:
                                    carga_ant = float(f2['carga'].max())
                            if carga_hoje > carga_ant and carga_ant > 0:
                                recordes.append({
                                    "exercicio": row['exercicio'],
                                    "antes": carga_ant, "depois": carga_hoje,
                                    "diff": carga_hoje - carga_ant
                                })

                        conclusao_emoji = "🏆" if recordes else "✅"
                        conclusao_msg = "Recordes Quebrados!" if recordes else "Treino Concluído!"
                        st.markdown(f"""
                            <div class='conclusao-card'>
                                <div style='font-size:3rem'>{conclusao_emoji}</div>
                                <p class='conclusao-titulo'>{conclusao_msg}</p>
                                <p class='conclusao-sub'>Mais um passo para o seu melhor.</p>
                            </div>
                        """, unsafe_allow_html=True)

                        vol_class = "up" if diff_vol >= 0 else "down"
                        vol_sinal = "+" if diff_vol >= 0 else ""
                        st.markdown(f"""
                            <div class='stat-row'>
                                <div class='stat-box'>
                                    <div class='stat-val'>{vol_hoje:,.0f}</div>
                                    <div class='stat-lbl'>Volume Total (kg)</div>
                                </div>
                                <div class='stat-box'>
                                    <div class='stat-val {vol_class}'>{vol_sinal}{diff_pct:.1f}%</div>
                                    <div class='stat-lbl'>vs Treino Anterior</div>
                                </div>
                                <div class='stat-box'>
                                    <div class='stat-val'>{total_ex}</div>
                                    <div class='stat-lbl'>Exercícios</div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                        if recordes:
                            st.markdown(
                                "<p style='color:#F9C03D;font-family:Inter;font-size:11px;letter-spacing:2px;text-align:center;text-transform:uppercase;margin:16px 0 8px;'>🔥 PRs Quebrados Hoje</p>",
                                unsafe_allow_html=True
                            )
                            badges = "".join([
                                f"<div class='record-badge'>{r['exercicio']}<br>"
                                f"<span>{r['antes']:.1f} → {r['depois']:.1f} kg (+{r['diff']:.1f})</span></div>"
                                for r in recordes
                            ])
                            st.markdown(badges, unsafe_allow_html=True)

                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
                        if st.button("+ Novo Treino", use_container_width=True):
                            st.session_state.ex_index = 0
                            st.session_state.cargas_sessao = {}
                            st.session_state.treino_finalizado = False
                            st.session_state.notas_sessao = ""
                            st.cache_data.clear()
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                    # ---- FLUXO PASSO A PASSO ----
                    else:
                        idx_atual = st.session_state.ex_index
                        row = exercicios_df.iloc[idx_atual]
                        chave = f"carga_{idx_atual}"
                        carga_atual = st.session_state.cargas_sessao[chave]

                        pct = int((idx_atual / total_ex) * 100)
                        st.markdown(f"""
                            <div class='progress-bar-bg'>
                                <div class='progress-bar-fill' style='width:{pct}%;'></div>
                            </div>
                            <p class='progress-label'>Exercício {idx_atual + 1} de {total_ex}</p>
                        """, unsafe_allow_html=True)

                        series = int(float(row['series'])) if pd.notnull(row.get('series')) else 0
                        reps   = int(float(row['reps']))   if pd.notnull(row.get('reps'))   else 0

                        st.markdown(f"""
                            <div class='ex-card'>
                                <p class='ex-label'>{selecao_treino}</p>
                                <p class='ex-name'>{row['exercicio']}</p>
                                <p class='ex-meta'>{series} SÉRIES × {reps} REPS</p>
                                <p class='ex-pr'>Última carga: {carga_atual:.1f} kg</p>
                            </div>
                        """, unsafe_allow_html=True)

                        video_url = row.get('video_url', '')
                        if pd.notnull(video_url) and str(video_url).startswith('http'):
                            embed = video_url.split('?')[0].replace('/view', '/preview').replace('/edit', '/preview')
                            with st.expander("🎬 Ver Execução"):
                                st.components.v1.html(f'<iframe src="{embed}" width="100%" height="200" frameborder="0"></iframe>', height=210)

                        # --- INPUT EDITÁVEL + BOTÕES SEM RERUN ---
                        input_key = f"input_carga_{idx_atual}"

                        # Sincroniza input com session_state na primeira vez
                        if input_key not in st.session_state:
                            st.session_state[input_key] = carga_atual

                        # Campo de digitação
                        col_inp_l, col_inp, col_inp_r = st.columns([1, 3, 1])
                        with col_inp:
                            nova_carga = st.number_input(
                                "Carga (kg)",
                                min_value=0.0,
                                max_value=999.0,
                                step=0.5,
                                value=st.session_state[input_key],
                                format="%.1f",
                                key=input_key,
                                label_visibility="collapsed"
                            )
                        # Atualiza session sem rerun — o number_input já re-renderiza
                        st.session_state.cargas_sessao[chave] = nova_carga
                        carga_atual = nova_carga

                        # Linha: − 2.5 | − 0.5 | + 0.5 | + 2.5  (sem rerun individual)
                        c1, c2, c3, c4 = st.columns(4)
                        def _ajustar(delta, _chave, _input_key):
                            novo = max(0.0, st.session_state.cargas_sessao[_chave] + delta)
                            st.session_state.cargas_sessao[_chave] = novo
                            st.session_state[_input_key] = novo

                        with c1:
                            st.button("−2.5", key=f"m25_{idx_atual}", use_container_width=True,
                                      on_click=_ajustar, args=(-2.5, chave, input_key))
                        with c2:
                            st.button("−0.5", key=f"m05_{idx_atual}", use_container_width=True,
                                      on_click=_ajustar, args=(-0.5, chave, input_key))
                        with c3:
                            st.button("+0.5", key=f"p05_{idx_atual}", use_container_width=True,
                                      on_click=_ajustar, args=(0.5, chave, input_key))
                        with c4:
                            st.button("+2.5", key=f"p25_{idx_atual}", use_container_width=True,
                                      on_click=_ajustar, args=(2.5, chave, input_key))

                        st.markdown("<br>", unsafe_allow_html=True)

                        eh_ultimo = (idx_atual == total_ex - 1)

                        if eh_ultimo:
                            notas = st.text_area(
                                "💬 Feedback do Atleta (opcional)",
                                value=st.session_state.notas_sessao,
                                placeholder="Como foi o treino? Alguma dor, cansaço, observação...",
                                key="notas_final"
                            )
                            st.session_state.notas_sessao = notas
                            col_ant, col_fin = st.columns(2)
                            with col_ant:
                                if st.button("← Anterior", key="btn_ant_final", use_container_width=True):
                                    st.session_state.ex_index -= 1
                                    st.rerun()
                            with col_fin:
                                st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
                                if st.button("FINALIZAR TREINO ✓", key="btn_finalizar", use_container_width=True):
                                    lista = []
                                    for i, r in exercicios_df.iterrows():
                                        lista.append({
                                            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                            "email_aluno": st.session_state.email,
                                            "treino": selecao_treino,
                                            "exercicio": r['exercicio'],
                                            "carga": st.session_state.cargas_sessao.get(f"carga_{i}", 0),
                                            "comentario": st.session_state.notas_sessao
                                        })
                                    df_envio = pd.DataFrame(lista)
                                    existente = ler_sem_cache("registros")
                                    conn.update(worksheet="registros", data=pd.concat([existente, df_envio], ignore_index=True))
                                    st.cache_data.clear()
                                    st.session_state.treino_finalizado = True
                                    st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            col_ant, col_prox = st.columns(2)
                            with col_ant:
                                if idx_atual > 0:
                                    if st.button("← Anterior", key=f"btn_ant_{idx_atual}", use_container_width=True):
                                        st.session_state.ex_index -= 1
                                        st.rerun()
                                else:
                                    st.button("← Anterior", key=f"btn_ant_{idx_atual}", use_container_width=True, disabled=True)
                            with col_prox:
                                st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
                                if st.button("Próximo →", key=f"btn_prox_{idx_atual}", use_container_width=True):
                                    st.session_state.ex_index += 1
                                    st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Erro: {e}")
