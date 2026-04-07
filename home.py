import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import io
import random
import re

st.set_page_config(page_title="Escala Pastoral Fatima", page_icon="⛪", layout="wide")

st.title("⛪ Gerador de Escala - Paróquia N. Sra. de Fátima")

col1, col2 = st.columns(2)
with col1:
    mes = st.selectbox("Mês:", range(1, 13), index=datetime.now().month - 1)
with col2:
    ano = st.number_input("Ano:", value=2026)

upload = st.file_uploader("📂 Arraste o CSV aqui", type="csv")

if upload:
    try:
        df = pd.read_csv(upload, sep=None, engine='python', encoding='utf-8-sig')
    except:
        upload.seek(0)
        df = pd.read_csv(upload, sep=';', encoding='latin1')

    def localizar_coluna(data_f, termo):
        for col in data_f.columns:
            if termo.lower() in col.lower(): return col
        return None

    df.columns = df.columns.str.strip().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8').str.lower()
    df = df.map(lambda x: str(x).strip() if pd.notnull(x) else x)

    if st.button("🚀 Gerar Escala Corrigida"):
        escala = []
        col_nome = localizar_coluna(df, "nome")
        nomes_unicos = list(df[col_nome].unique())
        contagem_participacao = {nome: 0 for nome in nomes_unicos}
        
        dias_no_mes = calendar.monthrange(ano, mes)[1]

        for dia in range(1, dias_no_mes + 1):
            dt = datetime(ano, mes, dia)
            sem = dt.weekday()
            nomes_sem = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]
            nome_dia_exibicao = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"][sem]
            data_formatada = dt.strftime("%d/%m")
            num_dom = (dia - 1) // 7 + 1
            
            # Identificação da Missa
            celebracao = ""
            if sem == 0: celebracao = "Missa pelas Almas"
            elif sem == 1 and num_dom == 1: celebracao = "Missa pela Saúde (15h)"
            elif sem == 2: celebracao = "Missa Cura e Libertação"
            elif dia == 13: celebracao = "Missa Louvor N. Sra. Fátima"
            elif sem == 5: celebracao = "Missa Devocional a Maria"
            elif "16/03" in data_formatada or "17/03" in data_formatada or "18/03" in data_formatada: celebracao = "Tríduo São José"
            elif "19/03" in data_formatada: celebracao = "Solenidade São José"

            if sem == 6:
                textos = {1:"1º DOMINGO", 2:"2º DOMINGO - DIZIMISTAS", 3:"3º DOMINGO - CRIANÇAS", 4:"4º DOMINGO - FAMÍLIAS", 5:"5º DOMINGO"}
                escala.append({"Data": textos.get(num_dom, "DOMINGO"), "Dia": "", "Missa": "", "Cor": "", "Hora": "", "1ª Leitura": "", "2ª Leitura": "", "Prece": ""})

            # Define Horários
            horarios = ["07h30", "11h", "18h"] if sem == 6 else (["15h"] if "15h" in celebracao else (["19h30"] if (sem in [0, 2, 4] or "São José" in celebracao) else (["09h"] if sem == 5 else [])))

            for idx_h, h in enumerate(horarios):
                # Define número de leitores
                vagas = 3 if sem == 6 else (1 if sem == 2 else 2)
                
                # Regra 2º Dom 11h
                l1_obrigatorio = None
                if num_dom == 2 and sem == 6 and h == "11h":
                    prios = [p for p in ["Aline", "Natalia", "Jefferson", "Natália "] if p in contagem_participacao]
                    random.shuffle(prios)
                    prios.sort(key=lambda n: contagem_participacao[n])
                    l1_obrigatorio = prios[0]

                # Busca candidatos disponíveis
                col_alvo = localizar_coluna(df, data_formatada) or localizar_coluna(df, nomes_sem[sem])
                disponiveis = []
                if col_alvo:
                    mask = df[col_alvo].str.contains(h, na=False, case=False) if sem == 6 else df[col_alvo].str.lower() == "sim"
                    for _, row in df[mask].iterrows():
                        nome = row[col_nome]
                        imp = str(row.get(localizar_coluna(df, "nao pode") or "", "")).lower()
                        if not re.search(rf"\b0?{dia}\b", imp):
                            disponiveis.append(nome)

                random.shuffle(disponiveis)
                disponiveis.sort(key=lambda n: contagem_participacao[n])

                # Preenchimento das vagas
                escolhidos = []
                if l1_obrigatorio:
                    escolhidos.append(l1_obrigatorio)
                    if l1_obrigatorio in disponiveis: disponiveis.remove(l1_obrigatorio)

                for p in disponiveis:
                    if len(escolhidos) < vagas:
                        escolhidos.append(p)

                # Montagem da linha
                linha = {
                    "Data": dt.strftime("%d/%m") if (sem != 6 or idx_h == 0) else "",
                    "Dia": nome_dia_exibicao if (sem != 6 or idx_h == 0) else "",
                    "Missa": celebracao if (sem != 6 or idx_h == 0) else "",
                    "Cor": "Verde", "Hora": h,
                    "1ª Leitura": escolhidos[0] if len(escolhidos) > 0 else "Pendente",
                    "2ª Leitura": "", "Prece": ""
                }

                if vagas == 2:
                    linha["Prece"] = escolhidos[1] if len(escolhidos) > 1 else ""
                elif vagas == 3:
                    linha["2ª Leitura"] = escolhidos[1] if len(escolhidos) > 1 else ""
                    linha["Prece"] = escolhidos[2] if len(escolhidos) > 2 else ""

                # Atualiza contagem global
                for e in escolhidos:
                    contagem_participacao[e] += 1
                
                escala.append(linha)

        st.table(pd.DataFrame(escala))
