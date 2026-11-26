"""Sincronização da topologia normalizada do Digital Twin com a API REST v2 do GNS3."""

from __future__ import annotations

import requests
from pydantic import BaseModel, Field

from src.models import Link, Topology


class SyncReport(BaseModel):
    """Resumo das alterações aplicadas no projeto GNS3."""

    created_nodes: list[str] = Field(default_factory=list)
    created_links: list[str] = Field(default_factory=list)
    deleted_links: list[str] = Field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """Indica se foi feita alguma alteração no GNS3."""
        return bool(self.created_nodes or self.created_links or self.deleted_links)


class Gns3Client:
    """Cliente HTTP simples para a API REST v2 do GNS3."""

    def __init__(self, base_url: str = "http://localhost:3080/v2") -> None:
        self.base_url = base_url.rstrip("/")

    def find_project_id(self, project_name: str) -> str:
        resp = requests.get(f"{self.base_url}/projects", timeout=5)
        resp.raise_for_status()
        for proj in resp.json():
            if proj["name"].lower() == project_name.lower():
                return proj["project_id"]
        raise ValueError(f"Projeto '{project_name}' não encontrado no GNS3.")

    def find_template_id(self, query: str) -> str:
        resp = requests.get(f"{self.base_url}/templates", timeout=5)
        resp.raise_for_status()
        matches = [t for t in resp.json() if query.lower() in t["name"].lower()]
        if len(matches) == 1:
            return matches[0]["template_id"]
        if not matches:
            raise ValueError(f"Nenhum template encontrado com '{query}'.")
        raise ValueError(f"Vários templates correspondem a '{query}'. Sê mais específico.")

    def list_nodes(self, project_id: str) -> list[dict]:
        resp = requests.get(f"{self.base_url}/projects/{project_id}/nodes", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def create_node(self, project_id: str, template_id: str, name: str, x: int, y: int) -> dict:
        resp = requests.post(
            f"{self.base_url}/projects/{project_id}/templates/{template_id}",
            json={"x": x, "y": y, "name": name},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def list_links(self, project_id: str) -> list[dict]:
        resp = requests.get(f"{self.base_url}/projects/{project_id}/links", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def create_link(self, project_id: str, endpoints: list[dict]) -> dict:
        resp = requests.post(
            f"{self.base_url}/projects/{project_id}/links",
            json={"nodes": endpoints},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def delete_link(self, project_id: str, link_id: str) -> None:
        resp = requests.delete(
            f"{self.base_url}/projects/{project_id}/links/{link_id}",
            timeout=10,
        )
        resp.raise_for_status()


def _resolve_gns3_port(node: dict, iface_name: str) -> tuple[int, int]:
    """Mapeia um nome de interface (ex: '1') para (adapter_number, port_number) no GNS3."""
    ports = node.get("ports", [])
    for port in ports:
        if port.get("name") == iface_name or port.get("short_name") == iface_name:
            return int(port["adapter_number"]), int(port["port_number"])

    if iface_name.isdigit():
        idx = int(iface_name)
        if 0 <= idx < len(ports):
            return int(ports[idx]["adapter_number"]), int(ports[idx]["port_number"])

    raise ValueError(f"Interface '{iface_name}' não encontrada no nó GNS3 '{node['name']}'.")


def _gns3_link_key(gns3_link: dict) -> frozenset[tuple[str, int, int]]:
    """Chave única bidirecional para um link retornado pela API do GNS3."""
    return frozenset(
        (n["node_id"], int(n["adapter_number"]), int(n["port_number"]))
        for n in gns3_link.get("nodes", [])
    )


def _desired_link_key(
    link: Link, nodes_by_name: dict[str, dict]
) -> tuple[frozenset[tuple[str, int, int]], list[dict]]:
    """Converte um Link do Digital Twin para chave GNS3 + payload de endpoints."""
    node_a = nodes_by_name[link.source_device]
    node_b = nodes_by_name[link.target_device]
    ad_a, pt_a = _resolve_gns3_port(node_a, link.source_interface)
    ad_b, pt_b = _resolve_gns3_port(node_b, link.target_interface)

    key = frozenset([(node_a["node_id"], ad_a, pt_a), (node_b["node_id"], ad_b, pt_b)])
    endpoints = [
        {"node_id": node_a["node_id"], "adapter_number": ad_a, "port_number": pt_a},
        {"node_id": node_b["node_id"], "adapter_number": ad_b, "port_number": pt_b},
    ]
    return key, endpoints


def sync_topology_to_gns3(
    client: Gns3Client,
    project_name: str,
    template_query: str,
    topology: Topology,
) -> SyncReport:
    """Garante que os nós e links de `topology` estão espelhados no projeto GNS3."""
    project_id = client.find_project_id(project_name)
    template_id = client.find_template_id(template_query)

    existing_nodes = client.list_nodes(project_id)
    nodes_by_name = {n["name"]: n for n in existing_nodes}

    # Inclui nós descobertos apenas como vizinhos LLDP para que os cabos possam ligar
    required_names = {d.name for d in topology.devices}
    for link in topology.links:
        required_names.add(link.source_device)
        required_names.add(link.target_device)

    report = SyncReport()
    for name in sorted(required_names):
        if name not in nodes_by_name:
            x_pos = len(nodes_by_name) * 220 - 200
            new_node = client.create_node(project_id, template_id, name=name, x=x_pos, y=0)
            nodes_by_name[name] = new_node
            report.created_nodes.append(name)

    existing_links = client.list_links(project_id)
    existing_by_key = {_gns3_link_key(lnk): lnk for lnk in existing_links}

    desired_by_key: dict[frozenset[tuple[str, int, int]], tuple[Link, list[dict]]] = {}
    for link in topology.links:
        key, endpoints = _desired_link_key(link, nodes_by_name)
        desired_by_key[key] = (link, endpoints)

    # Criar links novos
    for key, (link, endpoints) in desired_by_key.items():
        if key not in existing_by_key:
            client.create_link(project_id, endpoints)
            report.created_links.append(
                f"{link.source_device}:{link.source_interface} "
                f"<-> {link.target_device}:{link.target_interface}"
            )

    # Remover links que já não existem na rede real
    for key, gns3_link in existing_by_key.items():
        if key not in desired_by_key:
            client.delete_link(project_id, gns3_link["link_id"])
            report.deleted_links.append(gns3_link["link_id"])

    return report
