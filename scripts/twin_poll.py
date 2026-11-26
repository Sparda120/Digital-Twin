"""Ciclo de polling do Digital Twin: recolhe EXOS, compara estado e sincroniza com GNS3."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# Garante que `src` é encontrado ao correr `python scripts/twin_poll.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.diff import TopologyDiff, diff_topologies
from src.exos_normalizer import normalize_exos_device, normalize_exos_lldp
from src.models import Topology


def run_exos_cli(host: str, port: int, user: str, password: str, cmd: str) -> dict:
    """Executa um comando CLI no EXOS via POST /jsonrpc."""
    url = f"http://{host}:{port}/jsonrpc"
    payload = {"jsonrpc": "2.0", "id": 1, "method": "cli", "params": [cmd]}
    resp = requests.post(url, auth=(user, password), json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def collect_snapshot(host: str, port: int, user: str, password: str, device_name: str) -> Topology:
    """Recolhe portas e LLDP do EXOS e devolve um snapshot Topology normalizado."""
    ports_raw = run_exos_cli(host, port, user, password, "show ports no-refresh")
    lldp_raw = run_exos_cli(host, port, user, password, "show lldp neighbors")

    device = normalize_exos_device(device_name, ports_raw, management_ip=host)
    links = normalize_exos_lldp(device_name, lldp_raw)
    return Topology(name="exos-twin", devices=[device], links=links)


def print_diff(diff: TopologyDiff) -> None:
    """Imprime de forma legível as alterações detetadas entre dois snapshots."""
    for dev in diff.added_devices:
        print(f"  [+] Novo switch: {dev.name}")
    for dev in diff.removed_devices:
        print(f"  [-] Switch removido: {dev.name}")
    for change in diff.port_changes:
        old_s = "UP" if change.was_enabled else "DOWN"
        new_s = "UP" if change.is_enabled else "DOWN"
        print(f"  [~] Porta {change.device}:{change.interface} mudou de {old_s} -> {new_s}")
    for link in diff.added_links:
        print(
            f"  [+] Novo cabo: {link.source_device}:{link.source_interface} "
            f"<-> {link.target_device}:{link.target_interface}"
        )
    for link in diff.removed_links:
        print(
            f"  [-] Cabo removido: {link.source_device}:{link.source_interface} "
            f"<-> {link.target_device}:{link.target_interface}"
        )


def main() -> None:
    """Corre o ciclo de polling ao EXOS e mostra alterações em tempo real."""
    parser = argparse.ArgumentParser(description="Polling e deteção de alterações no EXOS.")
    parser.add_argument("--name", default="EXOS-Switch-1", help="Nome do switch local")
    parser.add_argument("--interval", type=int, default=10, help="Intervalo em segundos")
    parser.add_argument("--once", action="store_true", help="Executa apenas 1 leitura e sai")
    args = parser.parse_args()

    load_dotenv()
    host = os.getenv("EXOS_HOST", "192.168.122.210")
    port = int(os.getenv("EXOS_PORT", "80"))
    user = os.getenv("EXOS_USER", "admin")
    password = os.getenv("EXOS_PASSWORD", "")

    print(f"A iniciar polling a {host}:{port} (a cada {args.interval}s). Ctrl+C para parar.")
    previous: Topology | None = None

    try:
        while True:
            current = collect_snapshot(host, port, user, password, args.name)
            ts = time.strftime("%H:%M:%S")

            if previous is None:
                up_ports = [i.name for i in current.devices[0].interfaces if i.enabled]
                print(
                    f"[{ts}] Snapshot inicial: {len(current.devices[0].interfaces)} portas "
                    f"(UP: {up_ports}), {len(current.links)} link(s) LLDP."
                )
            else:
                diff = diff_topologies(previous, current)
                if diff.has_changes:
                    print(f"[{ts}] Alterações detetadas:")
                    print_diff(diff)
                else:
                    print(f"[{ts}] Sem alterações.")

            previous = current
            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nPolling terminado pelo utilizador.")
    except requests.RequestException as exc:
        print(f"\nErro de comunicação com o EXOS: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
