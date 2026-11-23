from __future__ import annotations

import ipaddress

from src.models import Topology


class TopologyValidationError(Exception):
    """Exceção levantada quando a topologia do Digital Twin contém erros estruturais."""


def validate_topology(topology: Topology) -> list[str]:
    """Valida a consistência técnica da topologia do Digital Twin.

    Retorna uma lista de avisos (warnings) ou levanta TopologyValidationError se houver
    erros críticos (portas inexistentes, loops físicos impossíveis, colisões de IP).
    """
    warnings: list[str] = []

    # 1. Validar unicidade dos nomes dos equipamentos
    device_names = set()
    device_map = {}
    for device in topology.devices:
        if device.name in device_names:
            raise TopologyValidationError(f"Dispositivo duplicado na topologia: '{device.name}'")
        device_names.add(device.name)
        device_map[device.name] = device

        # Validar unicidade de interfaces no dispositivo
        iface_names = set()
        for iface in device.interfaces:
            if iface.name in iface_names:
                raise TopologyValidationError(
                    f"Interface duplicada no dispositivo '{device.name}': '{iface.name}'"
                )
            iface_names.add(iface.name)

    # 2. Validar conexões (links)
    used_interfaces: set[tuple[str, str]] = set()

    for idx, link in enumerate(topology.links):
        src_dev = link.source_device
        src_if = link.source_interface
        dst_dev = link.target_device
        dst_if = link.target_interface

        # Dispositivos existem?
        if src_dev not in device_map:
            raise TopologyValidationError(
                f"Link #{idx}: Dispositivo de origem '{src_dev}' não existe na topologia."
            )
        if dst_dev not in device_map:
            raise TopologyValidationError(
                f"Link #{idx}: Dispositivo de destino '{dst_dev}' não existe na topologia."
            )

        if src_dev == dst_dev and src_if == dst_if:
            raise TopologyValidationError(
                f"Link #{idx}: Interface '{src_dev}:{src_if}' ligada a si própria (loop inválido)."
            )

        # Interfaces existem nos dispositivos?
        src_ifaces = {i.name: i for i in device_map[src_dev].interfaces}
        dst_ifaces = {i.name: i for i in device_map[dst_dev].interfaces}

        if src_if not in src_ifaces:
            raise TopologyValidationError(
                f"Link #{idx}: Interface '{src_if}' não existe no dispositivo '{src_dev}'."
            )
        if dst_if not in dst_ifaces:
            raise TopologyValidationError(
                f"Link #{idx}: Interface '{dst_if}' não existe no dispositivo '{dst_dev}'."
            )

        # Interface já conectada a outro link?
        if (src_dev, src_if) in used_interfaces:
            raise TopologyValidationError(
                f"Interface '{src_dev}:{src_if}' já está ligada a outro link."
            )
        if (dst_dev, dst_if) in used_interfaces:
            raise TopologyValidationError(
                f"Interface '{dst_dev}:{dst_if}' já está ligada a outro link."
            )

        used_interfaces.add((src_dev, src_if))
        used_interfaces.add((dst_dev, dst_if))

        # 3. Validar consistência de sub-rede se ambos tiverem IP
        src_obj = src_ifaces[src_if]
        dst_obj = dst_ifaces[dst_if]

        if src_obj.ip_address and dst_obj.ip_address:
            src_net = ipaddress.IPv4Interface(src_obj.ip_address).network
            dst_net = ipaddress.IPv4Interface(dst_obj.ip_address).network
            if src_net != dst_net:
                raise TopologyValidationError(
                    f"Incompatibilidade de sub-rede no link {src_dev}:{src_if} "
                    f"({src_obj.ip_address}) <-> {dst_dev}:{dst_if} ({dst_obj.ip_address}). "
                    f"Sub-redes: {src_net} vs {dst_net}"
                )

    return warnings
