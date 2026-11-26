"""Script mínimo para criar um switch EXOS no GNS3 via API REST v2."""

from __future__ import annotations

import argparse
import os
import sys

import requests
from dotenv import load_dotenv


def find_project_id(base_url: str, project_name: str) -> str:
    """Procura o ID de um projeto no GNS3 pelo nome (sem distinguir maiúsculas)."""
    resp = requests.get(f"{base_url}/projects", timeout=5)
    resp.raise_for_status()
    projects = resp.json()

    for proj in projects:
        if proj["name"].lower() == project_name.lower():
            return proj["project_id"]

    print("Projetos disponíveis no teu GNS3:")
    for proj in projects:
        print(f" - {proj['name']} (estado={proj['status']})")
    raise ValueError(f"\nProjeto '{project_name}' não encontrado no GNS3.")


def find_template(base_url: str, query: str) -> dict:
    """Procura um template no GNS3 cujo nome contenha `query` (sem distinguir maiúsculas)."""
    resp = requests.get(f"{base_url}/templates", timeout=5)
    resp.raise_for_status()
    templates = resp.json()

    matches = [t for t in templates if query.lower() in t["name"].lower()]
    if len(matches) == 1:
        return matches[0]

    print("Templates disponíveis no teu GNS3:")
    for t in templates:
        print(f" - {t['name']} (id={t['template_id']}, tipo={t.get('template_type')})")

    if not matches:
        raise ValueError(f"\nNenhum template encontrado com '{query}'.")
    raise ValueError(
        f"\nVários templates correspondem a '{query}'. Sê mais específico com --template."
    )


def create_node_from_template(
    base_url: str, project_id: str, template_id: str, node_name: str
) -> dict:
    """Cria um nó num projeto GNS3 a partir de um template existente."""
    payload = {"x": 0, "y": 0, "name": node_name}
    resp = requests.post(
        f"{base_url}/projects/{project_id}/templates/{template_id}",
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    """Ponto de entrada: localiza projeto/template e cria o switch no GNS3."""
    parser = argparse.ArgumentParser(description="Cria um switch no GNS3 a partir de um template.")
    parser.add_argument("--project", default="trial", help="Nome do projeto GNS3 (padrão: trial)")
    parser.add_argument("--template", default="EXOS", help="Texto para encontrar o template")
    parser.add_argument("--name", default="EXOS-Twin-1", help="Nome do novo switch no GNS3")
    args = parser.parse_args()

    load_dotenv()
    base_url = os.getenv("GNS3_BASE_URL", "http://localhost:3080/v2").rstrip("/")

    try:
        project_id = find_project_id(base_url, args.project)
        template = find_template(base_url, args.template)
        node = create_node_from_template(base_url, project_id, template["template_id"], args.name)
    except (requests.RequestException, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Switch criado com sucesso no projeto '{args.project}'!")
    print(f" - Nome: {node['name']}")
    print(f" - Template usado: {template['name']}")
    print(f" - node_id: {node['node_id']}")


if __name__ == "__main__":
    main()
