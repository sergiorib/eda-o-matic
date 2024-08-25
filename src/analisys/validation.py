import pandas as pd
from pandas import DataFrame, Series
from typing import Dict, Any, Tuple, Optional, Union
import traceback
import sys 
import re

# Rotinas auxiliares

def field_apply_list(df_data: DataFrame, df_fields: DataFrame, row: Series) -> Tuple[str, str, Optional[str]]:
    # ----------------------------------------------------------------------------------
    # Retorna as caracteristicas do campo para determinação das analises
    # ----------------------------------------------------------------------------------   
    apply_list = []

    row = row.astype('string')

    # Tipo
    apply_list.append(row["type"]) 

    # Subtipo 
    if len(str(row["subtype"]))  > 0 and str(row["subtype"])  != "undefined": 
        apply_list.append(row["subtype"])      

    # Nulos
    if row["null"] == "no": 
        apply_list.append("no-null") 

    # pk
    if row["pk"] == "yes": 
        apply_list.append("pk") 

    # fk
    if row["fk"] == "yes": 
        apply_list.append("fk") 

    if row["zero"] == "no": 
        apply_list.append("no-zero") 

    if row["negative"] == "no": 
        apply_list.append("no-negative") 

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

# Rotinas de validação

def check_null_empty(df_data: DataFrame, df_fields: DataFrame, row: Series) -> Tuple[str, str, Optional[str]]:
    """
    # ----------------------------------------------------------------------------------
    #  Checagem de Nulos e vazios em um campo
    # ----------------------------------------------------------------------------------

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
        status = "pass"
        details = "Nenhum valor nulo ou vazio detectado neste campo."
        evidence_msg = "0 ausências."
    else:
        status = "fail"
        
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

def check_regex_format(df_data: DataFrame, df_fields: DataFrame, row: Series) -> Tuple[str, str, Optional[str]]:
    """
    Aplica uma expressão regular (REGEX) a um campo específico do DataFrame de dados,
    retornando o percentual de compatibilidade e o detalhe do primeiro erro.

    Args:
        df_data: DataFrame com os dados a serem analisados.
        df_fields: DataFrame de campos (mantido na assinatura, mas não utilizado).
        row: Registro de testes com 'format' (REGEX) e 'field' (nome do campo).

    Returns:
        Uma tupla contendo: (evidence_msg, status, details)
    """
    
    # 1. Extrair e Sanitizar os Parâmetros
    field_name = str(row["field"]).strip()
    regex_pattern = str(row["format_regex"]).strip()
    
    # Adicionar âncoras de início e fim (^) e ($) ao regex se não existirem
    # Isso garante que a regex corresponda à STRING INTEIRA, não apenas a uma substring.
    if not regex_pattern.startswith('^'):
        regex_pattern = '^' + regex_pattern
    if not regex_pattern.endswith('$'):
        regex_pattern = regex_pattern + '$'
       
    # 3. Aplicação do Regex e Contagem
    
    # Converte para string (necessário para .str.match) e lida com nulos
    series_alvo = df_data[field_name].astype(str)
    
    # Aplica o regex. Retorna True para correspondência e False para não correspondência.
    # O ~ inverte a máscara para encontrar os que NÃO CORRESPONDEM (os erros)
    mascara_erro = ~series_alvo.str.match(regex_pattern, na=False)
    
    # Remove os nulos (que viraram 'nan') da contagem de erros, se necessário.
    # Se você quer incluir 'nan' como erro, remova esta linha:
    # máscara_erro = mascara_erro & series_alvo.str.lower().ne('nan')
    
    total_linhas = len(df_data)
    erros_encontrados = mascara_erro.sum()
    
    # 4. Cálculo de Métricas
    compatibilidade_percentual = ((total_linhas - erros_encontrados) / total_linhas) * 100
    
    # 5. Geração de Retorno
    
    # Variável de Mensagem de Evidência
    evidence_msg = f"Compatibilidade: {compatibilidade_percentual:.2f}%"
    
    if compatibilidade_percentual == 100.00:
        # 5a. Sucesso
        status = "pass"
        details = "" # Vazio se não houverem erros
    else:
        # 5b. Falha: Encontrar o Primeiro Erro
        status = "fail"
        
        # Encontra o índice (número da linha) da primeira ocorrência True (erro)
        # O idxmax() retorna o índice da primeira ocorrência do valor máximo (True=1, False=0)
        primeiro_erro_indice = mascara_erro.idxmax()
        primeiro_erro_valor = df_data.loc[primeiro_erro_indice, field_name]        
        primeiro_erro_indice += 2 # compensa erro na atribuição do indice. 
        # Obtém o valor real que causou o erro
 
        
        # Geração de Detalhes
        details = (
            f"Exemplo de erro: '{primeiro_erro_valor}' "
            f"(linha {primeiro_erro_indice})"
        )
        
    return evidence_msg, status, details

def check_zero_values(df_data: DataFrame, df_fields: DataFrame, row: Series) -> Tuple[str, str, Optional[str]]:

    try: 
        # 1. Extrair e Sanitizar os Parâmetros
        field_name = str(row["field"]).strip()

        # separar valores numericos e não numericos da coluna 
        coluna_numerica = pd.to_numeric(
        df_data[field_name].astype(str).str.replace(',', '.', regex=False), errors='coerce')  # padroniza virgula para separador decimal
        # Cria a Máscara Booleana de Ruído:
        # True onde o valor NÃO É NaN (foi convertido com sucesso)
        mascara_numerico = coluna_numerica.notna()
        # 3. Cria a Série de Valores que Podem Ser Convertidos (Os Limpos)
        # Usa o isna() no DataFrame original onde a máscara é True
        df_valores_numericos = df_data.loc[mascara_numerico, field_name]
        df_valores_numericos = pd.to_numeric(df_valores_numericos, errors='raise')

        #pd.to_numeric(df_valores_numericos, errors='coerce')
        # 4. Cria a Série de Valores de Ruído (Os Não Convertíveis)
        #    Usa o inverso da máscara (~mascara_numerico)
        df_valores_nao_numericos = df_data.loc[~mascara_numerico, field_name]   
        print("-------- Debug ----------")
        print(df_data.size) 
        print(df_valores_numericos.size) 
        print(df_valores_nao_numericos.size)         
        print("-------- Debug ----------")

        print("-------- Debug df_valores_numericos----------")
        print(field_name) 
        print(df_valores_numericos.dtype) 
        print("-------- Debug ----------")
        # 3. Aplicação da Máscara (Valores Iguais a Zero)
        series_alvo = df_valores_numericos
        print("-------- Debug series_alvo ----------")
        print(series_alvo.dtype) 
        print("-------- Debug ----------")        
        if series_alvo.dtype in ['object', 'string']:
            print("-------- FODEU ! ----------") 
            evidence_msg = "Não foi possivel validar"
            status = "error"
            details = f"ERRO: Coluna '{field_name}' é do tipo {series_alvo.dtype}. Não é ideal para checagem de zero numérico."
            return evidence_msg, status, details  # Retorno 2 (Em caso de tipo de dado inadequado)

        # 4. Cálculo de Métricas
        mascara_negativos = (series_alvo == 0)
        total_linhas = len(df_valores_numericos)
        negativos_encontrados = mascara_negativos.sum()
        percentual_negativos = (negativos_encontrados / total_linhas) * 100 if total_linhas > 0 else 0.00

        # 5. Geração de Retorno Padrão
        evidence_msg = f"Zerados: {percentual_negativos:.2f}%"
   
        if percentual_negativos == 0.00:
            status = "pass"
            details = "" # Retorno 3 (Sucesso)
        else:
            # 6. Falha: Encontrar o Primeiro Erro
            status = "fail"
            # Buscando o índice do erro (Pode ser o ponto de falha mais comum)
            primeiro_negativo_indice = mascara_negativos.idxmax()
            primeiro_negativo_valor =  df_valores_numericos.loc[primeiro_negativo_indice]
            primeiro_negativo_indice += 2 # Corrige o numero do indice

            details = (
                f"Linha com exemplo de erro: ({primeiro_negativo_indice}): "
                f"Valor encontrado: {primeiro_negativo_valor}"
            )

        # Retorno 5 (Garante o retorno normal)

        return evidence_msg, status, details   
        
    except Exception as e:
      
        evidence_msg = "Erro ao chamar a rotina de analise."
        # 7. TRATAMENTO FINAL: Captura QUALQUER exceção não prevista e GARANTE o retorno de 3 valores.
        details = f"FALHA INESPERADA na rotina check_zero_values: {type(e).__name__}: {str(e)}"
        
        # Retorno FINAL, Crítico e Garantido (Retorno 6)
        return evidence_msg, "error", details

def check_negative_values(df_data: DataFrame, df_fields: DataFrame, row: Series) -> Tuple[str, str, Optional[str]]:

    try: 
        # 1. Extrair e Sanitizar os Parâmetros
        field_name = str(row["field"]).strip()
        # separar valores numericos e não numericos da coluna 
        coluna_numerica = pd.to_numeric(
        df_data[field_name].astype(str).str.replace(',', '.', regex=False), errors='coerce')  # padroniza virgula para separador decimal
        # Cria a Máscara Booleana de Ruído:
        # True onde o valor NÃO É NaN (foi convertido com sucesso)
        mascara_numerico = coluna_numerica.notna()
        # 3. Cria a Série de Valores que Podem Ser Convertidos (Os Limpos)
        # Usa o isna() no DataFrame original onde a máscara é True
        df_valores_numericos = df_data.loc[mascara_numerico, field_name]
        df_valores_numericos = pd.to_numeric(df_valores_numericos, errors='raise')       
        # 4. Cria a Série de Valores de Ruído (Os Não Convertíveis)
        #    Usa o inverso da máscara (~mascara_numerico)
        df_valores_nao_numericos = df_data.loc[~mascara_numerico, field_name]  

        # 3. Aplicação da Máscara (Valores Iguais a Zero)
        series_alvo = df_valores_numericos
        
        if series_alvo.dtype in ['object', 'string']:
            evidence_msg = "Não foi possivel validar"
            status = "error"
            details = f"ERRO: Coluna '{field_name}' é do tipo {series_alvo.dtype}. Não é ideal para checagem de valores negativos."
            return evidence_msg, status, details  # Retorno 2 (Em caso de tipo de dado inadequado)

        # 4. Cálculo de Métricas
        mascara_negativos = (series_alvo < 0)
        total_linhas = len(df_valores_numericos)
        negativos_encontrados = mascara_negativos.sum()
        percentual_negativos = (negativos_encontrados / total_linhas) * 100 if total_linhas > 0 else 0.00

        # 5. Geração de Retorno Padrão
        evidence_msg = f"Negativos: {percentual_negativos:.2f}%"
   
        if percentual_negativos == 0.00:
            status = "pass"
            details = "" # Retorno 3 (Sucesso)
        else:
            # 6. Falha: Encontrar o Primeiro Erro
            status = "fail"
            # Buscando o índice do erro (Pode ser o ponto de falha mais comum)
            primeiro_negativo_indice = mascara_negativos.idxmax()
            primeiro_negativo_valor = df_valores_numericos.loc[primeiro_negativo_indice]
            primeiro_negativo_indice += 2 # Corrige o numero do indice

            details = (
                f"Linha com exemplo de erro: ({primeiro_negativo_indice}): "
                f"Valor encontrado: {primeiro_negativo_valor}"
            )

        # Retorno 5 (Garante o retorno normal)

        return evidence_msg, status, details   
        
    except Exception as e:
        evidence_msg = "Erro na rotina de analise."
        # 7. TRATAMENTO FINAL: Captura QUALQUER exceção não prevista e GARANTE o retorno de 3 valores.
        details = f"FALHA INESPERADA na rotina check_negative_values: {type(e).__name__}: {str(e)}"
        
        # Retorno FINAL, Crítico e Garantido (Retorno 6)
        return evidence_msg, "error", details
 
def check_valid_range(df_data: DataFrame, df_fields: DataFrame, row: Series) -> Tuple[str, str, Optional[str]]:

    try: 

        # 1. Extrair e Sanitizar os Parâmetros
        field_name = str(row["field"]).strip()
        field_range = str(row["range"]).strip()
    

        # separar valores numericos e não numericos da coluna 
        coluna_numerica = pd.to_numeric(
        df_data[field_name].astype(str).str.replace(',', '.', regex=False), errors='coerce')  # padroniza virgula para separador decimal
        # Cria a Máscara Booleana de Ruído:
        # True onde o valor NÃO É NaN (foi convertido com sucesso)
        mascara_numerico = coluna_numerica.notna()

        # 3. Cria a Série de Valores que Podem Ser Convertidos (Os Limpos)
        # Usa o isna() no DataFrame original onde a máscara é True
        df_valores_numericos = df_data.loc[mascara_numerico, field_name]
        df_valores_numericos = pd.to_numeric(df_valores_numericos, errors='raise')       
        # 4. Cria a Série de Valores de Ruído (Os Não Convertíveis)
        #    Usa o inverso da máscara (~mascara_numerico)
        df_valores_nao_numericos = df_data.loc[~mascara_numerico, field_name]   




        # Valida o formato do range 
        # Formato esperado para o range "de x a y", onde x e y são qualquer numero
        regex_formato = r"^de\s*([\d\.,]+)\s*a\s*([\d\.,]+)$"

        if not re.fullmatch(regex_formato, field_range):
            evidence_msg = "Não foi possivel validar"
            details = f"ERRO: O campo '{field_name}' está com erro no formato range. deve ser 'de x a y', onde x w y são numeros."
            status = "Error"
            return evidence_msg, status, details
        
        # Extrai os ranges 
        field_range_inicio = None 
        field_range_fim = None

        regex_intervalo = r"^de\s*([\d\.,]+)\s*a\s*([\d\.,]+)$"
        match = re.fullmatch(regex_intervalo, field_range, re.IGNORECASE)

        if match:
            num1_str = match.group(1)
            num2_str = match.group(2)
    
            try:
                field_range_inicio = float(num1_str.replace('.', '').replace(',', '.'))
                field_range_fim = float(num2_str.replace('.', '').replace(',', '.'))
            except ValueError:
                evidence_msg = "Não foi possivel validar"
                details = f"ERRO: Não foi possivel extrair os ranges informados no campo '{field_name}'"
                status = "Error"
                return evidence_msg, status, details

        # 3. Aplicação da Máscara (Valores Iguais a Zero)
        series_alvo = df_valores_numericos
        
        if series_alvo.dtype in ['object', 'string']:
            evidence_msg = "Não foi possivel validar"
            status = "fail"
            details = f"ERRO: Coluna '{field_name}' é do tipo {series_alvo.dtype}. Não é ideal para checagem de valores negativos."
            return evidence_msg, status, details  # Retorno 2 (Em caso de tipo de dado inadequado)

        # 4. Cálculo de Métricas
        mascara_range = (series_alvo >= field_range_inicio) & (series_alvo <= field_range_fim)
        total_linhas = len(df_valores_numericos)
        ranges_invalidos_encontrados = mascara_range.sum()
        percentual_ranges_invalidos = (ranges_invalidos_encontrados / total_linhas) * 100 if total_linhas > 0 else 0.00

        # 5. Geração de Retorno Padrão
        evidence_msg = f"fora do range: {percentual_ranges_invalidos:.2f}%"
   
        if percentual_ranges_invalidos == 0.00:
            status = "pass"
            details = "" # Retorno 3 (Sucesso)
        else:
            # 6. Falha: Encontrar o Primeiro Erro
            status = "fail"
            # Buscando o índice do erro (Pode ser o ponto de falha mais comum)
            primeiro_range_invalido_indice = mascara_range.idxmax()
            primeiro_range_negativo_valor = df_valores_numericos.loc[primeiro_range_invalido_indice]
            primeiro_range_invalido_indice += 2 # Corrige o numero do indice

            details = (
                f"Linha com exemplo de erro: ({primeiro_range_invalido_indice}): "
                f"Valor encontrado: {primeiro_range_negativo_valor}"
            )

        # Retorno 5 (Garante o retorno normal)

        return evidence_msg, status, details   
        
    except Exception as e:

        exc_type, exc_obj, exc_tb = sys.exc_info()

        evidence_msg = "Erro de execução da rotina de analise"
        # 7. TRATAMENTO FINAL: Captura QUALQUER exceção não prevista e GARANTE o retorno de 3 valores.
        details = f"FALHA INESPERADA na rotina check_negative_values: {type(e).__name__}: {str(e)}" "("+ str(exc_tb.tb_lineno) + ")"
        
        # Retorno FINAL, Crítico e Garantido (Retorno 6)
        return evidence_msg, "error", details

def check_values_list(df_data: DataFrame, df_fields: DataFrame, row: Series) -> Tuple[str, str, Optional[str]]:
    pass 