import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import io
import random
import re
import unicodedata

st.set_page_config(page_title="Escala Pastoral Fatima", page_icon="⛪", layout="wide")

st.title("⛪ Gerador de Escala - Paróquia N. Sra. de Fátima")

# --- FUNÇÕES DE APOIO ---
def normalizar(txt):
    if pd.isna(txt): return ""
    txt = str(txt).lower().strip()
    return "".join(c for c in unicodedata.normalize('NFKD', txt) if not unicodedata.combining(c))

def buscar_coluna(df, termo):
    termo_norm = normalizar(termo)
    for col in df.columns:
        if termo_norm in normalizar(col):
            return col
    return None

# --- CONFIGURAÇÃO ---
col1, col2 = st.columns(2)
with col1:
    mes = st.selectbox("Mês:", range(1, 13), index=datetime.now().month - 1)
with col2:
    ano = st.number_input("Ano:", value=2026)

upload = st.file_uploader("📂 Arraste o arquivo CSV aqui", type="csv")

if upload:
    try:
        df = pd.read_csv(upload, sep=None, engine='python', encoding='utf-8-sig')
    except:
        upload.seek(0)
        df = pd.read_csv(upload, sep=';', encoding='latin1')

    if st.button("🚀 Gerar Escala (Nomes Limpos)"):
        escala = []
        # Identifica a coluna correta de nomes e impedimentos
        col_nome = buscar_coluna(df, "nome")
        col_impedimento = buscar_coluna(df, "nao pod")
        
        if not col_nome:
            st.error("Coluna 'Nome' não encontrada no arquivo!")
        else:
            # Pega apenas os nomes, sem sujeira de outras colunas
            todos_nomes = df[col_nome].dropna().unique()
            contagem = {str(n).strip(): 0 for n in todos_nomes}
            
            _, ultimo_dia = calendar.monthrange(ano, mes)

            for dia in range(1, ultimo_dia + 1):
                dt = datetime(ano, mes, dia)
                sem = dt.weekday()
                data_str = dt.strftime("%d/%m")
                dias_semana_norm = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]
                exibir_dia = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"][sem]
                num_dom = (dia - 1) // 7 + 1
                
                # Regras de Missas
                missa = ""
                if sem == 0: missa = "Missa pelas Almas"
                elif sem == 1 and num_dom == 1: missa = "Missa pela Saúde (15h)"
                elif sem == 2: missa = "Cura e Libertação"
                elif dia == 13: missa = "N. Sra. Fátima"
                elif sem == 5: missa = "Devocional Maria"
                elif any(d in data_str for d in ["16/03", "17/03", "18/03"]): missa = "Tríduo São José"
                elif "19/03" in data_str: missa = "Solenidade São José"

                if sem == 6:
                    tit = {1:"1º DOMINGO", 2:"2º DOMINGO", 3:"3º DOMINGO", 4:"4º DOMINGO", 5:"5º DOMINGO"}
                    escala.append({"Data": tit.get(num_dom, "DOMINGO"), "Dia": "", "Missa": "", "Hora": "", "1ª Leitura": "", "2ª Leitura": "", "Prece": ""})

                horarios = ["07h30", "11h", "18h"] if sem == 6 else (["15h"] if "15h" in missa else (["19h30"] if (missa or sem in [0,2,4]) else []))
                
                for idx_h, h in enumerate(horarios):
                    vagas = 3 if sem == 6 else 2
                    if "cura" in missa.lower(): vagas = 1
                    
                    # Aline/Natalia/Jefferson (2º Dom 11h)
                    l1_fixo = None
                    if num_dom == 2 and sem == 6 and h == "11h":
                        prios = [p for p in ["Aline", "Natalia", "Jefferson", "Natália "] if p in contagem]
                        random.shuffle(prios)
                        prios.sort(key=lambda x: contagem[x])
                        l1_fixo = prios[0]

                    col_alvo = buscar_coluna(df, data_str) or buscar_coluna(df, dias_semana_norm[sem])
                    candidatos = []
                    
                    if col_alvo:
                        for _, row in df.iterrows():
                            val_celula = str(row[col_alvo]).lower()
                            # Só entra se a pessoa marcou "Sim" ou o horário específico
                            if "sim" in val_celula or h in val_celula:
                                nome_limpo = str(row[col_nome]).strip()
                                imp = str(row.get(col_impedimento, "")).lower()
                                
                                # Verifica se não há bloqueio para este dia
                                if not re.search(rf"\b0?{dia}\b", imp):
                                    candidatos.append(nome_limpo)

                    random.shuffle(candidatos)
                    candidatos.sort(key=lambda x: contagem[x])

                    escolhidos = []
                    if l1_fixo: 
                        escolhidos.append(l1_fixo)
                        if l1_fixo in candidatos: candidatos.remove(l1_fixo)
                    
                    for c in candidatos:
                        if len(escolhidos) < vagas: escolhidos.append(c)

                    for e in escolhidos: contagem[e] += 1

                    linha = {
                        "Data": data_str if (sem != 6 or idx_h == 0) else "",
                        "Dia": exibir_dia if (sem != 6 or idx_h == 0) else "",
                        "Missa": missa if (sem != 6 or idx_h == 0) else "",
                        "Hora": h,
                        "1ª Leitura": escolhidos[0] if len(escolhidos) > 0 else "Pendente",
                        "2ª Leitura": "", "Prece": ""
                    }
                    if vagas == 2: linha["Prece"] = escolhidos[1] if len(escolhidos) > 1 else ""
                    elif vagas == 3:
                        linha["2ª Leitura"] = escolhidos[1] if len(escolhidos) > 1 else ""
                        linha["Prece"] = escolhidos[2] if len(escolhidos) > 2 else ""
                    
                    if num_dom == 3 and sem == 6 and h == "11h":
                        linha["1ª Leitura"] = linha["2ª Leitura"] = linha["Prece"] = "CRIANÇAS"

                    escala.append(linha)

            df_final = pd.DataFrame(escala)
            st.table(df_final)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False)
            st.download_button("📥 Baixar Escala", output.getvalue(), "escala_liturgia.xlsx")
