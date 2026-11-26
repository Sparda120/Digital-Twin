"""Script mínimo para recolher dados de um switch ExtremeXOS via JSON-RPC."""

from __future__ import annotations

import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv


def run_exos_cli(host: str, port: int, user: str, password: str, cmd: str) -> dict:
    """Envia um comando CLI ao switch EXOS via POST /jsonrpc e devolve o JSON."""
    url = f"http://{host}:{port}/jsonrpc"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "cli",
        "params": [cmd],
    }
    resp = requests.post(url, auth=(user, password), json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    """Lê credenciais do .env, executa o comando no EXOS e imprime o JSON."""
    parser = argparse.ArgumentParser(description="Recolhe dados de um switch EXOS via JSON-RPC.")
    parser.add_argument(
        "--cmd",
        default="show ports no-refresh",
        help="Comando CLI EXOS a executar (padrão: 'show ports no-refresh')",
    )
    args = parser.parse_args()

    load_dotenv()
    host = os.getenv("EXOS_HOST", "192.168.122.210")
    port = int(os.getenv("EXOS_PORT", "80"))
    user = os.getenv("EXOS_USER", "admin")
    password = os.getenv("EXOS_PASSWORD", "")

    try:
        data = run_exos_cli(host, port, user, password, args.cmd)
    except requests.RequestException as exc:
        print(f"Erro ao contactar o switch EXOS ({host}:{port}): {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
