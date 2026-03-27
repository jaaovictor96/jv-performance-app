import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="JV PERFORMANCE", page_icon="💪", layout="centered")
URL_PLANILHA = "SUA_URL_AQUI"
conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)

# --- CSS TEAM JV FERREIRA ---
st.markdown("""
    <style>
    .stApp { background-color: #131313; color: #e5e2e1; }
    .main-title { color: #F9C03D !important; font-family: 'Space Grotesk'; font-weight: 900; text-align: center; text-transform: uppercase; font-size: 2.2rem !important; }
    .exercise-card { background-color: #201f1f; padding: 15px; border-radius: 10px; border-left: 4px solid #F9C03D; margin-bottom: 10px; }
    .last-load { color: #888; font-size: 0.85rem; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.email = ""

# --- LOGIN ---
if not st.session_state.logado:
    st.markdown("<h1 class='main-title'>TEAM JV FERREIRA</h1>", unsafe_allow_html=True)
    email_input = st.text_input("📧 E-mail do Atleta").strip().lower()
    senha_input = st.text_input("🔒 Senha", type="password")
    
    if st.button("ACESSAR"):
        usuarios = conn.read(worksheet="usuarios")
        if ((usuarios['email'].str.lower() == email_input) & (usuarios['senha'].astype(str) == senha_input)).any():
            st.session_state.logado = True
            st.session_state.email = email_input
            st.rerun()
        else:
            st.error("Acesso negado.")

# --- ÁREA LOGADA ---
else:
    # DEFINA SEU E-MAIL AQUI PARA ACESSAR O DASHBOARD
    E_MAIL_TREINADOR = "seu-email@exemplo.com"
    eh_treinador = (st.session_state.email == E_MAIL_TREINADOR)

    st.sidebar.markdown(f"**Atleta:** {st.session_state.email}")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # CARREGANDO DADOS HISTÓRICOS PARA CONSULTA
    try:
        df_hist = conn.read(worksheet="registros")
        # Converte data para formato datetime para ordenar corretamente
        df_hist['data_dt'] = pd.to_datetime(df_hist['data'], dayfirst=True, errors='coerce')
    except:
        df_hist = pd.DataFrame()

    # --- VISÃO DO TREINADOR ---
    if eh_treinador:
        st.markdown("<h1 class='main-title'>DASHBOARD MASTER</h1>", unsafe_allow_html=True)
        
        if not df_hist.empty:
            lista_alunos = df_hist['email_aluno'].unique()
            aluno_sel = st.selectbox("Selecione o Aluno para Monitorar:", lista_alunos)
            
            dados_aluno = df_hist[df_hist['email_aluno'] == aluno_sel].sort_values('data_dt')
            
            col1, col2 = st.columns(2)
            col1.metric("Total de Treinos", len(dados_aluno['data'].unique()))
            col2.metric("Último Registro", dados_aluno['data'].iloc[-1] if not dados_aluno.empty else "N/A")
            
            st.markdown("### Histórico de Cargas")
            st.dataframe(dados_aluno[['data', 'exercicio', 'carga']].sort_values('data', ascending=False), use_container_width=True)
        else:
            st.info("Nenhum registro encontrado na planilha.")

    # --- VISÃO DO ALUNO ---
    else:
        st.markdown("<h2 style='color:#F9C03D; font-family:Space Grotesk;'>DAILY PROTOCOL</h2>", unsafe_allow_html=True)

        try:
            df_treinos = conn.read(worksheet="planilha_treinos")
            meus_treinos = df_treinos[df_treinos['email_aluno'].str.lower() == st.session_state.email]
            
            if not meus_treinos.empty:
                selecao = st.selectbox("Escolha o treino:", meus_treinos['treino_nome'].unique())
                exercicios = meus_treinos[meus_treinos['treino_nome'] == selecao]
                
                with st.form("registro_treino"):
                    regs = []
                    for i, row in exercicios.iterrows():
                        # Lógica para buscar a ÚLTIMA CARGA usada
                        carga_anterior = "N/A"
                        if not df_hist.empty:
                            hist_ex = df_hist[(df_hist['email_aluno'] == st.session_state.email) & 
                                              (df_hist['exercicio'] == row['exercicio'])]
                            if not hist_ex.empty:
                                carga_anterior = hist_ex.sort_values('data_dt').iloc[-1]['carga']

                        st.markdown(f"""
                            <div class='exercise-card'>
                                <b>{row['exercicio']}</b><br>
                                <small>META: {int(float(row['series']))}x{str(row['reps']).replace('.0','')}</small><br>
                                <span class='last-load'>Última vez: {carga_anterior} kg</span>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        carga = st.number_input(f"Carga Atual (kg) - {row['exercicio']}", key=f"kg_{i}", step=0.5)
                        regs.append({
                            "data": datetime.now().strftime("%d/%m/%Y"), 
                            "email_aluno": st.session_state.email, 
                            "exercicio": row['exercicio'], 
                            "carga": carga
                        })
                    
                    if st.form_submit_button("FINALIZAR PROTOCOLO"):
                        df_final = pd.concat([df_hist.drop(columns=['data_dt'], errors='ignore'), pd.DataFrame(regs)], ignore_index=True)
                        conn.update(worksheet="registros", data=df_final)
                        st.success("Dados enviados! Evolução registrada.")
                        st.rerun()

            # --- GRÁFICO DE EVOLUÇÃO ---
            st.markdown("---")
            st.markdown("### 📈 PERFORMANCE ANALYTICS")
            
            meu_hist = df_hist[df_hist['email_aluno'].str.lower() == st.session_state.email]
            
            if not meu_hist.empty and len(meu_hist) > 0:
                ex_foco = st.selectbox("Analisar Evolução de:", meu_hist['exercicio'].unique())
                dados_grafico = meu_hist[meu_hist['exercicio'] == ex_foco].sort_values('data_dt')

                fig = px.line(dados_grafico, x='data_dt', y='carga', markers=True, title=f"Progressão: {ex_foco}")
                fig.update_traces(line_color='#F9C03D', marker=dict(size=10, color='#F9C03D'))
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#e5e2e1', xaxis_title="Data", yaxis_title="Carga (kg)",
                    xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#333')
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("O gráfico aparecerá aqui após o primeiro envio de cargas.")

        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
