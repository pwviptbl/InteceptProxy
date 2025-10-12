import concurrent.futures
import requests
import os
from .logger_config import log

import re

def send_single_request(url, param_name, value, queue=None):
    """
    Envia uma única requisição HTTP, substituindo o valor do parâmetro
    e opcionalmente reportando o resultado para uma fila.
    """
    full_url = ""
    try:
        payload = value.strip()
        pattern = re.compile(f"({param_name}=)([^&]*)")

        if pattern.search(url):
            full_url = pattern.sub(f"\\g<1>{payload}", url)
        else:
            separator = '&' if '?' in url else '?'
            full_url = f"{url}{separator}{param_name}={payload}"

        proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
        response = requests.get(full_url, proxies=proxies, verify=False)

        success = response.status_code in [200, 201, 204]
        if success:
            log.info(f"Sender: Requisição para '{full_url}' enviada com sucesso (Status: {response.status_code}).")
        else:
            log.warning(f"Sender: Requisição para '{full_url}' retornou status: {response.status_code}.")

        if queue:
            result = {'url': full_url, 'status': response.status_code, 'success': success}
            queue.put({'type': 'result', 'data': result})
        return success

    except requests.RequestException as e:
        log.error(f"Sender: Erro ao enviar requisição para '{full_url}': {e}")
        if queue:
            result = {'url': full_url, 'status': 'Erro', 'success': False}
            queue.put({'type': 'result', 'data': result})
        return False

def run_sender(url, file_path, param_name, num_threads, queue=None):
    """
    Lê um arquivo, envia requisições em paralelo e reporta o progresso.
    """
    if not os.path.exists(file_path):
        log.error(f"Sender: O arquivo '{file_path}' não foi encontrado.")
        if queue:
            queue.put({'type': 'error', 'data': f"Arquivo '{file_path}' não encontrado."})
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        values = f.readlines()

    total_requests = len(values)
    log.info(f"Sender: Iniciando envio de {total_requests} requisições...")
    if queue:
        queue.put({'type': 'progress_start', 'total': total_requests})

    completed_requests = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(send_single_request, url, param_name, value, queue) for value in values]

        for future in concurrent.futures.as_completed(futures):
            completed_requests += 1
            if queue:
                progress = (completed_requests / total_requests) * 100
                queue.put({'type': 'progress_update', 'value': progress})

    log.info(f"Sender: Envio concluído.")
    if queue:
        queue.put({'type': 'progress_done'})


def send_request_no_params(url, queue=None):
    """
    Envia uma única requisição sem modificar parâmetros e reporta o resultado.
    """
    full_url = ""
    try:
        full_url = url.strip()
        proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
        response = requests.get(full_url, proxies=proxies, verify=False)

        success = response.status_code in [200, 201, 204]
        if success:
            log.info(f"Sender: Requisição para '{full_url}' enviada com sucesso (Status: {response.status_code}).")
        else:
            log.warning(f"Sender: Requisição para '{full_url}' retornou status: {response.status_code}.")

        if queue:
            result = {'url': full_url, 'status': response.status_code, 'success': success}
            queue.put({'type': 'result', 'data': result})
        return success

    except requests.RequestException as e:
        log.error(f"Sender: Erro ao enviar requisição para '{full_url}': {e}")
        if queue:
            result = {'url': full_url, 'status': 'Erro', 'success': False}
            queue.put({'type': 'result', 'data': result})
        return False
