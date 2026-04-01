import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
import time
import base64

# --- FUNÇÃO PARA CARREGAR A LOGO QUE VOCÊ SUBIU ---
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

try:
    img_base64 = get_base64_image("JV Ferreira logo.jpeg")
    logo_url = f"data:image/jpeg;base64,{img_base64}"
except:
    # Caso o arquivo não seja encontrado, ele tenta o link do Drive como backup
    logo_url = "https://drive.google.com/uc?export=view&id=1oIpYQkIp4Y0M0vumaR5Tpa0yVDwSF7mc"   

# --- 1. CONFIGURAÇÃO E CSS (RESTALREI O ORIGINAL 100%) ---
st.set_page_config(page_title="JV PERFORMANCE", page_icon="💪", layout="centered")

URL_PLANILHA = "SUA_URL_AQUI"
EMAIL_COACH = "jaaovictor96@gmail.com"

conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Space+Grotesk:wght@700;900&display=swap');
    
    .stApp {{
        background: linear-gradient(rgba(19, 19, 19, 0.94), rgba(19, 19, 19, 0.94)), 
                    url('{logo_url}');
        background-size: contain !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }}

    [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: transparent !important;
    }}

    .main-title {{
        color: #F9C03D !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 900 !important;
        letter-spacing: -1px !important;
        line-height: 1 !important;
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

    .exercise-card {{
        background-color: rgba(32, 31, 31, 0.9) !important;
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #F9C03D;
        margin-bottom: 15px;
    }}

    input {{ background-color: #201f1f !important; color: white !important; border: 1px solid #333 !important; border-radius: 8px !important; }}
    
    div.stButton > button {{
        background-color: transparent !important; 
        color: #ffffff !important; 
        border: 1px solid #ffffff !important;
        border-radius: 8px; 
        padding: 10px 60px !important; 
        font-weight: bold; 
        display: block !important; 
        margin: 0 auto !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DE ESTADO ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.email = ""

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.markdown("<h1 class='main-title'>TEAM <br> JV FERREIRA</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>AESTHETIC & PERFORMANCE LAB<br>CONSULTORIA ONLINE</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        email_input = st.text_input("📧 E-mail do Atleta", placeholder="atleta@exemplo.com").strip().lower()
        senha_input = st.text_input("🔒 Senha", type="password", placeholder="••••••").strip()
        
        if st.button("ACESSAR"):
            try:
                # Tenta ler os usuários. Se falhar, espera 1 segundo e tenta de novo uma única vez.
                try:
                    usuarios = conn.read(worksheet="usuarios")
                except:
                    import time
                    time.sleep(1) # Pequena pausa para estabilizar a conexão
                    usuarios = conn.read(worksheet="usuarios")
                
                usuarios['email'] = usuarios['email'].astype(str).str.strip().str.lower()
                usuarios['senha'] = usuarios['senha'].astype(str).str.strip()
                
                if ((usuarios['email'] == email_input) & (usuarios['senha'] == senha_input)).any():
                    st.session_state.logado = True
                    st.session_state.email = email_input
                    st.rerun()
                else: 
                    st.error("Credenciais inválidas.")
            except Exception as e: 
                st.error("Instabilidade na rede. Tente clicar novamente em 1 segundo.")

# --- ÁREA LOGADA ---
else:
    # Cabeçalho Fixo da Área Interna
    st.markdown("<h1 class='main-title' style='font-size: 1.5rem !important; text-align: left !important;'>JV PERFORMANCE</h1>", unsafe_allow_html=True)
    
    # Sidebar
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()
    
    st.sidebar.divider()
    with st.sidebar.expander("🔑 Alterar Minha Senha"):
        nova_senha = st.text_input("Nova Senha", type="password", key="new_pass")
        confirma_senha = st.text_input("Confirme a Nova Senha", type="password", key="conf_pass")
        
        if st.button("ATUALIZAR SENHA"):
            if nova_senha == confirma_senha and len(nova_senha) >= 4:
                try:
                    # 1. Lê a base de usuários atual
                    df_usuarios = conn.read(worksheet="usuarios", ttl=0)
                    
                    # 2. Localiza o usuário logado e altera a senha no DataFrame
                    mask = df_usuarios['email'].astype(str).str.strip().str.lower() == st.session_state.email.lower()
                    
                    if mask.any():
                        df_usuarios.loc[mask, 'senha'] = str(nova_senha).strip()
                        
                        # 3. Sobe a planilha inteira atualizada
                        conn.update(worksheet="usuarios", data=df_usuarios)
                        st.sidebar.success("Senha alterada com sucesso!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.sidebar.error("Usuário não encontrado.")
                except Exception as e:
                    st.sidebar.error(f"Erro ao conectar: {e}")
            elif len(nova_senha) < 4:
                st.sidebar.warning("A senha deve ter pelo menos 4 caracteres.")
            else:
                st.sidebar.error("As senhas não coincidem.")

    # Lógica de troca de tela para o Coach
    ativar_dashboard = False
    if st.session_state.email == EMAIL_COACH:
        st.sidebar.divider()
        st.sidebar.subheader("🛠 PAINEL DO COACH")
        ativar_dashboard = st.sidebar.checkbox("Visualizar Métricas")

    # --- ESCOLHA DE TELA (O QUE APARECE NO CENTRO) ---
    if ativar_dashboard:
        # ==========================
        # TELA: DASHBOARD COACH
        # ==========================
        st.markdown("<h2 style='font-family: Space Grotesk; color: #F9C03D;'>ANÁLISE DE PERFORMANCE</h2>", unsafe_allow_html=True)
        
        # 1. Lemos as abas necessárias
        df_usuarios = conn.read(worksheet="usuarios", ttl=0)
        df_coach = conn.read(worksheet="registros", ttl=0)
        
        if not df_usuarios.empty:
            # Criamos uma lista de nomes para o selectbox
            # (Removemos valores nulos e garantimos que sejam strings)
            lista_nomes = df_usuarios['nome'].dropna().unique().tolist()
            
            nome_sel = st.selectbox("Selecione o Aluno:", lista_nomes)
            
            # 2. Descobrimos o e-mail vinculado ao nome selecionado
            email_vinculado = df_usuarios[df_usuarios['nome'] == nome_sel]['email'].iloc[0].strip().lower()
            
            if not df_coach.empty:
                df_coach['email_aluno'] = df_coach['email_aluno'].astype(str).str.strip().str.lower()
                
                # Filtramos os registros pelo e-mail que acabamos de encontrar
                df_aluno = df_coach[df_coach['email_aluno'] == email_vinculado].copy()
                
                if not df_aluno.empty:
                    df_aluno['data'] = pd.to_datetime(df_aluno['data'], dayfirst=True)
                    
                    exercicio_sel = st.selectbox("Exercício:", df_aluno['exercicio'].unique())
                    df_prog = df_aluno[df_aluno['exercicio'] == exercicio_sel].sort_values('data')
                    
                    fig = px.line(df_prog, x='data', y='carga', title=f'Progressão: {exercicio_sel}', markers=True)
                    fig.update_traces(line_color='#F9C03D')
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
                    fig.update_xaxes(title_text='Data', tickformat='%d/%m/%Y')
                    fig.update_yaxes(title_text='Carga (kg)')   
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"O(A) atleta {nome_sel} ainda não registrou nenhum treino.")
            else:
                st.warning("A base de registros está vazia.")
        else:
            st.error("Nenhum usuário encontrado na aba 'usuarios'.")

    else:
        # ==========================
        # TELA: PROTOCOLO DIÁRIO (ORIGINAL)
        # ==========================
        st.markdown("<h2 style='font-family: Space Grotesk; font-size: 2.5rem; font-weight: 900; line-height: 1;'>PROTOCOLO <br><span style='color: #F9C03D;'>DIÁRIO</span></h2>", unsafe_allow_html=True)
        
        if st.button("🔄 ATUALIZAR PLANILHA"):
            st.cache_data.clear()
            st.rerun()

        try:
            # Carregamento de dados (seu código original de treino)
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

                        st.markdown(f"""
                            <div class="exercise-card">
                                <p style="color: #F9C03D; font-size: 10px; font-weight: bold; margin: 0;">{selecao_treino}</p>
                                <h4 style="margin: 5px 0; color: white; font-family: Space Grotesk; text-transform: uppercase;">{row['exercicio']}</h4>
                                <p style="color: #888; font-size: 12px; margin: 0;"> META: {int(float(row['series'])) if pd.notnull(row['series']) else 0} SÉRIES x {int(float(row['reps'])) if pd.notnull(row['reps']) else 0} REPS</p>
                                <p style="color: #F9C03D; font-size: 11px; margin-top: 5px; opacity: 0.8;">Última carga: {carga_anterior} kg</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        video_url = row.get('video_url', '') 
                        if pd.notnull(video_url) and str(video_url).startswith('http'):
                            video_embed = video_url.split('?')[0].replace('/view', '/preview').replace('/edit', '/preview')
                            with st.expander("🎬 VER EXECUÇÃO"):
                                st.components.v1.html(f'<iframe src="{video_embed}" width="100%" height="200" frameborder="0"></iframe>', height=210)

                        carga = st.number_input(
                        f"Carga (kg) - {row['exercicio']}", 
                        key=f"kg_{idx}", 
                        step=0.5,         
                        min_value=0.0,    
                        value=carga_anterior
)
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
