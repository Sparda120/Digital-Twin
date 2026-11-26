"""Script de descoberta automática (BFS Crawler) a partir de 1 switch semente."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.crawler import crawl_exos_topology, make_jsonrpc_fetcher


def main() -> None:
    """Inicia a descoberta BFS no EXOS_HOST do .env e imprime a topologia completa."""
    load_dotenv()
    seed_ip = os.getenv("EXOS_HOST", "192.168.122.210")
    port = int(os.getenv("EXOS_PORT", "80"))
    user = os.getenv("EXOS_USER", "admin")
    password = os.getenv("EXOS_PASSWORD", "")

    fetcher = make_jsonrpc_fetcher(port=port, user=user, password=password)
    topology, warnings = crawl_exos_topology(seed_ip, fetcher, seed_name="EXOS-A")

    print(f"Descoberta concluída a partir de {seed_ip}:")
    print(f" - Switches visitados: {[d.name for d in topology.devices]}")
    print(f" - Ligações descobertas ({len(topology.links)}):")
    for link in topology.links:
        print(
            f"   * {link.source_device}:{link.source_interface} "
            f"<-> {link.target_device}:{link.target_interface}"
        )

    if warnings:
        print("\nAvisos:")
        for w in warnings:
            print(f" - {w}")


if __name__ == "__main__":
    main()
