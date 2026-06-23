import os

# Configura chaves fictícias no ambiente antes da coleta e importação de módulos do projeto
os.environ["GEMINI_API_KEY"] = "mock_key_for_testing"
os.environ["LOG_LEVEL"] = "INFO"
os.environ["ANKI_CONNECT_URL"] = "http://localhost:8765"
