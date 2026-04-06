import streamlit as st
import pandas as pd
from datetime import datetime
import calendar

st.set_page_config(page_title="Escala Pastoral Oficial", page_icon="⛪", layout="wide")

st.title("⛪ Gerador de Escala Pastoral")
st.write("Ajustado com regras de Pastorais, Crianças e Preferências.")

# --- SELEÇÃO DE DATA ---
col_data1, col_data2 = st.columns(2)
with col_data1:
    mes = st.selectbox("Selecione o Mês:", range(1, 13), index=datetime.now().month - 1)
with col_data2:
    ano = st.number_input("Ano:", value=2026)

upload = st.file_uploader("📂 Arraste aqui o arquivo CSV", type="csv")

if upload:
    df = pd.read_csv(upload)
    
    if st.button("🚀 Gerar Escala Final"):
        escala = []
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        
        for dia in range(1, dias_no_mes + 1):
            data_atual = datetime(ano, mes, dia)
            dia_semana = data_atual.weekday() 
            nome_dia = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][dia_semana]
            num_dom = (dia - 1) // 7 + 1
            
            missas_hoje = []
            
            # --- LÓGICA DE DOMINGOS ---
            if dia_semana == 6:
                for horario in ["07h30", "11h", "18h"]:
                    # Regra 3º Domingo 11h (Crianças)
                    if num_dom == 3 and horario == "11h":
                        missas_hoje.append({"h": horario, "vagas": 3, "fixo": "CRIANÇAS"})
                    # Regra 4º Domingo 07h30 e 18h (Família + Formulário)
                    elif num_dom == 4 and (horario == "07h30" or horario == "18h"):
                        missas_hoje.append({"h": horario, "vagas": 3, "tipo": "MistaFamília"})
                    else:
                        missas_hoje.append({"h": horario, "vagas": 3, "col": "Domingo"})
            
            # --- MISSAS SEMANAIS ---
            elif dia_semana == 0: missas_hoje.append({"h": "19h30", "vagas": 2, "col": "Segunda-feira 19h30 - Missa pelas almas"})
            elif dia_semana == 2: missas_hoje.append({"h": "19h30", "vagas": 1, "col": "Quarta-feira 19h30 - Clamando por Cura e Libertação"})
            elif dia_semana == 4: missas_hoje.append({"h": "19h30", "vagas": 2, "col": "Sexa-feira 19h30"})
            elif dia_semana == 5: missas_hoje.append({"h": "09h", "vagas": 2, "col": "Sábado 09h"})

            for m in missas_hoje:
                l1, l2, pr = "-", "-", "-"
                escolhidos = []

                # Se for escala totalmente fixa (Crianças)
                if "fixo" in m:
                    l1, l2, pr = m['fixo'], m['fixo'], m['fixo']
                
                # Se for escala mista (Pastoral Familiar + Preces do formulário)
                elif "tipo" in m and m['tipo'] == "MistaFamília":
                    l1, l2 = "PASTORAL FAMILIAR", "PASTORAL FAMILIAR"
                    # Busca 1 pessoa no formulário para preces
                    possiveis = df[df['Domingo'].astype(str).str.contains(m['h'], na=False)]
                    if not possiveis.empty:
                        pr = possiveis.iloc[0]['Nome']

                # Escala normal via formulário
                else:
                    # Preferência 2º Domingo 11h
                    if num_dom == 2 and m['h'] == "11h":
                        favoritos = ["Aline", "Zezinho", "Amorzinho", "Senhor"]
                        for fav in favoritos:
                            if len(escolhidos) < m['vagas'] and not df[df['Nome'].str.contains(fav, case=False, na=False)].empty:
                                escolhidos.append(fav)

                    # Preenchimento geral
                    col_busca = m.get('col', 'Domingo')
                    if col_busca in df.columns:
                        possiveis = df[df[col_busca].astype(str).str.contains(m['h'], na=False) | (df[col_busca] == "Sim")]
                        for _, row in possiveis.iterrows():
                            if len(escolhidos) < m['vagas'] and row['Nome'] not in escolhidos:
                                if str(dia) not in str(row['Quaisdias não pode servir']):
                                    escolhidos.append(row['Nome'])
                    
                    # Distribuição nas colunas conforme sua regra
                    if m['vagas'] == 1:
                        l1 = escolhidos[0] if escolhidos else "Pendente"
                    elif m['vagas'] == 2:
                        l1 = escolhidos[0] if len(escolhidos) > 0 else "Pendente"
                        pr = escolhidos[1] if len(escolhidos) > 1 else "Pendente"
                    else:
                        l1 = escolhidos[0] if len(escolhidos) > 0 else "Pendente"
                        l2 = escolhidos[1] if len(escolhidos) > 1 else "Pendente"
                        pr = escolhidos[2] if len(escolhidos) > 2 else "Pendente"

                escala.append({
                    "Data": data_atual.strftime("%d/%m"),
                    "Dia": nome_dia,
                    "Horário": m['h'],
                    "1ª Leitura": l1,
                    "2ª Leitura": l2,
                    "Preces": pr
                })

        st.subheader("📊 Sugestão de Escala Equilibrada")
        st.table(pd.DataFrame(escala))
