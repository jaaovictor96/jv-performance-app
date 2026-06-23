import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import time
import base64
try:
    import extra_streamlit_components as stx
except ModuleNotFoundError:
    stx = None
import html

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="JV PERFORMANCE", page_icon="💪", layout="centered")

# --- 2. COOKIE MANAGER ---
class CookieManagerFallback:
    def get(self, *args, **kwargs):
        return None

    def get_all(self):
        return {}

    def set(self, *args, **kwargs):
        return None

    def delete(self, *args, **kwargs):
        return None

cookie_manager = stx.CookieManager() if stx else CookieManagerFallback()

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

    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: 0.001ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.001ms !important;
            scroll-behavior: auto !important;
        }}
    }}

    @media (max-width: 640px) {{
        .stApp {{
            background-attachment: scroll !important;
            background-size: 78vw auto !important;
        }}
        .block-container {{
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            padding-top: 1rem !important;
            padding-bottom: 5rem !important;
        }}
        .main-title {{
            letter-spacing: 0 !important;
        }}
        .sub-title,
        .coach-alert-label,
        .coach-msg-label,
        .ex-label,
        .stat-lbl {{
            letter-spacing: 1.5px !important;
        }}
        .ex-card,
        .conclusao-card,
        .coach-alert,
        .streak-card {{
            border-radius: 14px !important;
            padding-left: 16px !important;
            padding-right: 16px !important;
            box-shadow: 0 3px 18px rgba(0,0,0,0.35) !important;
        }}
        .ex-name,
        .coach-alert-texto,
        .coach-msg-texto,
        .pr-nome,
        .record-badge {{
            overflow-wrap: anywhere;
            word-break: normal;
        }}
        .stat-row {{
            display: grid !important;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 6px !important;
        }}
        .stat-box {{
            padding: 12px 6px !important;
        }}
        .stat-val {{
            font-size: 1rem !important;
        }}
        .carga-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 8px;
            margin-top: 8px;
        }}
        .carga-grid [data-testid="column"] {{
            width: 100% !important;
            flex: 1 1 48% !important;
        }}
        .mobile-account-panel {{
            display: block;
            background: rgba(18,17,17,0.95);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 14px;
            padding: 12px 14px;
            margin-bottom: 14px;
        }}
        .mobile-account-label {{
            color: #F9C03D;
            font-family: Inter, sans-serif;
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 3px;
        }}
        .mobile-account-email {{
            color: #777;
            font-family: Inter, sans-serif;
            font-size: 12px;
            overflow-wrap: anywhere;
        }}
    }}

    @media (min-width: 641px) {{
        .mobile-account-panel {{
            display: none;
        }}
    }}
    </style>
