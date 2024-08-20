# ============================================================
#  File:        Utilities.py
#  Author:      Sergio Ribeiro
#  Description: Various tools
# ============================================================
import json
import os
from pathlib import Path
from src.utilities import logger
import pandas as pd
from charset_normalizer import from_path 
from typing import Union

# Carrega as configurações gerais 
def load_config(df_config: pd.DataFrame):
    
    config_path = Path(__file__).resolve().parents[2] / "config" / "config.json"

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Atualiza (in place)
    for key, value in config.items():
        df_config[key] = value

    return None

# Reinicia o log pra pegar a path das configurações gerais
def init_log(log_path: str):
    if len(log_path) > 0:
        logger.set_log_path(log_path)
        logger.log_event("load_config", "CONFIG_LOADED", f"Log path set to {log_path}", "info")
    else:
        logger.log_event("load_config", "CONFIG_MISSING", "LOG_PATH not found in config.json", "fail")
    return None

# Leitura dos parametros de validações
def load_validations(df_validations: pd.DataFrame, excel_path: str):
    # Verifica se o arquivo existe
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Arquivo Excel não encontrado: {excel_path}")

    # Lê o Excel e verifica se a aba existe
     # Lê o conteúdo da aba 'validations'
    df_temp = pd.read_excel(excel_path, sheet_name="validations")

    # Limpa o dataframe original e substitui os dados
    df_validations.drop(df_validations.index, inplace=True)
    for col in df_temp.columns:
        df_validations[col] = df_temp[col]

    return df_validations

def load_fields(df_fields: pd.DataFrame, excel_path: str):
    # Verifica se o arquivo existe
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Arquivo Excel não encontrado: {excel_path}")

    # Lê o Excel e verifica se a aba existe
     # Lê o conteúdo da aba 'validations'
    df_temp = pd.read_excel(excel_path, sheet_name="fields")

    # Limpa o dataframe original e substitui os dados
    df_fields.drop(df_fields.index, inplace=True)
    for col in df_temp.columns:
        df_fields[col] = df_temp[col]

    return df_fields


def load_data(df_data: pd.DataFrame, file_path: str, separator: str, encode: str):

    try:
        try:
            if len(encode) == 0: 
                detectado = from_path(str(file_path)).best() 
                encoding_detectado = detectado.encoding 
            else: 
                encoding_detectado = encode
        except Exception:
            encoding_detectado = 'utf-8' 

        df_temp = pd.read_csv(
            file_path,
            encoding=encoding_detectado,
            sep=separator,
            engine='python' 
        )
    except Exception as e:
        raise ValueError(f"Falha no carregamento do arquivo !")
    
    df_data = df_temp

    

    '''
    # Limpa o dataframe original e substitui os dados
    df_data.drop(df_data.index, inplace=True)
    for col in df_temp.columns:
        df_data[col] = df_temp[col]
    '''

    return df_data


def format_file_size(file_size_bytes: Union[int, float]) -> str:
    """
    Converte um tamanho de arquivo em bytes para uma string legível 
    em KB, MB, GB, etc., com duas casas decimais.

    Args:
        file_size_bytes: O tamanho do arquivo em bytes (int ou float).

    Returns:
        Uma string formatada (Ex: "858.00 KB", "75.34 MB").
    """
    
    # 1. Caso base: Zero bytes
    if file_size_bytes == 0:
        return "0.00 B"

    # 2. Constantes e Unidades (base 1024)
    TAMANHO_BASE = 1024
    UNIDADES = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    
    # 3. Determinar a unidade correta
    i = 0
    tamanho = float(file_size_bytes)
    
    # Itera enquanto o tamanho for maior ou igual a 1024
    # e enquanto houver unidades para avançar
    while (tamanho >= TAMANHO_BASE) and (i < len(UNIDADES) - 1):
        tamanho /= TAMANHO_BASE # Divide por 1024 para mudar a unidade
        i += 1
        
    # 4. Formatação do resultado (limitado a duas casas decimais)
    # Usa f-string com o formato ":.2f" para o float e adiciona a unidade
    return f"{tamanho:.2f} {UNIDADES[i]}"

