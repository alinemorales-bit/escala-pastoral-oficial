import streamlit as st
import pandas as pd
from datetime import datetime
import calendar

# Configuração da página - Limpa e Organizada
st.set_page_config(page_title="Escala Pastoral", page_icon="⛪", layout="wide")

st.title("⛪ Gerador de Escala Pastoral")
st.write("Organize as leituras do mês de forma equilibrada e visual.")

# --- SELEÇÃO DE DATA ---
col_data1, col_data2 = st.columns(2)
with col_data1:
    mes = st.selectbox("Selecione o Mês:", range(1, 13), index=datetime.now().month - 1)
with col_data2:
    ano = st.number_input("Ano:", value=2026)

upload = st.file_uploader("📂 Arraste aqui o arquivo de respostas (CSV)", type="csv")

if upload:
    df = pd.read_csv(upload)
    st.success(f"Legal! Carregamos {len(df)} respostas.")

    if st.button("🚀 Gerar Escala"):
        escala = []
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        
        for dia in range(1, dias_no_mes + 1):
            data_atual = datetime(ano, mes, dia)
            dia_semana = data_atual.weekday() 
            nome_dia = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][dia_semana]
            
            missas_hoje = []
            
            # REGRAS DE DOMINGO (Sempre 3 leitores, exceto 4º domingo que é 1)
            if dia_semana == 6: 
                num_dom = (dia - 1) // 7 + 1
                if num_dom != 3: 
                    vagas = 3 if num_dom != 4 else 1 
                    missas_hoje.append({"h": "07h30", "vagas": vagas, "col": "Domingo"})
                    missas_hoje.append({"h": "11h", "vagas": 3, "col": "Domingo"})
                    missas_hoje.append({"h": "18h", "vagas": vagas, "col": "Domingo"})
            
            # MISSAS SEMANAIS
            elif dia_semana == 0: missas_hoje.append({"h": "19h30", "vagas": 2, "col": "Segunda-feira 19h30 - Missa pelas almas"})
            elif dia_semana == 2: missas_hoje.append({"h": "19h30", "vagas": 1, "col": "Quarta-feira 19h30 - Clamando por Cura e Libertação"})
            elif dia_semana == 4: missas_hoje.append({"h": "19h30", "vagas": 2, "col": "Sexa-feira 19h30"})
            elif dia_semana == 5: missas_hoje.append({"h": "09h", "vagas": 2, "col": "Sábado 09h"})
            
            for m in missas_hoje:
                escolhidos = []
                
                # Prioridade 2º Domingo 11h
                if dia_semana == 6 and (dia - 1) // 7 + 1 == 2 and m['h'] == "11h":
                    favoritos = ["Aline", "Zezinho", "Amorzinho", "Senhor"]
                    for fav in favoritos:
                        if len(escolhidos) < m['vagas'] and not df[df['Nome'].str.contains(fav, case=False, na=False)].empty:
                            escolhidos.append(fav)

                # Preenchimento Geral
                if m['col'] in df.columns:
                    possiveis = df[df[m['col']].astype(str).str.contains(m['h'], case=False, na=False) | (df[m['col']] == "Sim")]
                    for _, row in possiveis.iterrows():
                        if len(escolhidos) < m['vagas']:
                            nome = row['Nome']
                            obs = str(row['Quaisdias não pode servir'])
                            if str(dia) not in obs and nome not in escolhidos:
                                escolhidos.append(nome)
                
                # Organização das colunas
                leitura1 = escolhidos[0] if len(escolhidos) > 0 else "-"
                leitura2 = escolhidos[1] if len(escolhidos) > 1 else "-"
                preces = escolhidos[2] if len(escolhidos) > 2 else "-"
                
                # Ajuste para dias com apenas 1 ou 2 leitores
                if m['vagas'] == 1:
                    preces, leitura1 = leitura1, "-" # Em missas de 1 pessoa, ela faz as preces
                
                escala.append({
                    "Data": data_atual.strftime("%d/%m"),
                    "Dia": nome_dia,
                    "Horário": m['h'],
                    "1ª Leitura": leitura1,
                    "2ª Leitura": leitura2,
                    "Preces": preces
                })

        # EXIBIÇÃO DA TABELA
        st.subheader(f"📊 Sugestão de Escala")
        df_escala = pd.DataFrame(escala)
        st.table(df_escala)
        
        csv = df_escala.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Escala em Excel/CSV", csv, "escala_pastoral.csv", "text/csv")
