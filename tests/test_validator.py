import pytest

from src.models import Device, DeviceType, Interface, Link, Topology
from src.validator import TopologyValidationError, validate_topology


@pytest.fixture
def valid_topology() -> Topology:
    rtr = Device(
        name="rtr-1",
        device_type=DeviceType.ROUTER,
        interfaces=[
            Interface(name="eth0", ip_address="10.0.0.1/30"),
            Interface(name="eth1", ip_address="10.0.0.5/30"),
        ],
    )
    sw = Device(
        name="sw-1",
        device_type=DeviceType.SWITCH,
        interfaces=[
            Interface(name="p1", ip_address="10.0.0.2/30"),
            Interface(name="p2", vlan_id=10),
        ],
    )
    links = [
        Link(
            source_device="rtr-1",
            source_interface="eth0",
            target_device="sw-1",
            target_interface="p1",
        )
    ]
    return Topology(name="test-topo", devices=[rtr, sw], links=links)


def test_validate_valid_topology(valid_topology: Topology):
    warnings = validate_topology(valid_topology)
    assert isinstance(warnings, list)


def test_duplicate_device_name(valid_topology: Topology):
    dup = Device(name="rtr-1", device_type=DeviceType.ROUTER)
    valid_topology.devices.append(dup)
    with pytest.raises(TopologyValidationError, match="Dispositivo duplicado"):
        validate_topology(valid_topology)


def test_duplicate_interface_name(valid_topology: Topology):
    valid_topology.devices[0].interfaces.append(Interface(name="eth0", ip_address="10.0.2.1/24"))
    with pytest.raises(TopologyValidationError, match="Interface duplicada"):
        validate_topology(valid_topology)


def test_nonexistent_device_in_link(valid_topology: Topology):
    valid_topology.links.append(
        Link(
            source_device="ghost-dev",
            source_interface="eth0",
            target_device="sw-1",
            target_interface="p2",
        )
    )
    with pytest.raises(TopologyValidationError, match="não existe na topologia"):
        validate_topology(valid_topology)


def test_nonexistent_interface_in_link(valid_topology: Topology):
    valid_topology.links.append(
        Link(
            source_device="rtr-1",
            source_interface="eth999",
            target_device="sw-1",
            target_interface="p2",
        )
    )
    with pytest.raises(TopologyValidationError, match="não existe no dispositivo"):
        validate_topology(valid_topology)


def test_interface_reused_in_multiple_links(valid_topology: Topology):
    valid_topology.links.append(
        Link(
            source_device="rtr-1",
            source_interface="eth0",  # Já em uso no link 1!
            target_device="sw-1",
            target_interface="p2",
        )
    )
    with pytest.raises(TopologyValidationError, match="já está ligada a outro link"):
        validate_topology(valid_topology)


def test_mismatched_subnets(valid_topology: Topology):
    # Alterar IP da interface p1 para uma subrede diferente
    valid_topology.devices[1].interfaces[0].ip_address = "192.168.1.1/24"
    with pytest.raises(TopologyValidationError, match="Incompatibilidade de sub-rede"):
        validate_topology(valid_topology)
