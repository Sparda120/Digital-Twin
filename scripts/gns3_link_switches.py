"""Script mínimo para criar 2 switches no GNS3 e ligá-los por um cabo (link)."""

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
    for proj in resp.json():
        if proj["name"].lower() == project_name.lower():
            return proj["project_id"]
    raise ValueError(f"Projeto '{project_name}' não encontrado no GNS3.")


def find_template(base_url: str, query: str) -> dict:
    """Procura um template no GNS3 cujo nome contenha `query` (sem distinguir maiúsculas)."""
    resp = requests.get(f"{base_url}/templates", timeout=5)
    resp.raise_for_status()
    matches = [t for t in resp.json() if query.lower() in t["name"].lower()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValueError(f"Nenhum template encontrado com '{query}'.")
    raise ValueError(f"Vários templates correspondem a '{query}'. Sê mais específico.")


def create_node(
    base_url: str, project_id: str, template_id: str, name: str, x: int, y: int
) -> dict:
    """Cria um nó no projeto GNS3 na posição (x, y) indicada."""
    payload = {"x": x, "y": y, "name": name}
    resp = requests.post(
        f"{base_url}/projects/{project_id}/templates/{template_id}",
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def create_link(
    base_url: str, project_id: str, node_a: dict, node_b: dict, port_index: int = 0
) -> dict:
    """Liga dois nós no GNS3 usando a porta `port_index` de cada um."""
    port_a = node_a["ports"][port_index]
    port_b = node_b["ports"][port_index]

    payload = {
        "nodes": [
            {
                "node_id": node_a["node_id"],
                "adapter_number": port_a["adapter_number"],
                "port_number": port_a["port_number"],
            },
            {
                "node_id": node_b["node_id"],
                "adapter_number": port_b["adapter_number"],
                "port_number": port_b["port_number"],
            },
        ]
    }
    resp = requests.post(f"{base_url}/projects/{project_id}/links", json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    """Cria 2 switches no GNS3 (lado a lado) e estabelece um link entre eles."""
    parser = argparse.ArgumentParser(description="Cria 2 switches no GNS3 e liga-os por cabo.")
    parser.add_argument("--project", default="trial1", help="Nome do projeto GNS3")
    parser.add_argument("--template", default="EXOS", help="Texto para encontrar o template")
    parser.add_argument("--port-index", type=int, default=0, help="Índice da porta a ligar (0..N)")
    args = parser.parse_args()

    load_dotenv()
    base_url = os.getenv("GNS3_BASE_URL", "http://localhost:3080/v2").rstrip("/")

    try:
        project_id = find_project_id(base_url, args.project)
        template = find_template(base_url, args.template)

        node_a = create_node(base_url, project_id, template["template_id"], "EXOS-A", x=-150, y=0)
        node_b = create_node(base_url, project_id, template["template_id"], "EXOS-B", x=150, y=0)
        link = create_link(base_url, project_id, node_a, node_b, port_index=args.port_index)
    except (requests.RequestException, ValueError, IndexError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)

    p_a = node_a["ports"][args.port_index]
    p_b = node_b["ports"][args.port_index]
    print(f"Switches criados e ligados no projeto '{args.project}'!")
    print(f" - {node_a['name']} ({p_a['name']}) <---> {node_b['name']} ({p_b['name']})")
    print(f" - link_id: {link['link_id']}")


if __name__ == "__main__":
    main()
