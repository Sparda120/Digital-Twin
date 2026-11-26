from __future__ import annotations

from src.gns3_sync import sync_topology_to_gns3
from src.models import Device, DeviceType, Interface, Link, Topology


class FakeGns3Client:
    """Cliente GNS3 em memória para testar a sincronização sem servidor real."""

    def __init__(self) -> None:
        self.nodes: list[dict] = []
        self.links: list[dict] = []
        self._counter = 0

    def find_project_id(self, project_name: str) -> str:
        return "proj-1"

    def find_template_id(self, query: str) -> str:
        return "tmpl-exos"

    def list_nodes(self, project_id: str) -> list[dict]:
        return list(self.nodes)

    def create_node(self, project_id: str, template_id: str, name: str, x: int, y: int) -> dict:
        self._counter += 1
        node = {
            "node_id": f"node-{self._counter}",
            "name": name,
            "ports": [
                {"name": "Mgmt", "adapter_number": 0, "port_number": 0},
                {"name": "1", "adapter_number": 1, "port_number": 0},
                {"name": "2", "adapter_number": 2, "port_number": 0},
            ],
        }
        self.nodes.append(node)
        return node

    def list_links(self, project_id: str) -> list[dict]:
        return list(self.links)

    def create_link(self, project_id: str, endpoints: list[dict]) -> dict:
        self._counter += 1
        link = {"link_id": f"link-{self._counter}", "nodes": endpoints}
        self.links.append(link)
        return link

    def delete_link(self, project_id: str, link_id: str) -> None:
        self.links = [lnk for lnk in self.links if lnk["link_id"] != link_id]


def test_sync_creates_nodes_and_links_then_removes_deleted_link() -> None:
    client = FakeGns3Client()
    topo_with_link = Topology(
        name="twin",
        devices=[
            Device(name="EXOS-A", device_type=DeviceType.SWITCH, interfaces=[Interface(name="1")]),
            Device(name="EXOS-B", device_type=DeviceType.SWITCH, interfaces=[Interface(name="1")]),
        ],
        links=[
            Link(
                source_device="EXOS-A",
                source_interface="1",
                target_device="EXOS-B",
                target_interface="1",
            )
        ],
    )

    # 1. Primeira sincronização cria os 2 switches e 1 link
    report1 = sync_topology_to_gns3(client, "trial1", "EXOS", topo_with_link)
    assert report1.created_nodes == ["EXOS-A", "EXOS-B"]
    assert len(report1.created_links) == 1
    assert len(report1.deleted_links) == 0

    # 2. Segunda sincronização igual não faz alterações (idempotente)
    report2 = sync_topology_to_gns3(client, "trial1", "EXOS", topo_with_link)
    assert report2.has_changes is False

    # 3. Se o cabo cair na rede real, o link é apagado no GNS3
    topo_without_link = Topology(name="twin", devices=topo_with_link.devices, links=[])
    report3 = sync_topology_to_gns3(client, "trial1", "EXOS", topo_without_link)
    assert len(report3.deleted_links) == 1
    assert len(client.links) == 0
