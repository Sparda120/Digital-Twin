from __future__ import annotations

import requests

from src.crawler import crawl_exos_topology
from src.exos_normalizer import parse_exos_mgmt_ip


def test_parse_exos_mgmt_ip_hex() -> None:
    assert parse_exos_mgmt_ip("c0:a8:7a:d3", 1) == "192.168.122.211"
    assert parse_exos_mgmt_ip("0c:5a:4f:c4:00:00", 6) is None
    assert parse_exos_mgmt_ip(None, 1) is None


def test_crawl_exos_topology_bfs_avoids_loops() -> None:
    fake_switches = {
        "192.168.122.210": {
            "show ports no-refresh": {"result": [{"show_ports_info": {"port": 1, "linkState": 1}}]},
            "show lldp neighbors": {
                "result": [
                    {
                        "lldpPortNbrInfoShort": {
                            "port": 1,
                            "nbrSysName": "EXOS-B",
                            "nbrPortID": 1,
                            "nbrMgmtAddr": "c0:a8:7a:d3",
                            "nbrMgmtAddrType": 1,
                        }
                    }
                ]
            },
        },
        "192.168.122.211": {
            "show ports no-refresh": {
                "result": [
                    {"show_ports_info": {"port": 1, "linkState": 1}},
                    {"show_ports_info": {"port": 2, "linkState": 1}},
                ]
            },
            "show lldp neighbors": {
                "result": [
                    {
                        "lldpPortNbrInfoShort": {
                            "port": 1,
                            "nbrSysName": "EXOS-A",
                            "nbrPortID": 1,
                            "nbrMgmtAddr": "c0:a8:7a:d2",
                            "nbrMgmtAddrType": 1,
                        }
                    },
                    {
                        "lldpPortNbrInfoShort": {
                            "port": 2,
                            "nbrSysName": "EXOS-C",
                            "nbrPortID": 1,
                            "nbrMgmtAddr": "c0:a8:7a:d4",
                            "nbrMgmtAddrType": 1,
                        }
                    },
                ]
            },
        },
    }

    def fake_fetcher(host: str, cmd: str) -> dict:
        if host not in fake_switches:
            raise requests.ConnectionError("unreachable")
        return fake_switches[host][cmd]

    topo, warnings = crawl_exos_topology("192.168.122.210", fake_fetcher, seed_name="EXOS-A")

    assert [d.name for d in topo.devices] == ["EXOS-A", "EXOS-B"]
    assert len(topo.links) == 2
    assert len(warnings) == 1
    assert "EXOS-C" in warnings[0]
