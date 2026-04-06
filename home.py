import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import io

st.set_page_config(page_title="Escala Pastoral Fatima", page_icon="⛪", layout="wide")

st.title("⛪ Gerador de Escala - Paróquia N. Sra. de Fátima")

# --- ENTRADA DE DADOS ---
col1, col2, col3 = st.columns(3)
with col1:
    mes = st.selectbox("Mês:", range(1, 13), index=datetime.now().month - 1)
with col2:
    ano = st.number_input("Ano:", value=2026)
with col3:
    cor_padrao = st.selectbox("Cor Litúrgica:", ["Verde", "Roxo", "Branco", "Vermelho", "Rosa"])

upload = st.file_uploader("📂 Arraste o CSV aqui", type="csv")

if upload:
    df = pd.read_csv(upload)
    
    # Limpa nomes de colunas (tira espaços extras)
    df.columns = df.columns.str.strip()

    if st.button("🚀 Gerar Escala Completa"):
        escala = []
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        
        for dia in range(1, dias_no_mes + 1):
            data_atual = datetime(ano, mes, dia)
            dia_semana = data_atual.weekday()
            nome_dia = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][dia_semana]
            num_dom = (dia - 1) // 7 + 1
            
            missas_hoje = []
            destaque = ""

            if dia_semana == 6:
                if num_dom == 1: destaque = "1º DOMINGO"
                elif num_dom == 2: destaque = "2º DOMINGO - DIZIMISTAS"
                elif num_dom == 3: destaque = "3º DOMINGO - CRIANÇAS"
                elif num_dom == 4: destaque = "4º DOMINGO - FAMÍLIAS"
                
                for h in ["07h30", "11h", "18h"]:
                    if num_dom == 3 and h == "11h": missas_hoje.append({"h": h, "v": 3, "fixo": "CRIANÇAS", "dest": destaque})
                    elif num_dom == 4 and (h == "07h30" or h == "18h"): missas_hoje.append({"h": h, "v": 3, "tipo": "MistaFamília", "dest": destaque})
                    else: missas_hoje.append({"h": h, "v": 3, "col": "Domingo", "dest": destaque})
            
            elif dia_semana == 0: missas_hoje.append({"h": "19h30", "v": 2, "col": "Segunda-feira 19h30 - Missa pelas almas"})
            elif dia_semana == 1 and num_dom == 1: missas_hoje.append({"h": "15h", "v": 1, "col": "Terça-feira (Missa pela Saúde)"})
            elif dia_semana == 2: missas_hoje.append({"h": "19h30", "v": 1, "col": "Quarta-feira 19h30 - Clamando por Cura e Libertação"})
            elif dia_semana == 4: missas_hoje.append({"h": "19h30", "v": 2, "col": "Sexa-feira 19h30"})
            elif dia_semana == 5: missas_hoje.append({"h": "09h", "v": 2, "col": "Sábado 09h"})

            for m in missas_hoje:
                l1, l2, pr = "-", "-", "-"
                escolhidos = []

                if "fixo" in m:
                    l1 = l2 = pr = m['fixo']
                elif "tipo" in m and m['tipo'] == "MistaFamília":
                    l1 = l2 = "PASTORAL FAMILIAR"
                    if 'Domingo' in df.columns:
                        possiveis = df[df['Domingo'].astype(str).str.contains(m['h'], na=False)]
                        if not possiveis.empty: pr = possiveis.iloc[0]['Nome']
                else:
                    col_busca = m.get('col', 'Domingo')
                    # Só tenta buscar se a coluna realmente existir
                    if col_busca in df.columns:
                        possiveis = df[df[col_busca].astype(str).str.contains(m['h'], na=False)]
                        for _, row in possiveis.iterrows():
                            if len(escolhidos) < m['v'] and row['Nome'] not in escolhidos:
                                escolhidos.append(row['Nome'])
                    
                    if m['v'] == 1: l1 = escolhidos[0] if escolhidos else "Pendente"
                    elif m['v'] == 2: 
                        l1 = escolhidos[0] if len(escolhidos) > 0 else "Pendente"
                        pr = escolhidos[1] if len(escolhidos) > 1 else "Pendente"
                    else:
                        l1 = escolhidos[0] if len(escolhidos) > 0 else "Pendente"
                        l2 = escolhidos[1] if len(escolhidos) > 1 else "Pendente"
                        pr = escolhidos[2] if len(escolhidos) > 2 else "Pendente"

                escala.append({
                    "Destaque": m.get('dest', ""),
                    "Data": data_atual.strftime("%d/%m"),
                    "Dia": nome_dia,
                    "Horário": m['h'],
                    "Cor": cor_padrao,
                    "1ª Leitura": l1,
                    "2ª Leitura": l2,
                    "Preces": pr
                })

        df_final = pd.DataFrame(escala)
        st.table(df_final)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False)
        st.download_button("📥 Baixar Excel", buffer.getvalue(), "escala.xlsx")
