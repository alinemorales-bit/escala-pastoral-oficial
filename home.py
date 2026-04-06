import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import io

st.set_page_config(page_title="Escala Pastoral Fatima", page_icon="⛪", layout="wide")

st.title("⛪ Gerador de Escala - Paróquia N. Sra. de Fátima")

col1, col2 = st.columns(2)
with col1:
    mes = st.selectbox("Selecione o Mês:", range(1, 13), index=datetime.now().month - 1)
with col2:
    ano = st.number_input("Ano:", value=2026)

upload = st.file_uploader("📂 Arraste o CSV aqui", type="csv")

if upload:
    df = pd.read_csv(upload)
    df.columns = df.columns.str.strip() 

    if st.button("🚀 Gerar Escala Final"):
        escala = []
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        
        def achar_coluna(termo):
            for col in df.columns:
                if termo.lower() in col.lower():
                    return col
            return None

        for dia in range(1, dias_no_mes + 1):
            data_atual = datetime(ano, mes, dia)
            dia_semana = data_atual.weekday()
            nomes_dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
            nome_dia_puro = nomes_dias[dia_semana]
            num_dom = (dia - 1) // 7 + 1
            
            celebracao = ""
            if dia_semana == 0: celebracao = "Missa pelas Almas"
            elif dia_semana == 1 and num_dom == 1: celebracao = "Missa pela Saúde (15h)"
            elif dia_semana == 2: celebracao = "Missa Cura e Libertação"
            elif dia == 13: celebracao = "Missa em Louvor a N. Sra. de Fátima"
            elif dia_semana == 5: celebracao = "Missa Devocional a Maria"
            
            if dia_semana == 6:
                textos_dom = {1: "1º DOMINGO", 2: "2º DOMINGO - DIZIMISTAS", 3: "3º DOMINGO - CRIANÇAS", 4: "4º DOMINGO - FAMÍLIAS", 5: "5º DOMINGO"}
                escala.append({"Data": textos_dom.get(num_dom, "DOMINGO"), "Dia": "", "Missa": "", "Hora": "", "1ª Leitura": "", "2ª Leitura": "", "Prece": "", "Cor": ""})

            horarios = []
            if dia_semana == 6: horarios = ["07h30", "11h", "18h"]
            elif "15h" in celebracao: horarios = ["15h"]
            elif dia_semana in [0, 2, 4]: horarios = ["19h30"]
            elif dia_semana == 5: horarios = ["09h"]

            for h in horarios:
                l1, l2, pr = "-", "-", "-"
                vagas = 3 if dia_semana == 6 else (2 if h in ["19h30", "09h"] else 1)
                escolhidos = []
                
                # 1. Prioridade do 2º Domingo (Aline, Natália e Jefferson)
                if num_dom == 2 and dia_semana == 6 and h == "11h":
                    escolhidos = ["Aline", "Natália", "Jefferson"]
                
                # 2. Regra das Crianças
                elif num_dom == 3 and dia_semana == 6 and h == "11h":
                    l1 = l2 = pr = "CRIANÇAS"
                
                # 3. Busca Geral baseada no seu CSV
                else:
                    col_real = achar_coluna(nome_dia_puro)
                    if col_real:
                        # Se for Domingo, procura o horário (ex: "11h")
                        # Se for semana, procura quem respondeu "Sim"
                        if dia_semana == 6:
                            possiveis = df[df[col_real].astype(str).str.contains(h, na=False)]
                        else:
                            possiveis = df[df[col_real].astype(str).str.lower() == "sim"]
                        
                        for _, row in possiveis.iterrows():
                            impedimentos = str(row.get('Quaisdias não pode servir', ''))
                            if len(escolhidos) < vagas and row['Nome'] not in escolhidos and str(dia) not in impedimentos:
                                escolhidos.append(row['Nome'])

                # Preenchimento
                if l1 == "-":
                    if vagas == 1: l1 = escolhidos[0] if escolhidos else "Pendente"
                    elif vagas == 2:
                        l1 = escolhidos[0] if len(escolhidos) > 0 else "Pendente"
                        pr = escolhidos[1] if len(escolhidos) > 1 else "Pendente"
                    else:
                        l1 = escolhidos[0] if len(escolhidos) > 0 else "Pendente"
                        l2 = escolhidos[1] if len(escolhidos) > 1 else "Pendente"
                        pr = escolhidos[2] if len(escolhidos) > 2 else "Pendente"

                escala.append({"Data": data_atual.strftime("%d/%m"), "Dia": nome_dia_puro, "Missa": celebracao, "Hora": h, "1ª Leitura": l1, "2ª Leitura": l2, "Prece": pr, "Cor": "Verde"})

        df_final = pd.DataFrame(escala)
        st.table(df_final)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Escala')
            workbook = writer.book
            worksheet = writer.sheets['Escala']
            worksheet.data_validation('H2:H200', {'validate': 'list', 'source': ['Verde', 'Roxo', 'Branco', 'Vermelho', 'Rosa']})
            
        st.download_button("📥 Baixar Escala para Excel", buffer.getvalue(), f"escala_{mes}_{ano}.xlsx")
