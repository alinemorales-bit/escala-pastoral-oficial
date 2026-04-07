import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import io
import random

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

    if st.button("🚀 Gerar Escala Final (Sorteio Aleatório)"):
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
            num_dom = (dia - 1) // 7 + 1
            data_formatada = dt.strftime("%d/%m")
            
            # --- REGRAS DE CELEBRAÇÃO ---
            celebracao = ""
            if sem == 0: celebracao = "Missa pelas Almas"
            elif sem == 1 and num_dom == 1: celebracao = "Missa pela Saúde (15h)"
            elif sem == 2: celebracao = "Missa Cura e Libertação"
            elif dia == 13: celebracao = "Missa Louvor N. Sra. Fátima"
            elif sem == 5: celebracao = "Missa Devocional a Maria"
            elif "16/03" in data_formatada: celebracao = "Tríduo São José"
            elif "17/03" in data_formatada: celebracao = "Tríduo São José"
            elif "18/03" in data_formatada: celebracao = "Tríduo São José"
            elif "19/03" in data_formatada: celebracao = "Solenidade São José"

            if sem == 6:
                textos = {1:"1º DOMINGO", 2:"2º DOMINGO - DIZIMISTAS", 3:"3º DOMINGO - CRIANÇAS", 4:"4º DOMINGO - FAMÍLIAS", 5:"5º DOMINGO"}
                escala.append({"Data": textos.get(num_dom, "DOMINGO"), "Dia": "", "Missa": "", "Cor": "", "Hora": "", "1ª Leitura": "", "2ª Leitura": "", "Prece": ""})

            horarios = []
            if sem == 6: horarios = ["07h30", "11h", "18h"]
            elif "15h" in celebracao: horarios = ["15h"]
            elif sem in [0, 2, 4] or "São José" in celebracao: horarios = ["19h30"]
            elif sem == 5: horarios = ["09h"]

            quem_serviu_hoje = []

            for idx, h in enumerate(horarios):
                l1, l2, pr = "-", "", ""
                vagas = 1 if sem == 2 else (2 if (sem == 1 or "São José" in celebracao) else (3 if sem == 6 else 2))
                escolhidos = []

                # --- REGRA 2º DOM 11H (Aline, Natalia, Jefferson) ---
                if num_dom == 2 and sem == 6 and h == "11h":
                    prioritarios = [p for p in ["Aline", "Natalia", "Jefferson", "Natália "] if p in contagem_participacao]
                    random.shuffle(prioritarios) # Embaralha os prioritários
                    prioritarios.sort(key=lambda n: contagem_participacao[n])
                    l1 = prioritarios[0]
                    quem_serviu_hoje.append(l1)
                    contagem_participacao[l1] += 1
                    vagas_restantes = vagas - 1
                elif num_dom == 3 and sem == 6 and h == "11h":
                    l1 = l2 = pr = "CRIANÇAS"
                    vagas_restantes = 0
                else:
                    vagas_restantes = vagas

                if vagas_restantes > 0:
                    col_alvo = localizar_coluna(df, data_formatada) or localizar_coluna(df, nomes_sem[sem])
                    if col_alvo:
                        # Filtra quem pode no horário
                        if sem == 6:
                            possiveis_df = df[df[col_alvo].str.contains(h, na=False, case=False)]
                        else:
                            possiveis_df = df[df[col_alvo].str.lower() == "sim"]
                        
                        candidatos = []
                        for _, row in possiveis_df.iterrows():
                            n_p = row[col_nome]
                            imp = str(row.get(localizar_coluna(df, "nao pode") or "", ""))
                            if n_p not in quem_serviu_hoje and str(dia) not in imp:
                                candidatos.append(n_p)
                        
                        # --- O PULO DO GATO: EMBARALHAR TUDO ---
                        random.shuffle(candidatos) # Mistura a lista toda
                        candidatos.sort(key=lambda n: contagem_participacao[n]) # Reordena por quem serviu menos
                        
                        for p in candidatos:
                            if len(escolhidos) < vagas_restantes:
                                escolhidos.append(p)
                                quem_serviu_hoje.append(p)
                                contagem_participacao[p] += 1

                # Organização das Colunas
                if l1 == "-":
                    l1 = escolhidos[0] if len(escolhidos) > 0 else "Pendente"
                    if vagas >= 2: pr = escolhidos[1] if len(escolhidos) > 1 else ""
                    if vagas == 3: 
                        l2 = escolhidos[1] if len(escolhidos) > 1 else ""
                        pr = escolhidos[2] if len(escolhidos) > 2 else ""
                elif l1 != "CRIANÇAS" and vagas == 3:
                    l2 = escolhidos[0] if len(escolhidos) > 0 else ""
                    pr = escolhidos[1] if len(escolhidos) > 1 else ""

                d_str = dt.strftime("%d/%m") if (sem != 6 or idx == 0) else ""
                s_str = nome_dia_exibicao if (sem != 6 or idx == 0) else ""
                m_str = celebracao if (sem != 6 or idx == 0) else ""

                escala.append({"Data": d_str, "Dia": s_str, "Missa": m_str, "Cor": "Verde", "Hora": h, "1ª Leitura": l1, "2ª Leitura": l2, "Prece": pr})

        st.table(pd.DataFrame(escala))
