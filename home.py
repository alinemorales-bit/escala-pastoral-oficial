import streamlit as st
import pandas as pd
from datetime import datetime
import calendar

# Configuração da página - Equilibrada e Leve
st.set_page_config(page_title="Escala Pastoral", page_icon="⛪", layout="wide")

st.title("⛪ Gerador de Escala Pastoral")
st.write("Olá! Vamos organizar a escala do mês de forma prática.")

# --- SELEÇÃO DE DATA ---
col1, col2 = st.columns(2)
with col1:
    mes = st.selectbox("Selecione o Mês:", range(1, 13), index=datetime.now().month - 1)
with col2:
    ano = st.number_input("Ano:", value=2026)

# --- UPLOAD DO ARQUIVO ---
upload = st.file_uploader("📂 Arraste aqui o arquivo de respostas (CSV)", type="csv")

if upload:
    df = pd.read_csv(upload)
    st.success(f"Legal! Carregamos {len(df)} respostas.")

    if st.button("🚀 Gerar Escala"):
        escala = []
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        
        for dia in range(1, dias_no_mes + 1):
            data_atual = datetime(ano, mes, dia)
            dia_semana = data_atual.weekday() # 0=Seg, 6=Dom
            nome_dia = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"][dia_semana]
            
            missas_hoje = []
            
            # REGRAS DE DOMINGO
            if dia_semana == 6: 
                num_dom = (dia - 1) // 7 + 1
                if num_dom != 3: # 3º Domingo não tem escala
                    vagas = 3 if num_dom != 4 else 1 
                    missas_hoje.append({"h": "07h30", "vagas": vagas, "col": "Domingo"})
                    missas_hoje.append({"h": "11h", "vagas": 3, "col": "Domingo"})
                    missas_hoje.append({"h": "18h", "vagas": vagas, "col": "Domingo"})
            
            # MISSAS SEMANAIS
            elif dia_semana == 0: missas_hoje.append({"h": "19h30", "vagas": 2, "col": "Segunda-feira 19h30 - Missa pelas almas"})
            elif dia_semana == 2: missas_hoje.append({"h": "19h30", "vagas": 1, "col": "Quarta-feira 19h30 - Clamando por Cura e Libertação"})
            elif dia_semana == 4: missas_hoje.append({"h": "19h30", "vagas": 2, "col": "Sexa-feira 19h30"})
            elif dia_semana == 5: missas_hoje.append({"h": "09h", "vagas": 2, "col": "Sábado 09h"})
            
            # ESCALONAMENTO
            for m in missas_hoje:
                escolhidos = []
                
                # Regra 2º Domingo 11h (Prioridades)
                if dia_semana == 6 and (dia - 1) // 7 + 1 == 2 and m['h'] == "11h":
                    favoritos = ["Aline", "Zezinho", "Amorzinho", "Senhor"]
                    for fav in favoritos:
                        if len(escolhidos) < m['vagas']:
                            if not df[df['Nome'].str.contains(fav, case=False, na=False)].empty:
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
                
                escala.append({
                    "Data": data_atual.strftime("%d/%m"),
                    "Dia": nome_dia,
                    "Missa": m['h'],
                    "Leitores": ", ".join(escolhidos) if escolhidos else "Pendente"
                })

        # EXIBIÇÃO
        st.subheader(f"📊 Sugestão de Escala")
        df_escala = pd.DataFrame(escala)
        st.table(df_escala)
        
        csv = df_escala.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Escala", csv, "escala.csv", "text/csv")
