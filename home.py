import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import io

st.set_page_config(page_title="Escala Pastoral Fatima", page_icon="⛪", layout="wide")

st.title("⛪ Gerador de Escala - Paróquia N. Sra. de Fátima")
st.info("🎨 Consulte a cor litúrgica aqui: [Liturgia Diária - Paulus](https://www.paulus.com.br/portal/liturgia-diaria/)")

# --- PAINEL DE CONTROLE ---
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
        
        for dia in range(1, dias_no_mes + 1):
            data_atual = datetime(ano, mes, dia)
            dia_semana = data_atual.weekday()
            nome_dia = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"][dia_semana]
            num_dom = (dia - 1) // 7 + 1
            
            missa_nome = ""
            if dia_semana == 0: missa_nome = "(Missa pelas Almas)"
            elif dia_semana == 1 and num_dom == 1: missa_nome = "15h - (Missa pela Saúde)"
            elif dia_semana == 2: missa_nome = "(Missa Clamando por Cura e Libertação)"
            elif dia == 13: missa_nome = "(Missa em Louvor a N. Sra. de Fátima)"
            elif dia_semana == 5: missa_nome = "(Missa Devocional a Maria)"
            
            if dia_semana == 6:
                textos_dom = {1: "1º DOMINGO", 2: "2º DOMINGO - DIZIMISTAS", 3: "3º DOMINGO - CRIANÇAS", 4: "4º DOMINGO - FAMÍLIAS", 5: "5º DOMINGO"}
                escala.append({"Data": textos_dom.get(num_dom, "DOMINGO"), "Dia": "", "Hora": "", "1ª Leitura": "", "2ª Leitura": "", "Prece": "", "Cor": ""})

            horarios = []
            if dia_semana == 6: horarios = ["07h30", "11h", "18h"]
            elif "15h" in missa_nome: horarios = ["15h"]
            elif dia_semana in [0, 2, 4]: horarios = ["19h30"]
            elif dia_semana == 5: horarios = ["09h"]

            for h in horarios:
                l1, l2, pr = "-", "-", "-"
                vagas = 3 if dia_semana == 6 else (2 if h in ["19h30", "09h"] else 1)
                
                escolhidos = []
                # Lógica simplificada de busca para evitar erros de colunas
                col_busca = 'Domingo' if dia_semana == 6 else (df.columns[1] if len(df.columns) > 1 else df.columns[0])
                
                if col_busca in df.columns:
                    possiveis = df[df[col_busca].astype(str).str.contains(h, na=False)]
                    for _, row in possiveis.iterrows():
                        if len(escolhidos) < vagas and row['Nome'] not in escolhidos:
                            escolhidos.append(row['Nome'])
                
                if vagas == 1: l1 = escolhidos[0] if escolhidos else "Pendente"
                elif vagas == 2:
                    l1 = escolhidos[0] if len(escolhidos) > 0 else "Pendente"
                    pr = escolhidos[1] if len(escolhidos) > 1 else "Pendente"
                else:
                    l1 = escolhidos[0] if len(escolhidos) > 0 else "Pendente"
                    l2 = escolhidos[1] if len(escolhidos) > 1 else "Pendente"
                    pr = escolhidos[2] if len(escolhidos) > 2 else "Pendente"

                escala.append({"Data": data_atual.strftime("%d/%m"), "Dia": f"{nome_dia} {missa_nome}", "Hora": h, "1ª Leitura": l1, "2ª Leitura": l2, "Prece": pr, "Cor": "Verde"})

        df_final = pd.DataFrame(escala)
        st.table(df_final)

        # --- CRIAÇÃO DO EXCEL COM LISTA SUSPENSA ---
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Escala')
            workbook  = writer.book
            worksheet = writer.sheets['Escala']
            
            # Define as opções da lista suspensa
            opcoes_cores = ['Verde', 'Roxo', 'Branco', 'Vermelho', 'Rosa']
            
            # Aplica a validação de dados na coluna G (Cor), da linha 2 até a 100
            worksheet.data_validation('G2:G100', {
                'validate': 'list',
                'source': opcoes_cores,
                'input_title': 'Escolha a cor:',
                'input_message': 'Selecione a cor litúrgica do dia'
            })
            
        st.download_button(
            label="📥 Baixar Escala para Excel",
            data=buffer.getvalue(),
            file_name=f"escala_pastoral_{mes}_{ano}.xlsx",
            mime="application/vnd.ms-excel"
        )
