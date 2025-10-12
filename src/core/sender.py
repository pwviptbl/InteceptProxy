import concurrent.futures
import requests
import os
from .logger_config import log

def send_single_request(url, param_name, value):
    """Envia uma única requisição HTTP através do proxy."""
    try:
        # Garante que o valor não tenha quebras de linha
        payload = value.strip()

        # Monta a URL com o parâmetro
        full_url = f"{url}?{param_name}={payload}"

        proxies = {
            "http": "http://127.0.0.1:8080",
            "https": "http://127.0.0.1:8080",
        }

        response = requests.get(
            full_url,
            proxies=proxies,
            verify=False  # Necessário por estarmos passando pelo mitmproxy
        )

        if response.status_code in [200, 201, 204]:
            log.info(f"Sender: Requisição para '{full_url}' enviada com sucesso (Status: {response.status_code}).")
            return True
        else:
            log.warning(f"Sender: Requisição para '{full_url}' retornou status inesperado: {response.status_code}.")
            return False

    except requests.RequestException as e:
        log.error(f"Sender: Erro ao enviar requisição para '{full_url}': {e}")
        return False

def run_sender(url, file_path, param_name, num_threads):
    """
    Lê um arquivo e envia requisições em paralelo.
    """
    if not os.path.exists(file_path):
        log.error(f"Sender: O arquivo '{file_path}' não foi encontrado.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        values = f.readlines()

    total_requests = len(values)
    log.info(f"Sender: Iniciando envio de {total_requests} requisições usando {num_threads} threads...")

    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Cria uma future para cada requisição
        future_to_value = {executor.submit(send_single_request, url, param_name, value): value for value in values}

        for future in concurrent.futures.as_completed(future_to_value):
            if future.result():
                success_count += 1

    log.info(f"Sender: Envio concluído. {success_count}/{total_requests} requisições enviadas com sucesso.")
