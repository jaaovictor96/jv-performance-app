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
