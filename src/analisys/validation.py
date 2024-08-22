import pandas as pd
from pandas import DataFrame, Series
from typing import Dict, Any, Tuple, Optional, Union



# ----------------------------------------------------------------------------------
# Checagem de Nulos e vazios em um campo
# ----------------------------------------------------------------------------------

def check_null_empty(df_data: DataFrame, df_fields: DataFrame, row: Series) -> Tuple[str, str, Optional[str]]:
    """
    Realiza uma checagem de valores nulos (NaN) e vazios (strings com espaços ou vazias)
    estritamente no campo especificado por row['field'].

    Args:
        df_data: O DataFrame Pandas contendo os dados.
        df_fields: (Não utilizado nesta rotina, mas mantido na assinatura).
        row: A Series (linha de metadados) que contém o nome do campo a ser checado via row['field'].

    Returns:
        Uma tupla contendo: (evidence_msg, status, details)
    """
    
    # 1. Extrair e Sanitizar o Nome do Campo
    #    Sanitiza-se o nome esperado (row['field']) para comparação
    field_name_raw = row['field']
    field_name_sanitized = field_name_raw.strip().lower()
    
    # Sanitiza-se os nomes das colunas do DF de dados para busca
    colunas_df_data_sanitized = [col.strip().lower() for col in df_data.columns]
    
    # 2. Verificar se o campo existe no DataFrame de dados
    if field_name_sanitized not in colunas_df_data_sanitized:
         return "Campo não encontrado para checagem.", "FAIL", f"A coluna '{field_name_raw}' (sanitizada para '{field_name_sanitized}') não existe no DataFrame de dados."

    # 3. Encontrar o nome real da coluna no df_data para acesso
    try:
        idx = colunas_df_data_sanitized.index(field_name_sanitized)
        nome_coluna_real = df_data.columns[idx]
    except ValueError:
        # Caso o nome sanitizado não seja encontrado (Controle de segurança)
        return "Erro interno de busca do campo.", "FAIL", f"Não foi possível localizar '{field_name_raw}' no DataFrame."

    # 4. Contagem de Nulos (NaN e None)
    null_count = df_data[nome_coluna_real].isnull().sum()
    empty_count = 0
    
    # 5. Contagem de Vazios (Strings Vazias/Whitespace) - Apenas para tipos string/object
    if df_data[nome_coluna_real].dtype in ['object', 'string']:
        # Verifica se o valor é string vazia ou contém apenas espaços (após conversão para str)
        empty_count = df_data[nome_coluna_real].astype(str).str.strip().eq('').sum()

    # 6. Cálculo de Estatísticas Focadas
    total_missing = null_count + empty_count
    total_rows = len(df_data)
    
    # 7. Determinar Status e Gerar Mensagens
    
    if total_missing == 0:
        status = "PASS"
        details = "Nenhum valor nulo ou vazio detectado neste campo."
        evidence_msg = "0 ausências."
    else:
        status = "FAIL"
        
        # Detalhes e Evidência
        pct_missing = (total_missing / total_rows) * 100
        
        # Detalhes: Informação focada no campo
        details = (
            f"Total de {total_missing} ausente(s) ({pct_missing:.2f}%) "
            f"[Nulos: {null_count}, Vazios/Whitespace: {empty_count}]"
        )
        
        # Evidência: Mensagem curta para o relatório
        evidence_msg = f"{total_missing} ausências ({pct_missing:.2f}%)"
    
    return evidence_msg, status, details

# ----------------------------------------------------------------------------------
# Retorna as caracteristicas do campo para determinação das analises
# ----------------------------------------------------------------------------------

def field_apply_list(df_data: DataFrame, df_fields: DataFrame, row: Series) -> Tuple[str, str, Optional[str]]:
    
    apply_list = []

    row = row.astype('string')

    # Tipo
    apply_list.append(row["type"]) 

    # Subtipo 
    if len(str(row["subtype"]))  > 0: 
        apply_list.append(row["subtype"])      

    # Nulos
    if row["null"] == "no": 
        apply_list.append("nulo") 

    # pk
    if row["pk"] == "yes": 
        apply_list.append("pk") 

    # fk
    if row["fk"] == "yes": 
        apply_list.append("fk") 

    if row["zero"] == "no": 
        apply_list.append("zero") 

    if row["negative"] == "no": 
        apply_list.append("negative") 

    # format
    campo_vazio = pd.isna(row['format']) or (isinstance(row['format'], str) and not row['format'].strip())
    if not campo_vazio: 
        apply_list.append("format")   

    # range
    campo_vazio = pd.isna(row['range']) or (isinstance(row['range'], str) and not row['range'].strip())
    if not campo_vazio: 
        apply_list.append("range")   

    # values
    campo_vazio = pd.isna(row['values']) or (isinstance(row['values'], str) and not row['values'].strip())
    if not campo_vazio: 
        apply_list.append("values")  

    return apply_list

def check_zero_negative(df_data: DataFrame, df_fields: DataFrame, row: Series) -> Tuple[str, str, Optional[str]]:
    pass 

def check_values_list(df_data: DataFrame, df_fields: DataFrame, row: Series) -> Tuple[str, str, Optional[str]]:
    pass 