# Diário de Bordo — Network Digital Twin

Registo cronológico do desenvolvimento do projeto para acompanhamento contínuo e suporte à redação do relatório técnico final.

---

## 2026-11-26 — Preparação da Base, Segurança e Documentação Contínua

### O que foi feito
- **Estrutura base existente revista:** Modelos de topologia em Pydantic (`src/models.py`), leitura YAML (`src/parser.py`), validação estrutural (`src/validator.py`), testes unitários (`tests/`) e pipeline de CI no GitHub Actions (`.github/workflows/ci.yml`).
- **Segurança de credenciais:** Adicionadas regras ao `.gitignore` para ignorar ficheiros `.env` e criado o modelo `.env.example` com as variáveis de acesso ao switch EXOS e à API REST do GNS3.
- **Documentação contínua:** Criada a pasta `docs/` com este `devlog.md` e o diretório `docs/decisions/` para registos de decisões técnicas (ADRs).

### Ambiente e Laboratório Validado (Pré-requisitos)
- GNS3 local ativo com interface `virbr0` (`192.168.122.1/24`) e API REST v2 em `http://localhost:3080/v2`.
- Switches virtuais ExtremeXOS (EXOS-VM 33.1) acessíveis na VLAN `Mgmt` (ex.: `192.168.122.210`), com pedidos `POST /jsonrpc` validados previamente via Postman.

### Como foi testado
- Execução local da suite de testes e linter (`pytest` e `ruff check .`) para garantir integridade antes de iniciar o coletor dinâmico.

### Próximo passo
- Criar o primeiro script Python mínimo para substituir o Postman na recolha de dados do switch EXOS via `POST /jsonrpc`.

---

## 2026-11-26 (Parte 2) — Primeiros Scripts Python com a API REST do GNS3

### O que foi feito
- **Dependências HTTP e configuração local:** Adicionadas as bibliotecas `requests` e `python-dotenv` ao `requirements.txt` e `pyproject.toml`, e criado o ficheiro `.env` local (ignorado pelo Git) com `GNS3_BASE_URL`.
- **Validação de ligação (`scripts/gns3_hello.py`):** Implementado script mínimo que consulta `GET /v2/version` e `GET /v2/projects`.
- **Criação automática de nós (`scripts/gns3_create_switch.py`):** Implementado script que localiza um projeto e um template pelo nome e cria um switch via `POST /v2/projects/{project_id}/templates/{template_id}`.

### Como foi testado
- `python scripts/gns3_hello.py`: Ligação bem-sucedida ao servidor GNS3 local; detetados 3 projetos (2 fechados e `trial1` aberto).
- `python scripts/gns3_create_switch.py --project trial1`: Switch `EXOS-Twin-1` criado automaticamente a partir do template EXOS e visível na topologia do projeto `trial1`.
- Verificação de qualidade: `ruff check .`, `ruff format --check .` e `pytest -q` (14 testes) passaram sem erros.

### Próximo passo
- Compreender e estruturar o ciclo completo do Digital Twin (Recolha $\rightarrow$ Normalização/Diff $\rightarrow$ Replicação no GNS3) antes de ligar os scripts ao *polling* contínuo.

---

## 2026-11-26 (Parte 3) — Recolha JSON-RPC no EXOS e Normalização

### O que foi feito
- **Coletor EXOS (`scripts/exos_collect.py`):** Implementado script mínimo que autentica via Basic Auth em `POST http://<EXOS_HOST>/jsonrpc` e executa comandos CLI no switch EXOS-VM (`show ports no-refresh`, `show vlan`, `show lldp neighbors`).
  - *Descoberta técnica:* O método `cli` da API JSON-RPC do ExtremeXOS exige os parâmetros em formato de lista (`"params": [cmd]`) e não em objeto (`{"cmd": ...}`).
- **Amostras reais (`samples/`):** Extraídas respostas reais (`exos_ports.json` com 2675 linhas e `exos_lldp.json` com vizinho LLDP ativo na porta 1).
- **Normalizador (`src/exos_normalizer.py`):** Criadas as funções `normalize_exos_device` e `normalize_exos_lldp` para converter as respostas brutas do EXOS para os modelos comuns `Device`, `Interface` e `Link` (`src/models.py`).
- **Testes automatizados (`tests/test_exos_normalizer.py`):** Adicionados testes unitários sobre os ficheiros em `samples/` para validar a extração das 12 portas, estado ativo/inativo, VLAN e vizinho LLDP.

### Como foi testado
- Conectividade validada ao EXOS-VM via `NAT` (`virbr0`, `192.168.122.210`).
- `pytest -v` (incluindo os novos testes de normalização) e `ruff check .` / `ruff format --check .` executados com sucesso.

