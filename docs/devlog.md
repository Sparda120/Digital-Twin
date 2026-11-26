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
