import pytest
from pydantic import ValidationError

from src.models import Device, DeviceType, Interface, Link, Topology


def test_valid_interface_creation():
    iface = Interface(name="eth0", ip_address="192.168.1.1/24", vlan_id=10, enabled=True)
    assert iface.name == "eth0"
    assert iface.ip_address == "192.168.1.1/24"
    assert iface.vlan_id == 10
    assert iface.enabled is True


def test_invalid_ip_interface():
    with pytest.raises(ValidationError):
        Interface(name="eth0", ip_address="999.999.999.999/24")


def test_invalid_vlan_range():
    with pytest.raises(ValidationError):
        Interface(name="eth0", vlan_id=5000)  # VLAN max 4094


def test_device_creation():
    dev = Device(
        name="router-01",
        device_type=DeviceType.ROUTER,
        model="cisco-ios",
        management_ip="10.0.0.1",
        interfaces=[Interface(name="GigabitEthernet0/0", ip_address="10.0.1.1/30")],
    )
    assert dev.name == "router-01"
    assert dev.device_type == DeviceType.ROUTER
    assert len(dev.interfaces) == 1


def test_link_creation():
    link = Link(
        source_device="r1",
        source_interface="eth1",
        target_device="sw1",
        target_interface="port1",
        latency_ms=1.5,
        bandwidth_mbps=1000,
    )
    assert link.latency_ms == 1.5
    assert link.bandwidth_mbps == 1000


def test_topology_creation():
    top = Topology(name="lab-test")
    assert top.name == "lab-test"
    assert top.devices == []
    assert top.links == []
