import base64
import urllib.parse

def b64_encode(input_text: str) -> str:
    """Codifica uma string para Base64."""
    try:
        return base64.b64encode(input_text.encode('utf-8')).decode('utf-8')
    except Exception as e:
        return f"Erro ao codificar: {e}"

def b64_decode(input_text: str) -> str:
    """Decodifica uma string de Base64."""
    try:
        return base64.b64decode(input_text.encode('utf-8')).decode('utf-8')
    except Exception as e:
        return f"Erro ao decodificar: {e}"

def url_encode(input_text: str) -> str:
    """Codifica uma string para o formato URL."""
    try:
        return urllib.parse.quote(input_text)
    except Exception as e:
        return f"Erro ao codificar: {e}"

def url_decode(input_text: str) -> str:
    """Decodifica uma string do formato URL."""
    try:
        return urllib.parse.unquote(input_text)
    except Exception as e:
        return f"Erro ao decodificar: {e}"