""", unsafe_allow_html=True)


# ==========================================================
# TELA DE LOGIN
# ==========================================================
if not st.session_state.logado:
    st.markdown("<h1 class='main-title' style='color:#F9C03D;'>TEAM<br>JV FERREIRA</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Aesthetic & Performance Lab<br>Consultoria Online</p>", unsafe_allow_html=True)

    with st.container():
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
                    df_aluno['data'] = pd.to_datetime(df_aluno['data'], dayfirst=True, errors='coerce')
                    df_aluno = df_aluno.dropna(subset=['data'])
                    if df_aluno.empty:
                        st.info(f"{nome_sel} ainda não possui treinos com data válida.")
                    else:
                        df_aluno['data_dia'] = df_aluno['data'].dt.date
                        df_aluno['data_display'] = df_aluno['data'].dt.strftime('%d/%m/%Y')

                        st.markdown("### 📅 Calendário de Treinos")
                        meses_disponiveis = sorted(df_aluno['data'].dt.to_period('M').unique(), reverse=True)
                        mes_opcoes = {m.strftime('%m/%Y'): m for m in meses_disponiveis}
                        mes_label = st.selectbox('Mês:', list(mes_opcoes.keys()), key=f'coach_mes_treino_{email_vinculado}')
                        mes_ref = mes_opcoes[mes_label].to_timestamp()
                        ano, mes = mes_ref.year, mes_ref.month
                        primeiro_dia_semana = mes_ref.weekday()
                        import calendar as cal_lib
                        total_dias = cal_lib.monthrange(ano, mes)[1]
                        treinos_por_dia = df_aluno.groupby('data_dia').size().to_dict()
                        max_treinos = max(treinos_por_dia.values()) if treinos_por_dia else 1

                        dias_semana = ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM']
                        cal_html = "<div style='background:rgba(18,17,17,0.95);border-radius:16px;padding:16px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.05);'>"
                        cal_html += "<div style='display:grid;grid-template-columns:repeat(7,1fr);gap:4px;margin-bottom:8px;'>"
                        for d in dias_semana:
                            cal_html += f"<div style='text-align:center;color:#555;font-family:Inter;font-size:9px;letter-spacing:1px;font-weight:600;'>{d}</div>"
                        cal_html += "</div><div style='display:grid;grid-template-columns:repeat(7,1fr);gap:4px;'>"
                        for _ in range(primeiro_dia_semana):
                            cal_html += "<div></div>"
                        for dia in range(1, total_dias + 1):
                            data_dia = datetime(ano, mes, dia).date()
                            qtd = treinos_por_dia.get(data_dia, 0)
                            if qtd:
                                intensidade = qtd / max_treinos
                                opacity = 0.35 + 0.65 * intensidade
                                bg = f"rgba(249,192,61,{opacity:.2f})"
                                cor_txt = '#0A0A0A' if intensidade > 0.5 else '#F9C03D'
                                borda = '1px solid rgba(249,192,61,0.55)'
                            else:
                                bg = 'rgba(255,255,255,0.03)'
                                cor_txt = '#333'
                                borda = '1px solid rgba(255,255,255,0.04)'
                            cal_html += (
                                f"<div title='{qtd} registros' style='aspect-ratio:1;display:flex;align-items:center;justify-content:center;"
                                f"border-radius:8px;background:{bg};border:{borda};font-family:Space Grotesk;font-size:11px;font-weight:700;color:{cor_txt};'>{dia}</div>"
                            )
                        cal_html += "</div></div>"
                        st.markdown(cal_html, unsafe_allow_html=True)

                        dias_treinados = sorted(df_aluno['data_dia'].unique())
                        dias_labels = [d.strftime('%d/%m/%Y') for d in dias_treinados]
                        dia_label = st.select_slider('Dias com treino:', options=dias_labels, value=dias_labels[-1], key=f'coach_dia_treino_{email_vinculado}')
                        dia_sel = datetime.strptime(dia_label, '%d/%m/%Y').date()
                        df_dia = df_aluno[df_aluno['data_dia'] == dia_sel].copy()

                        st.markdown(f"### 🧾 Treinos de {dia_label}")
                        for treino_nome, df_treino_dia in df_dia.sort_values(['treino', 'exercicio']).groupby('treino'):
                            with st.expander(f"{treino_nome} — {len(df_treino_dia)} exercícios", expanded=True):
                                cols = [c for c in ['exercicio', 'carga', 'comentario'] if c in df_treino_dia.columns]
                                st.dataframe(
                                    df_treino_dia[cols].rename(columns={
                                        'exercicio': 'Exercício',
                                        'carga': 'Carga (kg)',
                                        'comentario': 'Comentário'
                                    }),
                                    hide_index=True,
                                    use_container_width=True
                                )

                        st.markdown("### 📋 Exercícios por Treino")
                        try:
                            df_protocolos = ler_sem_cache('planilha_treinos')
                            df_protocolos['email_aluno'] = df_protocolos['email_aluno'].astype(str).str.strip().str.lower()
                            df_protocolos = df_protocolos[df_protocolos['email_aluno'] == email_vinculado].copy()
                            if df_protocolos.empty:
                                st.info("Nenhum protocolo cadastrado para este aluno.")
                            else:
                                for treino_nome, df_treino in df_protocolos.groupby('treino_nome', sort=False):
                                    with st.expander(f"{treino_nome} — protocolo", expanded=False):
                                        cols = [c for c in ['exercicio', 'series', 'reps', 'video_url'] if c in df_treino.columns]
                                        st.dataframe(
                                            df_treino[cols].rename(columns={
                                                'exercicio': 'Exercício',
                                                'series': 'Séries',
                                                'reps': 'Reps',
                                                'video_url': 'Vídeo'
                                            }),
                                            hide_index=True,
                                            use_container_width=True
                                        )
                        except Exception as e:
                            st.warning(f"Não foi possível carregar a tabela de exercícios: {e}")

                        st.markdown("### 📈 Progressão de Carga")
                        exercicio_sel = st.selectbox('Exercício:', df_aluno['exercicio'].dropna().unique(), key=f'coach_exercicio_{email_vinculado}')
                        df_prog = df_aluno[df_aluno['exercicio'] == exercicio_sel].sort_values('data')
                        df_prog['data_display'] = df_prog['data'].dt.strftime('%d/%m/%Y')
                        fig = px.line(df_prog, x='data_display', y='carga', title=f'Progressão: {exercicio_sel}', markers=True)
                        fig.update_traces(line_color='#F9C03D')
                        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
                        fig.update_xaxes(type='category', title='Data do Treino')
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"{nome_sel} ainda não registrou treinos.")

            st.divider()
            st.markdown("### 📋 Histórico de Check-ins")
            try:
                df_ci = ler_sem_cache("checkins")
                if not df_ci.empty:
                    df_ci['email'] = df_ci['email'].astype(str).str.strip().str.lower()
                    df_ci['data'] = pd.to_datetime(df_ci['data'], dayfirst=True, errors='coerce')
                    df_ci = df_ci.dropna(subset=['data'])
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

            st.divider()
            st.markdown("### 💳 Pagamentos")
            try:
                try:
                    df_pag = ler_sem_cache("pagamentos")
                except:
                    df_pag = pd.DataFrame(columns=["data", "email", "referencia", "valor", "status", "observacao"])
                if not df_pag.empty and 'email' in df_pag.columns:
                    df_pag['email'] = df_pag['email'].astype(str).str.strip().str.lower()
                df_pag_aluno = df_pag[df_pag['email'] == email_vinculado].copy() if not df_pag.empty and 'email' in df_pag.columns else pd.DataFrame()

                with st.form('form_pagamento_coach', clear_on_submit=True):
                    col_data, col_ref = st.columns(2)
                    with col_data:
                        data_pag = st.date_input("Data", value=datetime.now().date(), key="pag_data")
                    with col_ref:
                        referencia_pag = st.text_input("Referência", placeholder="Ex.: Julho/2026", key="pag_ref")
                    col_valor, col_status = st.columns(2)
                    with col_valor:
                        valor_pag = st.number_input("Valor (R$)", min_value=0.0, step=10.0, format="%.2f", key="pag_valor")
                    with col_status:
                        status_pag = st.selectbox("Status", ["Pago", "Pendente", "Atrasado", "Isento"], key="pag_status")
                    obs_pag = st.text_area("Observação", key="pag_obs")
                    if st.form_submit_button("REGISTRAR PAGAMENTO", use_container_width=True):
                        novo_pag = pd.DataFrame([{
                            "data": data_pag.strftime("%d/%m/%Y"),
                            "email": email_vinculado,
                            "referencia": referencia_pag,
                            "valor": valor_pag,
                            "status": status_pag,
                            "observacao": obs_pag
                        }])
                        conn.update(worksheet="pagamentos", data=pd.concat([df_pag, novo_pag], ignore_index=True))
                        st.success("Pagamento registrado!")
                        st.cache_data.clear()
                        st.rerun()

                if df_pag_aluno.empty:
                    st.info("Nenhum pagamento registrado para este aluno.")
                else:
                    df_pag_aluno['data_dt'] = pd.to_datetime(df_pag_aluno['data'], dayfirst=True, errors='coerce') if 'data' in df_pag_aluno.columns else pd.NaT
                    df_pag_aluno = df_pag_aluno.sort_values('data_dt', ascending=False)
                    cols_pag = [c for c in ['data', 'referencia', 'valor', 'status', 'observacao'] if c in df_pag_aluno.columns]
                    st.dataframe(
                        df_pag_aluno[cols_pag].rename(columns={
                            'data': 'Data',
                            'referencia': 'Referência',
                            'valor': 'Valor (R$)',
                            'status': 'Status',
                            'observacao': 'Observação'
                        }),
                        hide_index=True,
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Erro pagamentos: {e}")

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

        # ---- ACESSO RÁPIDO MOBILE ----
        st.markdown(f"""
            <div class='mobile-account-panel'>
                <div class='mobile-account-label'>Conta do atleta</div>
                <div class='mobile-account-email'>{html.escape(st.session_state.email)}</div>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("⚙️ Configurações"):
            tab_senha, tab_sair = st.tabs(["Senha", "Sair"])
            with tab_senha:
                nova_senha_mobile = st.text_input("Nova Senha", type="password", key="new_pass_mobile")
                confirma_senha_mobile = st.text_input("Confirme", type="password", key="conf_pass_mobile")
                if st.button("ATUALIZAR SENHA", key="btn_senha_mobile", use_container_width=True):
                    if nova_senha_mobile == confirma_senha_mobile and len(nova_senha_mobile) >= 4:
                        try:
                            df_u = ler_sem_cache("usuarios")
                            mask = df_u['email'].astype(str).str.strip().str.lower() == st.session_state.email.lower()
                            if mask.any():
                                df_u.loc[mask, 'senha'] = str(nova_senha_mobile).strip()
                                conn.update(worksheet="usuarios", data=df_u)
                                st.success("Senha alterada!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Usuário não encontrado.")
                        except Exception as e:
                            st.error(f"Erro: {e}")
                    elif len(nova_senha_mobile) < 4:
                        st.warning("Mínimo 4 caracteres.")
                    else:
                        st.error("As senhas não coincidem.")
            with tab_sair:
                st.caption("Encerra sua sessão neste aparelho.")
                if st.button("↩ Sair", key="btn_sair_mobile", use_container_width=True):
                    try:
                        todos_cookies = cookie_manager.get_all()
                        if "jv_ferreira_login" in todos_cookies:
                            cookie_manager.delete("jv_ferreira_login")
                    except:
                        pass
                    for k, v in defaults.items():
                        st.session_state[k] = v
                    st.session_state.saindo = True
                    time.sleep(0.3)
                    st.rerun()

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
                msg_html = html.escape(msg).replace(chr(13) + chr(10), '<br>').replace(chr(10), '<br>')
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
                                <div class='coach-alert-texto'>{msg_html}</div>
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
                                <div class='coach-msg-texto'>{msg_html}</div>
                            </div>
                        """, unsafe_allow_html=True)
        except:
            pass

        # ---- ABAS: TREINO | CHECK-IN ----
        if st.session_state.aba_ativa not in ('treino', 'checkin'):
            st.session_state.aba_ativa = 'treino'

        col_t, col_c = st.columns(2)
        with col_t:
            is_treino = st.session_state.aba_ativa == 'treino'
            st.markdown(f'<div class="{"btn-primary" if is_treino else ""}">', unsafe_allow_html=True)
            if st.button("🏋️ Treino", key="tab_treino", use_container_width=True):
                st.session_state.aba_ativa = 'treino'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_c:
            is_checkin = st.session_state.aba_ativa == 'checkin'
            st.markdown(f'<div class="{"btn-primary" if is_checkin else ""}">', unsafe_allow_html=True)
            if st.button("📝 Check-in", key="tab_checkin", use_container_width=True):
                st.session_state.aba_ativa = 'checkin'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('---')

        # ==========================================================
        # ABA: CHECK-IN
        # ==========================================================
        if st.session_state.aba_ativa == 'checkin':
            st.markdown(
                "<h2 style='font-family:Space Grotesk;font-size:1.8rem;font-weight:900;line-height:1;margin-bottom:16px;'>"
                "<span style='color:#F9C03D;'>CHECK-IN</span></h2>",
                unsafe_allow_html=True
            )
            with st.form("form_checkin_main", clear_on_submit=True):
                st.markdown("##### Relatório de Evolução")
                ultimo_peso = 0.0
                try:
                    df_ci_peso = ler_sem_cache("checkins")
                    if not df_ci_peso.empty:
                        df_ci_peso['email'] = df_ci_peso['email'].astype(str).str.strip().str.lower()
                        meus_checkins = df_ci_peso[df_ci_peso['email'] == st.session_state.email.lower()].copy()
                        if not meus_checkins.empty:
                            meus_checkins['data_dt'] = pd.to_datetime(meus_checkins['data'], dayfirst=True, errors='coerce')
                            meus_checkins = meus_checkins.sort_values('data_dt')
                            ultimo_peso = float(meus_checkins.iloc[-1].get('peso', 0) or 0)
                except:
                    ultimo_peso = 0.0
                peso_checkin_key = f"peso_checkin_main_{st.session_state.email}"
                peso_atual = st.number_input("Peso Atual (kg)", min_value=0.0, value=float(ultimo_peso), step=0.1, key=peso_checkin_key)
                feedback = st.text_area("Como se sentiu (Fome, Sono, Treino)?", key="feedback_checkin_main")
                if st.form_submit_button("ENVIAR PARA O COACH", use_container_width=True):
                    try:
                        try:
                            df_ci = ler_sem_cache("checkins")
                        except:
                            df_ci = pd.DataFrame(columns=["data", "email", "peso", "feedback"])
                        novo = pd.DataFrame([{"data": datetime.now().strftime("%d/%m/%Y"),
                                              "email": st.session_state.email,
                                              "peso": peso_atual, "feedback": feedback}])
                        conn.update(worksheet="checkins", data=pd.concat([df_ci, novo], ignore_index=True))
                        st.success("Check-in enviado! 🚀")
                    except Exception as e:
                        st.error(f"Erro: {e}")

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
                df_treinos = ler_planilha("planilha_treinos")
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
                        exercicio_nome_html = html.escape(str(row['exercicio']))
                        treino_nome_html = html.escape(str(selecao_treino))
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
                                <p class='ex-label'>{treino_nome_html}</p>
                                <p class='ex-name'>{exercicio_nome_html}</p>
                                <p class='ex-meta'>{series} SÉRIES × {reps} REPS</p>
                                <p class='ex-pr'>Última carga: {carga_atual:.1f} kg</p>
                            </div>
                        """, unsafe_allow_html=True)

                        video_url = row.get('video_url', '')
                        if pd.notnull(video_url) and str(video_url).startswith('http'):
                            embed = video_url.split('?')[0].replace('/view', '/preview').replace('/edit', '/preview')
                            with st.expander("🎬 Ver Execução"):
                                st.components.v1.html(f'<div style="position:relative;width:100%;padding-top:56.25%;overflow:hidden;border-radius:12px;background:#111;"><iframe src="{embed}" style="position:absolute;inset:0;width:100%;height:100%;border:0;" allowfullscreen></iframe></div>', height=260)


                        carga_manual_key = f"carga_manual_{idx_atual}_{carga_atual:.1f}"
                        carga_manual = st.number_input(
                            "Carga atual (kg)",
                            min_value=0.0,
                            value=float(carga_atual),
                            step=0.5,
                            format="%.1f",
                            key=carga_manual_key,
                            help="Digite a carga manualmente ou use os botões abaixo para ajustar."
                        )
                        if float(carga_manual) != float(carga_atual):
                            st.session_state.cargas_sessao[chave] = float(carga_manual)
                            st.rerun()

                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("−2.5", key=f"m25_{idx_atual}", use_container_width=True):
                                st.session_state.cargas_sessao[chave] = max(0.0, carga_atual - 2.5)
                                st.rerun()
                        with c2:
                            if st.button("−0.5", key=f"m05_{idx_atual}", use_container_width=True):
                                st.session_state.cargas_sessao[chave] = max(0.0, carga_atual - 0.5)
                                st.rerun()

                        c3, c4 = st.columns(2)
                        with c3:
                            if st.button("+0.5", key=f"p05_{idx_atual}", use_container_width=True):
                                st.session_state.cargas_sessao[chave] = carga_atual + 0.5
                                st.rerun()
                        with c4:
                            if st.button("+2.5", key=f"p25_{idx_atual}", use_container_width=True):
                                st.session_state.cargas_sessao[chave] = carga_atual + 2.5
                                st.rerun()
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

