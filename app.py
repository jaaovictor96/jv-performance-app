import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

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

EMAIL_COACH = "jaaovictor96@gmail.com"

# --- NA SIDEBAR ---
st.sidebar.divider()

# Verificamos se o e-mail logado é o seu (limpando espaços e letras maiúsculas)
email_logado = st.session_state.get('email', '').strip().lower()

if email_logado == EMAIL_COACH.lower():
    st.sidebar.subheader("🛠 PAINEL DO COACH")
    acesso_coach = st.sidebar.checkbox("Visualizar Métricas")
    
    if acesso_coach:
        st.markdown("### 📊 CENTRAL DE PERFORMANCE JV")
        
        # 1. Carregar dados de registros
        df_coach = conn.read(worksheet="registros", ttl=0)
        
        if not df_coach.empty:
            # Filtros de busca
            lista_alunos = df_coach['email_aluno'].unique()
            aluno_sel = st.selectbox("Selecione o Aluno:", lista_alunos)
            
            # Filtrar dados do aluno selecionado
            df_aluno = df_coach[df_coach['email_aluno'] == aluno_sel].copy()
            df_aluno['data'] = pd.to_datetime(df_aluno['data'], dayfirst=True)
            
            # --- KPIs RÁPIDOS ---
            col1, col2 = st.columns(2)
            with col1:
                total_treinos = df_aluno['data'].dt.date.nunique()
                st.metric("Treinos Realizados", total_treinos)
            with col2:
                ultimo_treino = df_aluno['data'].max().strftime('%d/%m/%Y')
                st.metric("Último Check-in", ultimo_treino)

            # --- GRÁFICO DE PROGRESSÃO ---
            st.markdown("### Progressão por Exercício")
            exercicio_sel = st.selectbox("Escolha o Exercício:", df_aluno['exercicio'].unique())
            
            df_progresso = df_aluno[df_aluno['exercicio'] == exercicio_sel].sort_values('data')
            
            fig = px.line(
                df_progresso, 
                x='data', 
                y='carga',
                title=f'Evolução: {exercicio_sel}',
                markers=True,
                line_shape='spline',
                color_discrete_sequence=['#F9C03D'] # Usando o seu amarelo padrão
            )
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color="white",
                xaxis_title="Data do Treino",
                yaxis_title="Carga (kg)"
            )
            
            st.plotly_chart(fig, use_container_width=True)

            # --- TABELA DE NOTAS/COMENTÁRIOS ---
            with st.expander("📝 Ver Comentários do Atleta"):
                df_notas = df_aluno[df_aluno['comentario'].str.len() > 2][['data', 'comentario']].drop_duplicates()
                st.table(df_notas)
        else:
            st.info("Ainda não há registros para analisar.")
    else:
        st.warning("Aguardando senha correta...")          
        
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
    # Botão de atualizar manual (discreto no estilo do seu app)
    if st.button("🔄 ATUALIZAR PLANILHA"):
        st.cache_data.clear() # Limpa todo o cache do app
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
                
                    # MONTAGEM DA LINHA (Garantindo que os dados entrem na lista)
                    dados_exercicio = {
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "email_aluno": st.session_state.email,
                        "treino": selecao_treino,
                        "exercicio": row['exercicio'],
                        "carga": carga
                    }
                    lista_registros.append(dados_exercicio)

                # --- ÁREA FINAL DO FORMULÁRIO (NOTAS E ENVIO) ---
                notas = st.text_area("Notas do Atleta", placeholder="Como foi o treino hoje? Dificuldade, cansaço, etc.")

                if st.form_submit_button("FINALIZAR TREINO"):
                    try:
                        # 1. Monta o DataFrame do envio atual com TODAS as colunas explicitamente
                        df_envio = pd.DataFrame(lista_registros)
                        df_envio["comentario"] = notas
                        
                        # Garantimos a ordem das colunas para não bagunçar o Sheets
                        colunas_padrao = ["data", "email_aluno", "treino", "exercicio", "carga", "comentario"]
                        df_envio = df_envio.reindex(columns=colunas_padrao)

                        # 2. Tenta ler o histórico para anexar (TTL=0)
                        try:
                            existente = conn.read(worksheet="registros", ttl=0)
                            if existente is not None and not existente.empty:
                                # Filtra apenas colunas que nos interessam e remove linhas vazias
                                existente = existente[colunas_padrao].dropna(how='all')
                                df_final = pd.concat([existente, df_envio], ignore_index=True)
                            else:
                                df_final = df_envio
                        except:
                            # Se a aba estiver vazia ou der erro na leitura, inicia com o envio atual
                            df_final = df_envio

                        # 3. COMANDO DE ATUALIZAÇÃO (Sobrescreve a aba com a tabela completa)
                        conn.update(worksheet="registros", data=df_final)
                        
                        # 4. LIMPEZA DE CACHE E FEEDBACK
                        st.cache_data.clear()
                        st.success("✅ TREINO REGISTRADO!")
                        st.balloons()
                        
                        import time
                        time.sleep(2)
                        st.rerun()

                    except Exception as e:
                        st.error(f"Erro ao gravar: {e}")

    except Exception as e: st.error(f"Erro ao carregar dados: {e}")
