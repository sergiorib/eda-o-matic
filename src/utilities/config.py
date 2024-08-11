# ============================================================
#  File:        config.py
#  Author:      Sergio Ribeiro
#  Description: General configurations
# ============================================================
from pathlib import Path
import json

# Define o diretório raiz do projeto (o diretório acima de 'src')
MAIN_PATH = Path(__file__).resolve().parent.parent.parent

# Caminho para o arquivo JSON de configuração (estático)
CONFIG_JSON_FILE = MAIN_PATH / "config" / "config.json"

# Carrega os dados do arquivo JSON
def _load_config_json():
    try:
        with open(CONFIG_JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"O arquivo de configuração não foi encontrado em: {CONFIG_JSON_FILE}")
        
# Carrega a configuração uma única vez ao iniciar o módulo
_DADOS_CONFIG = _load_config_json()

# -----------------------------------------------------------------
# Cria variaveis pra compartilhar os parametros no projeto todo
# -----------------------------------------------------------------

# Parâmetros lidos do JSON
DATA_PATH = _DADOS_CONFIG.get("data_path")
EDA_CONFIG_PATH = _DADOS_CONFIG.get("eda_config_path")
FILE_FORMAT = _DADOS_CONFIG.get("file_format")
SEPARATOR = _DADOS_CONFIG.get("separator")
DECIMAL_SEPARATOR = _DADOS_CONFIG.get("decimal_separator")
DATE_FORMAT = _DADOS_CONFIG.get("date_format")
LOG_PATH = _DADOS_CONFIG.get("log_path")
# Outros parametros
MAIN_PATH = Path.cwd().parent.parent.parent

# Lista de caminhos e parâmetros disponíveis para importação em outros módulos
__all__ = [
# Parâmetros lidos do JSON
DATA_PATH, 
EDA_CONFIG_PATH, 
FILE_FORMAT, 
SEPARATOR,
DECIMAL_SEPARATOR, 
DATE_FORMAT, 
LOG_PATH,
MAIN_PATH
]