### Próximo passo
- Implementar a **Peça 5**: comparação de estado (*diff* entre dois *snapshots*) e ciclo de *polling* para sincronizar alterações no GNS3.

---

## 2026-11-26 (Parte 4) — Motor de Diff, Polling e Descoberta Automática (BFS Crawler)

### O que foi feito
- **Motor de comparação (`src/diff.py`):** Implementada a função `diff_topologies(previous, current)` com suporte a links bidirecionais (`A:1 <-> B:1` equivalente a `B:1 <-> A:1`), detetando switches adicionados/removidos, cabos adicionados/removidos e alterações de estado das portas (`UP <-> DOWN`).
- **Ciclo de Polling (`scripts/twin_poll.py`):** Criado script de monitorização contínua ao switch EXOS que deteta e imprime alterações em tempo real.
- **Descoberta Automática BFS (`src/crawler.py` e `scripts/twin_crawl.py`):** Implementado crawler em largura (*Breadth-First Search*) a partir de um único switch semente (`seed_ip`), com controlo de nós já visitados para evitar loops e tolerância a vizinhos inacessíveis.
- **Descoberta técnica EXOS (LLDP Management Address):** Identificado que no ExtremeXOS 33.1 o campo `nbrMgmtAddr` (quando `nbrMgmtAddrType == 1`, IPv4) vem codificado em bytes hexadecimais separados por `:` (ex.: `c0:a8:7a:d3` $\rightarrow$ `192.168.122.211`). Adicionado `parse_exos_mgmt_ip` em `src/exos_normalizer.py` e documentada a arquitetura na ADR 002 (`docs/decisions/002-descoberta-bfs-lldp.md`).
- **Testes automatizados (`tests/test_diff.py`, `tests/test_crawler.py`):** Adicionados 5 novos testes unitários (total de 21 testes a passar).

### Como foi testado
- `scripts/twin_poll.py --interval 5` validado ao vivo contra o EXOS-VM (`192.168.122.210`), detetando desligamento/religamento de cabos na porta 1.
- `scripts/twin_crawl.py` validado contra o EXOS-A (`192.168.122.210`), descobrindo automaticamente `EXOS-B` (`192.168.122.211`) e `EXOS-VM` via LLDP.
- `ruff check .`, `ruff format --check .` e `pytest -v` (21 passed) validados localmente.

### Próximo passo
- Ligar a porta `Mgmt` de todos os switches ao `NAT` (via `Ethernet switch` de gestão) para o crawler visitar toda a rede, e conectar os eventos de *diff* à criação/remoção automática de links na API do GNS3.

---

## 2026-11-26 (Parte 5) — Sincronização Ponta-a-Ponta com o GNS3 (`gns3_sync` + `twin_sync`)

### O que foi feito
- **Filtro de gestão (`src/exos_normalizer.py`):** Atualizado `normalize_exos_lldp` com `ignore_mgmt=True` para excluir ligações LLDP da porta `mgmt` (geradas pelo `Ethernet switch` central de gestão) e manter apenas links de dados.
- **Sincronizador GNS3 (`src/gns3_sync.py`):** Implementados `Gns3Client` e `sync_topology_to_gns3`, que criam nós em falta, estabelecem novos links (`POST /links`) e removem links inexistentes (`DELETE /links/{link_id}`), garantindo idempotência.
- **Script ponta-a-ponta (`scripts/twin_sync.py`):** Integração completa do crawler BFS (`src/crawler.py`) com a sincronização automática no GNS3 (suporta `--once` e ciclo contínuo `--interval`).
- **Testes automatizados (`tests/test_gns3_sync.py`):** Adicionado teste em memória para criação inicial, execução idempotente e remoção de links (total de 22 testes a passar).

### Como foi testado
- Validação em ambiente virtual com dois projetos simultâneos no servidor GNS3:
  - Projeto `trial1` a simular a rede física (`EXOS-A` em `192.168.122.210` e `EXOS-B` em `192.168.122.211`).
  - Projeto `digital_twin_replica` criado como réplica limpa.
- Execução de `python scripts/twin_sync.py --project digital_twin_replica --once`: criou automaticamente os 3 nós (`EXOS-A`, `EXOS-B`, `EXOS-VM`) e os 3 cabos de dados (`EXOS-A:1 <-> EXOS-B:1`, `EXOS-A:2 <-> EXOS-VM:1`, `EXOS-B:2 <-> EXOS-VM:2`).
- `ruff check .`, `ruff format --check .` e `pytest -v` (22 passed) executados com sucesso.

### Próximo passo
- Evoluir para o **Marco 5 (Multi-Vendor)**: abstrair o coletor e normalizador por fabricante (Cisco IOS/RESTCONF/SSH e Juniper) mantendo o mesmo modelo comum e fluxo de sincronização.
