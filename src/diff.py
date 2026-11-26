"""Comparação (diff) entre dois snapshots de topologia do Digital Twin."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.models import Device, Link, Topology


class PortStateChange(BaseModel):
    """Representa uma mudança de estado operacional (up/down) numa porta."""

    device: str
    interface: str
    was_enabled: bool
    is_enabled: bool


class TopologyDiff(BaseModel):
    """Resultado da comparação entre uma topologia anterior e a atual."""

    added_devices: list[Device] = Field(default_factory=list)
    removed_devices: list[Device] = Field(default_factory=list)
    added_links: list[Link] = Field(default_factory=list)
    removed_links: list[Link] = Field(default_factory=list)
    port_changes: list[PortStateChange] = Field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """Indica se houve alguma alteração entre os dois snapshots."""
        return bool(
            self.added_devices
            or self.removed_devices
            or self.added_links
            or self.removed_links
            or self.port_changes
        )


def _link_key(link: Link) -> frozenset[tuple[str, str]]:
    """Chave bidirecional única para um link (A:1 <-> B:1 é igual a B:1 <-> A:1)."""
    return frozenset(
        [
            (link.source_device, link.source_interface),
            (link.target_device, link.target_interface),
        ]
    )


def diff_topologies(previous: Topology, current: Topology) -> TopologyDiff:
    """Compara dois snapshots de topologia e devolve todas as diferenças detetadas."""
    prev_devices = {d.name: d for d in previous.devices}
    curr_devices = {d.name: d for d in current.devices}

    added_devices = [
        curr_devices[name] for name in sorted(curr_devices.keys() - prev_devices.keys())
    ]
    removed_devices = [
        prev_devices[name] for name in sorted(prev_devices.keys() - curr_devices.keys())
    ]

    prev_links = {_link_key(link): link for link in previous.links}
    curr_links = {_link_key(link): link for link in current.links}

    added_links = [link for key, link in curr_links.items() if key not in prev_links]
    removed_links = [link for key, link in prev_links.items() if key not in curr_links]

    port_changes: list[PortStateChange] = []
    for dev_name in sorted(prev_devices.keys() & curr_devices.keys()):
        prev_ifaces = {i.name: i for i in prev_devices[dev_name].interfaces}
        curr_ifaces = {i.name: i for i in curr_devices[dev_name].interfaces}
        for iface_name in sorted(prev_ifaces.keys() & curr_ifaces.keys()):
            was_up = prev_ifaces[iface_name].enabled
            is_up = curr_ifaces[iface_name].enabled
            if was_up != is_up:
                port_changes.append(
                    PortStateChange(
                        device=dev_name,
                        interface=iface_name,
                        was_enabled=was_up,
                        is_enabled=is_up,
                    )
                )

    return TopologyDiff(
        added_devices=added_devices,
        removed_devices=removed_devices,
        added_links=added_links,
        removed_links=removed_links,
        port_changes=port_changes,
    )
