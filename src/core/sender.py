import concurrent.futures
import requests
import os
from urllib.parse import urlencode, parse_qs
from .logger_config import log
import re

def _substitute_value(source: str, param_name: str, new_value: str) -> str:
    """Helper to substitute a value in a query string or form-urlencoded body."""
    # Pattern to find the parameter and its value
    pattern = re.compile(f"([?&]|^)({re.escape(param_name)}=)([^&]*)")

    if pattern.search(source):
        # Substitute the value if the parameter is found
        return pattern.sub(f"\\1\\2{new_value}", source)
    else:
        # Append the parameter if it's not found
        if '?' not in source:
            return f"{source}?{param_name}={new_value}"
        else:
            return f"{source}&{param_name}={new_value}"

def send_from_raw(raw_request: str, param_name: str = None, new_value: str = None, proxy_port: int = 9507):
    """
    Parses a raw HTTP request, optionally substitutes a parameter,
    and resends it, returning the response object.
    """
    full_url = ""
    try:
        # Separate the request into head and body
        head, body = raw_request.strip().split('\n\n', 1) if '\n\n' in raw_request else (raw_request.strip(), "")
        request_lines = head.split('\n')

        # 1. Parse the first line
        method, path, _ = request_lines[0].split(' ')

        # 2. Parse Headers
        headers = {}
        for line in request_lines[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()

        # 3. Build URL
        host = headers.get("Host")
        if not host:
            raise ValueError("Header 'Host' não encontrado.")
        # Use HTTP for local hosts, HTTPS for others
        if host.startswith(('127.0.0.1', 'localhost', '192.168.', '10.', '172.')):
            scheme = "http"
        else:
            scheme = "https"
        base_url = f"{scheme}://{host}"

        # 4. Substitute parameter
        if param_name and new_value is not None:
            new_value = str(new_value).strip()
            # Try in URL path/query
            if param_name in path:
                path = _substitute_value(path, param_name, new_value)
            # Try in urlencoded body
            elif body and "application/x-www-form-urlencoded" in headers.get("Content-Type", ""):
                 body = _substitute_value(body, param_name, new_value)
            # Otherwise, add to URL
            else:
                path = _substitute_value(path, param_name, new_value)

        full_url = f"{base_url}{path}"

        # 5. Prepare for resending
        headers_to_send = {k: v for k, v in headers.items() if k.lower() not in ['host', 'content-length']}

        proxies = {"http": f"http://127.0.0.1:{proxy_port}", "https": f"http://127.0.0.1:{proxy_port}"}

        log.info(f"Resending request: {method} {full_url}")

        response = requests.request(
            method=method,
            url=full_url,
            headers=headers_to_send,
            data=body.encode('utf-8') if body else None,
            proxies=proxies,
            verify=False
        )

        log.info(f"Response received: {response.status_code}")
        return response

    except Exception as e:
        log.error(f"Error resending request: {e}", exc_info=True)
        return None

def run_sender_from_file(raw_request: str, file_path: str, param_name: str, num_threads: int, queue=None, proxy_port: int = 9507):
    """
    Reads a file and resends the base request for each value in the file, in parallel.
    """
    if not os.path.exists(file_path):
        log.error(f"Sender: File '{file_path}' not found.")
        if queue:
            queue.put({'type': 'error', 'data': f"File '{file_path}' not found."})
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        values = f.readlines()

    total_requests = len(values)
    log.info(f"Sender: Starting bulk send of {total_requests} requests.")
    if queue:
        queue.put({'type': 'progress_start', 'total': total_requests})

    completed_requests = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(send_from_raw, raw_request, param_name, value, proxy_port) for value in values]

        for future in concurrent.futures.as_completed(futures):
            response = future.result()
            completed_requests += 1
            if queue:
                progress = (completed_requests / total_requests) * 100
                queue.put({'type': 'progress_update', 'value': progress})

                if response:
                    success = 200 <= response.status_code < 300
                    result_data = {'url': response.request.url, 'status': response.status_code, 'success': success, 'response': response}
                else:
                    result_data = {'url': 'N/A', 'status': 'Error', 'success': False, 'response': None}

                queue.put({'type': 'result', 'data': result_data})

    log.info("Sender: Bulk send completed.")
    if queue:
        queue.put({'type': 'progress_done'})

def run_sender(url: str, file_path: str, param_name: str, num_threads: int):
    """
    Simplified function for CLI usage - sends GET requests with values from a file.
    """
    if not os.path.exists(file_path):
        log.error(f"Sender: File '{file_path}' not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        values = [line.strip() for line in f.readlines()]

    total_requests = len(values)
    log.info(f"Sender: Starting bulk send of {total_requests} requests to {url}")

    completed_requests = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for value in values:
            # Build the URL with the parameter
            if '?' in url:
                full_url = f"{url}&{param_name}={value}"
            else:
                full_url = f"{url}?{param_name}={value}"
            
            futures.append(executor.submit(_send_get_request, full_url))

        for future in concurrent.futures.as_completed(futures):
            response = future.result()
            completed_requests += 1
            if response:
                log.info(f"[{completed_requests}/{total_requests}] {response.request.url} -> {response.status_code}")
            else:
                log.error(f"[{completed_requests}/{total_requests}] Failed")

    log.info("Sender: Bulk send completed.")

def _send_get_request(url: str):
    """Helper function to send a GET request without proxy."""
    try:
        response = requests.get(url, verify=False, timeout=10)
        return response
    except Exception as e:
        log.error(f"Error sending request to {url}: {e}")
        return None

