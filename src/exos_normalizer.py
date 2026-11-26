"""Normalizador de respostas JSON-RPC do ExtremeXOS para o modelo comum do Digital Twin."""

from __future__ import annotations

from src.models import Device, DeviceType, Interface, Link


def normalize_exos_device(
    device_name: str,
    ports_payload: dict,
    management_ip: str | None = None,
) -> Device:
    """Converte a resposta JSON-RPC de `show ports no-refresh` num objeto Device."""
    port_states: dict[int, bool] = {}
    port_vlans: dict[int, int] = {}

    for entry in ports_payload.get("result", []):
        if not isinstance(entry, dict):
            continue

        if "show_ports_info" in entry:
            info = entry["show_ports_info"]
            port_num = int(info["port"])
            # No EXOS, linkState == 1 significa Active (cabo ligado e operacional)
            port_states[port_num] = info.get("linkState") == 1

        if "show_ports_info_detail_vlans" in entry:
            vlan_info = entry["show_ports_info_detail_vlans"]
            port_num = int(vlan_info["port"])
            vlan_id = vlan_info.get("vlanId")
            if vlan_id is not None and port_num not in port_vlans:
                port_vlans[port_num] = int(vlan_id)

    interfaces = [
        Interface(
            name=str(port_num),
            ip_address=None,
            vlan_id=port_vlans.get(port_num),
            enabled=enabled,
        )
        for port_num, enabled in sorted(port_states.items())
    ]

    return Device(
        name=device_name,
        device_type=DeviceType.SWITCH,
        model="EXOS",
        management_ip=management_ip,
        interfaces=interfaces,
    )


def normalize_exos_lldp(local_device: str, lldp_payload: dict) -> list[Link]:
    """Converte a resposta JSON-RPC de `show lldp neighbors` numa lista de Links."""
    links: list[Link] = []

    for entry in lldp_payload.get("result", []):
        if not isinstance(entry, dict) or "lldpPortNbrInfoShort" not in entry:
            continue

        info = entry["lldpPortNbrInfoShort"]
        links.append(
            Link(
                source_device=local_device,
                source_interface=str(info["port"]),
                target_device=str(info["nbrSysName"]),
                target_interface=str(info["nbrPortID"]),
            )
        )

    return links


def parse_exos_mgmt_ip(addr: str | None, addr_type: int | None) -> str | None:
    """Converte o `nbrMgmtAddr` em hexadecimal do EXOS (ex: 'c0:a8:7a:d3') para IPv4."""
    if not addr or addr_type != 1:
        return None
    parts = addr.split(":")
    if len(parts) != 4:
        return None
    try:
        return ".".join(str(int(part, 16)) for part in parts)
    except ValueError:
        return None


def extract_lldp_neighbor_ips(lldp_payload: dict) -> list[tuple[str, str]]:
    """Extrai pares (sys_name, mgmt_ip) dos vizinhos LLDP que anunciam IPv4 de gestão."""
    neighbors: list[tuple[str, str]] = []
    for entry in lldp_payload.get("result", []):
        if not isinstance(entry, dict) or "lldpPortNbrInfoShort" not in entry:
            continue
        info = entry["lldpPortNbrInfoShort"]
        ip = parse_exos_mgmt_ip(info.get("nbrMgmtAddr"), info.get("nbrMgmtAddrType"))
        if ip:
            neighbors.append((str(info["nbrSysName"]), ip))
    return neighbors
