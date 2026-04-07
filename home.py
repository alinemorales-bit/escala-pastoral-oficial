import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import io
import random
import re

st.set_page_config(page_title="Escala Pastoral Fatima", page_icon="⛪", layout="wide")

st.title("⛪ Gerador de Escala - Paróquia N. Sra. de Fátima")

# Seleção de Mês e Ano
col1, col2 = st.columns(2)
with col1:
    mes = st.selectbox("Mês:", range(1, 13), index=datetime.now().month - 1)
with col2:
    ano = st.number_input("Ano:", value=2026)

upload = st.file_uploader("📂 Arraste o CSV aqui", type="csv")

if upload:
    # Carregamento robusto do CSV
    try:
        df = pd.read_csv(upload, sep=None, engine='python', encoding='utf-8-sig')
    except:
        upload.seek(0)
        df = pd.read_csv(upload, sep=';', encoding='latin1')

    # Limpeza de colunas (Remove acentos, espaços e deixa minúsculo)
    def normalizar(txt):
        return str(txt).strip().lower().normalize('NFKD').encode('ascii', errors='ignore').decode('utf-8')

    df.columns = [normalizar(c) for c in df.columns]
    df = df.map(lambda x: str(x).strip() if pd.notnull(x) else "")

    def localizar_coluna(termo):
        for col in df.columns:
            if termo in col: return col
        return None

    if st.button("🚀 Gerar Escala Completa"):
        escala = []
        col_nome = localizar_coluna("nome")
        nomes_unicos = list(df[col_nome].unique())
        contagem = {nome: 0 for nome in nomes_unicos}
        
        _, ultimo_dia = calendar.monthrange(ano, mes)

        for dia in range(1, ultimo_dia + 1):
            dt = datetime(ano, mes, dia)
            sem = dt.weekday() # 0=Segunda, 6=Domingo
            data_str = dt.strftime("%d/%m")
            nome_dia = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"][sem]
            exibir_dia = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"][sem]
            num_dom = (dia - 1) // 7 + 1
            
            # --- Definição da Missa ---
            missa = ""
            if sem == 0: missa = "Missa pelas Almas"
            elif sem == 1 and num_dom == 1: missa = "Missa pela Saúde (15h)"
            elif sem == 2: missa = "Cura e Libertação"
            elif dia == 13: missa = "N. Sra. Fátima"
            elif sem == 5: missa = "Devocional Maria"
            elif any(d in data_str for d in ["16/03", "17/03", "18/03"]): missa = "Tríduo São José"
            elif "19/03" in data_str: missa = "Solenidade São José"

            # Cabeçalho de Domingo
            if sem == 6:
                titulos = {1:"1º DOMINGO", 2:"2º DOMINGO", 3:"3º DOMINGO", 4:"4º DOMINGO", 5:"5º DOMINGO"}
                escala.append({"Data": titulos.get(num_dom), "Dia": "", "Missa": "", "Cor": "", "Hora": "", "1ª Leitura": "", "2ª Leitura": "", "Prece": ""})

            # --- Horários e Vagas ---
            horarios = ["07h30", "11h", "18h"] if sem == 6 else (["15h"] if "15h" in missa else (["19h30"] if missa or sem in [0,2,4] else []))
            
            for idx_h, h in enumerate(horarios):
                vagas = 3 if sem == 6 else 2
                if "cura" in missa.lower(): vagas = 1
                
                # Sorteio Aline/Natalia/Jefferson (2º Dom 11h)
                l1_fixo = None
                if num_dom == 2 and sem == 6 and h == "11h":
                    prios = [p for p in ["Aline", "Natalia", "Jefferson", "Natalia "] if p in contagem]
                    if prios:
                        random.shuffle(prios)
                        prios.sort(key=lambda x: contagem[x])
                        l1_fixo = prios[0]

                # Busca candidatos
                col_dia = localizar_coluna(data_str) or localizar_coluna(nome_dia)
                candidatos = []
                if col_dia:
                    # Filtra quem marcou "Sim" ou o horário no Domingo
                    if sem == 6:
                        mask = df[col_dia].str.contains(h, na=False)
                    else:
                        mask = df[col_dia].str.contains("sim", na=False, case=False)
                    
                    for _, row in df[mask].iterrows():
                        n = row[col_nome]
                        imp = str(row.get(localizar_coluna("nao pod"), "")).lower()
                        if not re.search(rf"\b0?{dia}\b", imp):
                            candidatos.append(n)

                random.shuffle(candidatos)
                candidatos.sort(key=lambda x: contagem[x])

                escolhidos = []
                if l1_fixo: 
                    escolhidos.append(l1_fixo)
                    if l1_fixo in candidatos: candidatos.remove(l1_fixo)
                
                for c in candidatos:
                    if len(escolhidos) < vagas: escolhidos.append(c)

                # Atualiza peso
                for e in escolhidos: contagem[e] += 1

                # Monta Linha
                linha = {
                    "Data": data_str if (sem != 6 or idx_h == 0) else "",
                    "Dia": exibir_dia if (sem != 6 or idx_h == 0) else "",
                    "Missa": missa if (sem != 6 or idx_h == 0) else "",
                    "Cor": "Verde", "Hora": h,
                    "1ª Leitura": escolhidos[0] if len(escolhidos) > 0 else "Pendente",
                    "2ª Leitura": "", "Prece": ""
                }
                
                if vagas == 2:
                    linha["Prece"] = escolhidos[1] if len(escolhidos) > 1 else ""
                elif vagas == 3:
                    linha["2ª Leitura"] = escolhidos[1] if len(escolhidos) > 1 else ""
                    linha["Prece"] = escolhidos[2] if len(escolhidos) > 2 else ""
                
                if num_dom == 3 and sem == 6 and h == "11h":
                    linha["1ª Leitura"] = "CRIANÇAS"
                    linha["2ª Leitura"] = "CRIANÇAS"
                    linha["Prece"] = "CRIANÇAS"

                escala.append(linha)

        df_escala = pd.DataFrame(escala)
        st.table(df_escala)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_escala.to_excel(writer, index=False, sheet_name='Escala')
        st.download_button("📥 Baixar Escala Final", output.getvalue(), f"escala_{mes}.xlsx")
