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
