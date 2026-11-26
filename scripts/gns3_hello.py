"""Script mínimo para testar a ligação à API REST v2 do GNS3."""

from __future__ import annotations

import os

import requests
from dotenv import load_dotenv


def main() -> None:
    """Lê o URL do GNS3 a partir do .env e lista a versão e os projetos existentes."""
    load_dotenv()
    base_url = os.getenv("GNS3_BASE_URL", "http://localhost:3080/v2").rstrip("/")

    # 1. Confirmar que o servidor GNS3 responde
    version_resp = requests.get(f"{base_url}/version", timeout=5)
    version_resp.raise_for_status()
    version_data = version_resp.json()
    print(f"GNS3 ligado com sucesso! Versão: {version_data.get('version')}")

    # 2. Listar projetos existentes no GNS3
    projects_resp = requests.get(f"{base_url}/projects", timeout=5)
    projects_resp.raise_for_status()
    projects = projects_resp.json()

    print(f"\nProjetos encontrados ({len(projects)}):")
    for proj in projects:
        print(f" - {proj['name']} | id={proj['project_id']} | estado={proj['status']}")


if __name__ == "__main__":
    main()
