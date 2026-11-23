from pathlib import Path

from src.parser import load_topology_from_yaml


def test_load_sample_campus_network():
    topo_file = Path(__file__).parent.parent / "topologies" / "campus_network.yaml"
    topology = load_topology_from_yaml(topo_file)

    assert topology.name == "ipt-campus-core"
    assert len(topology.devices) == 4
    assert len(topology.links) == 3

    # Verificar dispositivos presentes
    dev_names = {d.name for d in topology.devices}
    assert "rtr-core-01" in dev_names
    assert "sw-dist-01" in dev_names
    assert "sw-acc-01" in dev_names
    assert "srv-digitaltwin" in dev_names
