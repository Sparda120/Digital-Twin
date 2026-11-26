from __future__ import annotations

from src.diff import diff_topologies
from src.models import Device, DeviceType, Interface, Link, Topology


def _make_switch(name: str, port1_up: bool) -> Device:
    return Device(
        name=name,
        device_type=DeviceType.SWITCH,
        model="EXOS",
        interfaces=[Interface(name="1", vlan_id=1, enabled=port1_up)],
    )


def test_diff_no_changes() -> None:
    topo = Topology(
        name="twin",
        devices=[_make_switch("SW1", True)],
        links=[
            Link(
                source_device="SW1",
                source_interface="1",
                target_device="SW2",
                target_interface="1",
            )
        ],
    )
    diff = diff_topologies(topo, topo)
    assert diff.has_changes is False


def test_diff_link_removed_and_port_down() -> None:
    before = Topology(
        name="twin",
        devices=[_make_switch("SW1", True), _make_switch("SW2", True)],
        links=[
            Link(
                source_device="SW1",
                source_interface="1",
                target_device="SW2",
                target_interface="1",
            )
        ],
    )
    after = Topology(
        name="twin",
        devices=[_make_switch("SW1", False), _make_switch("SW2", False)],
        links=[],
    )

    diff = diff_topologies(before, after)
    assert diff.has_changes is True
    assert len(diff.removed_links) == 1
    assert len(diff.added_links) == 0
    assert len(diff.port_changes) == 2
    assert diff.port_changes[0].was_enabled is True
    assert diff.port_changes[0].is_enabled is False


def test_diff_bidirectional_link_is_same() -> None:
    link_ab = Link(
        source_device="SW1", source_interface="1", target_device="SW2", target_interface="2"
    )
    link_ba = Link(
        source_device="SW2", source_interface="2", target_device="SW1", target_interface="1"
    )
    before = Topology(name="twin", devices=[], links=[link_ab])
    after = Topology(name="twin", devices=[], links=[link_ba])

    diff = diff_topologies(before, after)
    assert diff.has_changes is False
