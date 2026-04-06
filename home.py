import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import io

st.set_page_config(page_title="Escala Pastoral Fatima", page_icon="⛪", layout="wide")

st.title("⛪ Gerador de Escala - Paróquia N. Sra. de Fátima")

# --- PAINEL DE CONTROLE ---
st.info("🎨 Consulte a cor litúrgica aqui: [Liturgia Diária - Paulus](https://www.paulus.com.br/portal/liturgia-diaria/)")

col1, col2, col3 = st.columns(3)
with col1:
    mes = st.selectbox("Mês:", range(1, 13), index=datetime.now().month - 1)
with col2:
    ano = st.number_input("Ano:", value=2026)
with col3:
    cor_mes = st.selectbox("Cor Litúrgica Predominante:", ["Verde", "Roxo", "Branco", "Vermelho", "Rosa"])

upload = st.file_uploader("📂 Arraste o CSV das respostas aqui", type="csv")

if upload:
    df = pd.read_csv(upload)
    df.columns = df.columns.str.strip()

    if st.button("🚀 Gerar Escala Oficial"):
        escala = []
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        
        for dia in range(1, dias_no_mes + 1):
            data_atual = datetime(ano, mes, dia)
            dia_semana = data_atual.weekday()
            nome_dia = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"][dia_semana]
            num_dom = (dia - 1) // 7 + 1
            
            # --- TÍTULOS E CELEBRAÇÕES FIXAS ---
            missa_nome = ""
            if dia_semana == 0: missa_nome = "(Missa pelas Almas)"
            elif dia_semana == 1 and num_dom == 1: missa_nome = "15h - (Missa pela Saúde)"
            elif dia_semana == 2: missa_nome = "(Missa Clamando por Cura e Libertação)"
            elif dia == 13: missa_nome = "(Missa em Louvor a N. Sra. de Fátima)"
            elif dia_semana == 5: missa_nome = "(Missa Devocional a Maria)"
            
            # --- LINHA DE DESTAQUE DO DOMINGO ---
            if dia_semana == 6:
                textos_dom = {
                    1: "1º DOMINGO",
                    2: "2º DOMINGO - REZEMOS PELOS DIZIMISTAS",
                    3: "3º DOMINGO - REZEMOS PELAS CRIANÇAS",
                    4: "4º DOMINGO - REZEMOS PELAS FAMÍLIAS",
                    5: "5º DOMINGO"
                }
                escala.append({"Data": textos_dom.get(num_dom, "DOMINGO"), "Dia": "", "Hora": "", "1ª Leitura": "", "2ª Leitura": "", "Preces": "", "Cor": ""})

            # --- DEFINIÇÃO DE HORÁRIOS ---
            horarios = []
            if dia_semana == 6: horarios = ["07h30", "11h", "18h"]
            elif "15h" in missa_nome: horarios = ["15h"]
            elif dia_semana in [0, 2, 4]: horarios = ["19h30"]
            elif dia_semana == 5: horarios = ["09h"]

            for h in horarios:
                l1, l2, pr = "-", "-", "-"
                vagas = 3 if dia_semana == 6 else (2 if h in ["19h30", "09h"] else 1)
                
                # Regras Especiais de preenchimento
                if num_dom == 3 and dia_semana == 6 and h == "11h":
                    l1 = l2 = pr = "CRIANÇAS"
                elif num_dom == 4 and dia_semana == 6 and (h == "07h30" or h == "18h"):
                    l1 = l2 = "PASTORAL FAMILIAR"
                    # Busca prece no formulário
                    if 'Domingo' in df.columns:
                        poss = df[df['Domingo'].astype(str).str.contains(h, na=False)]
                        if not poss.empty: pr = poss.iloc[0]['Nome']
                else:
                    # Busca Geral
                    col_busca = 'Domingo' if dia_semana == 6 else 'Semana' # Ajuste conforme seu CSV
                    if col_busca not in df.columns: col_busca = df.columns[1] # Pega a segunda coluna se não achar
                    
                    escolhidos = []
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

                escala.append({
                    "Data": data_atual.strftime("%d/%m"),
                    "Dia": f"{nome_dia} {missa_nome}",
                    "Hora": h,
                    "1ª Leitura": l1,
                    "2ª Leitura": l2,
                    "Preces": pr,
                    "Cor": cor_mes
                })

        df_final = pd.DataFrame(escala)
        st.table(df_final)

        # Download Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False)
        st.download_button("📥 Baixar Escala (Excel)", buffer.getvalue(), "escala_fatima.xlsx")
