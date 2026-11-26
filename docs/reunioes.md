# Registo de Reuniões com o Orientador

Documento de preparação e ata das reuniões de acompanhamento do Projeto Final (**Network Digital Twin**).

---

## Próxima Reunião (Preparação)

### 1. Ponto de Situação Atual
- **Infraestrutura e Repositório:** Estrutura base em Python (`src/models.py`, `src/parser.py`, `src/validator.py`), pipeline de CI no GitHub Actions (`.github/workflows/ci.yml`), documentação contínua (`docs/devlog.md`, `docs/decisions/`) e 14 testes unitários a passar.
- **Integração GNS3 (Concluído):** Scripts funcionais em Python para ligar à API REST v2 do GNS3 (`scripts/gns3_hello.py`), criar switches EXOS (`scripts/gns3_create_switch.py`) e estabelecer ligações entre interfaces (`scripts/gns3_link_switches.py`).
- **Em curso:** Recolha de estado de switches EXOS via JSON-RPC (`POST /jsonrpc`) para alimentar o modelo normalizado e o mecanismo de *polling* / *diff*.

### 2. Dúvidas / Pontos a Validar com o Orientador
- [ ] **Âmbito multi-vendor:** Para a primeira versão funcional do Digital Twin, é suficiente focar em ExtremeXOS + Cisco, deixando Juniper como extensão futura ou prova de conceito?
- [ ] **Critérios de fidelidade do Digital Twin:** Além da topologia (nós, portas `up/down`, ligações LLDP e VLANs), que nível de configuração/estado é prioritário replicar na primeira entrega (ex.: FDB/ARP, routing estático/OSPF)?
- [ ] **Estrutura do Relatório Técnico:** Validar se o formato de *Architecture Decision Records* (`docs/decisions/`) + `devlog.md` alinha com os capítulos esperados pelo IPT.

### 3. Notas e Decisões da Reunião
*(Preencher após a reunião)*
- 

---

## Histórico de Reuniões
*(As reuniões passadas serão movidas para aqui por ordem cronológica inversa.)*
