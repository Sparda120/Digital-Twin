# ADR 002: Descoberta Automática de Topologia (BFS) via LLDP Management Address

- **Data:** 2026-11-26
- **Estado:** Aceite

## Contexto
O protocolo LLDP (IEEE 802.1AB) é *single-hop* (os frames não são reencaminhados por switches), pelo que consultar apenas um switch (`EXOS-A`) não revela ligações entre switches seguintes (`EXOS-B` $\leftrightarrow$ `EXOS-C`).

## Opções Consideradas
1. **Inventário estático manual:** Manter uma lista fixa de todos os IPs de gestão da rede no `.env`. Simples, mas exige atualização manual sempre que entra um switch novo.
2. **Descoberta automática em grafo (BFS — *Breadth-First Search*):** Partir apenas de um switch semente (*seed*) e seguir recursivamente os endereços de gestão anunciados pelos vizinhos LLDP, mantendo um conjunto `visited_ips` para evitar loops em topologias redundantes.

## Decisão
Adotar a descoberta automática **BFS** (`src/crawler.py`), utilizando:
- **LLDP Management Address TLV** (`configure lldp ports all advertise management-address` e `configure snmp sysName <nome>` nos equipamentos);
- Conversão do formato hexadecimal do EXOS (`nbrMgmtAddrType == 1`, ex.: `"c0:a8:7a:d3"` $\rightarrow$ `"192.168.122.211"`);
- Rede de gestão acessível (*Out-of-Band* `Mgmt` ligada ao `NAT`/`virbr0` ou *In-Band* roteada) para o controlador alcançar cada novo IP descoberto.

## Consequências
- **Positivas:** O Digital Twin mapeia automaticamente novos switches sem reconfigurar inventários; a deduplicação bidirecional de links evita arestas duplicadas; falhas de acesso a um vizinho geram avisos sem interromper o mapeamento restante.
- **Negativas / Cuidados:** Requer que os switches anunciem o IPv4 de gestão no LLDP e que o host do Digital Twin tenha conectividade IP até à rede de gestão de todos os equipamentos.
