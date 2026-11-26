from __future__ import annotations

import json
from pathlib import Path

from src.exos_normalizer import normalize_exos_device, normalize_exos_lldp
from src.models import DeviceType

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"


def test_normalize_exos_device_from_sample() -> None:
    ports_payload = json.loads((SAMPLES_DIR / "exos_ports.json").read_text(encoding="utf-8"))

    device = normalize_exos_device(
        device_name="EXOS-Switch-1",
        ports_payload=ports_payload,
        management_ip="192.168.122.210",
    )

    assert device.name == "EXOS-Switch-1"
    assert device.device_type == DeviceType.SWITCH
    assert device.model == "EXOS"
    assert device.management_ip == "192.168.122.210"
    assert len(device.interfaces) == 12

    iface_1 = next(i for i in device.interfaces if i.name == "1")
    assert iface_1.enabled is True
    assert iface_1.vlan_id == 1

    iface_2 = next(i for i in device.interfaces if i.name == "2")
    assert iface_2.enabled is False


def test_normalize_exos_lldp_from_sample() -> None:
    lldp_payload = json.loads((SAMPLES_DIR / "exos_lldp.json").read_text(encoding="utf-8"))

    links = normalize_exos_lldp(local_device="EXOS-Switch-1", lldp_payload=lldp_payload)

    assert len(links) == 1
    assert links[0].source_device == "EXOS-Switch-1"
    assert links[0].source_interface == "1"
    assert links[0].target_device == "EXOS-VM"
    assert links[0].target_interface == "1"
