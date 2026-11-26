"""Ciclo completo do Digital Twin: descobre a rede EXOS (BFS) e sincroniza com o GNS3."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.crawler import crawl_exos_topology, make_jsonrpc_fetcher
from src.gns3_sync import Gns3Client, sync_topology_to_gns3


def main() -> None:
    """Executa descoberta BFS na rede real e espelha nós/links no projeto GNS3."""
    parser = argparse.ArgumentParser(description="Sincroniza rede EXOS com GNS3 em tempo real.")
    parser.add_argument(
        "--project", default="trial1", help="Projeto GNS3 de destino (Digital Twin)"
    )
    parser.add_argument("--template", default="EXOS", help="Template EXOS no GNS3")
    parser.add_argument("--seed-name", default="EXOS-A", help="Nome do switch inicial")
    parser.add_argument("--interval", type=int, default=10, help="Intervalo de polling (segundos)")
    parser.add_argument("--once", action="store_true", help="Sincroniza apenas uma vez e sai")
    args = parser.parse_args()

    load_dotenv()
    seed_ip = os.getenv("EXOS_HOST", "192.168.122.210")
    exos_port = int(os.getenv("EXOS_PORT", "80"))
    exos_user = os.getenv("EXOS_USER", "admin")
    exos_password = os.getenv("EXOS_PASSWORD", "")
    gns3_url = os.getenv("GNS3_BASE_URL", "http://localhost:3080/v2")

    fetcher = make_jsonrpc_fetcher(port=exos_port, user=exos_user, password=exos_password)
    gns3 = Gns3Client(base_url=gns3_url)

    print(f"A sincronizar '{seed_ip}' -> projeto GNS3 '{args.project}' (Ctrl+C para parar).")

    try:
        while True:
            ts = time.strftime("%H:%M:%S")
            topology, warnings = crawl_exos_topology(seed_ip, fetcher, seed_name=args.seed_name)

            if not topology.devices:
                print(f"[{ts}] Sem contacto com o switch semente; réplica GNS3 mantida.")
                for w in warnings:
                    print(f"  [!] Aviso: {w}")
                if args.once:
                    break
                time.sleep(args.interval)
                continue

            report = sync_topology_to_gns3(gns3, args.project, args.template, topology)

            if report.has_changes:
                print(f"[{ts}] GNS3 atualizado:")
                for node in report.created_nodes:
                    print(f"  [+] Nó criado: {node}")
                for link in report.created_links:
                    print(f"  [+] Cabo ligado: {link}")
                for link_id in report.deleted_links:
                    print(f"  [-] Cabo removido (link_id={link_id})")
            else:
                print(
                    f"[{ts}] Em sincronia ({len(topology.devices)} switches, "
                    f"{len(topology.links)} cabos)."
                )

            for w in warnings:
                print(f"  [!] Aviso: {w}")

            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nSincronização terminada pelo utilizador.")
    except (requests.RequestException, ValueError) as exc:
        print(f"\nErro durante a sincronização: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
