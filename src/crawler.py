"""Descoberta automática de topologia (BFS Crawler) a partir de um switch semente."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable

import requests

from src.exos_normalizer import (
    extract_lldp_neighbor_ips,
    normalize_exos_device,
    normalize_exos_lldp,
)
from src.models import Device, Link, Topology

# Tipo da função que executa um comando CLI num switch (permite injetar mocks em testes)
CliFetcher = Callable[[str, str], dict]


def make_jsonrpc_fetcher(port: int, user: str, password: str) -> CliFetcher:
    """Cria um fetcher HTTP JSON-RPC para switches ExtremeXOS."""

    def _fetch(host: str, cmd: str) -> dict:
        url = f"http://{host}:{port}/jsonrpc"
        payload = {"jsonrpc": "2.0", "id": 1, "method": "cli", "params": [cmd]}
        resp = requests.post(url, auth=(user, password), json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    return _fetch


def crawl_exos_topology(
    seed_ip: str,
    fetcher: CliFetcher,
    seed_name: str = "EXOS-Seed",
) -> tuple[Topology, list[str]]:
    """Mapeia automaticamente a rede em largura (BFS) a partir de `seed_ip`.

    Devolve a topologia agregada (sem links duplicados) e uma lista de avisos
    para switches vizinhos que não responderam ao pedido de gestão.
    """
    queue: deque[tuple[str, str]] = deque([(seed_ip, seed_name)])
    visited_ips: set[str] = set()

    devices: list[Device] = []
    seen_links: set[frozenset[tuple[str, str]]] = set()
    links: list[Link] = []
    warnings: list[str] = []

    while queue:
        ip, dev_name = queue.popleft()
        if ip in visited_ips:
            continue
        visited_ips.add(ip)

        try:
            ports_raw = fetcher(ip, "show ports no-refresh")
            lldp_raw = fetcher(ip, "show lldp neighbors")
        except requests.RequestException as exc:
            warnings.append(f"Não foi possível contactar {dev_name} ({ip}): {exc}")
            continue

        devices.append(normalize_exos_device(dev_name, ports_raw, management_ip=ip))

        for link in normalize_exos_lldp(dev_name, lldp_raw):
            key = frozenset(
                [
                    (link.source_device, link.source_interface),
                    (link.target_device, link.target_interface),
                ]
            )
            if key not in seen_links:
                seen_links.add(key)
                links.append(link)

        for nbr_name, nbr_ip in extract_lldp_neighbor_ips(lldp_raw):
            if nbr_ip not in visited_ips:
                queue.append((nbr_ip, nbr_name))

    return Topology(name="discovered-topology", devices=devices, links=links), warnings
