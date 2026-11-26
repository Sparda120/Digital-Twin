# ADR 001: Documentação Contínua (Docs-as-Code) e Pipeline de CI

- **Data:** 2026-11-26
- **Estado:** Aceite

## Contexto
Este projeto corresponde à unidade curricular de Projeto Final da Licenciatura em Engenharia Informática (IPT) e exige um relatório técnico rigoroso. Além disso, o desenvolvimento envolve integração com equipamentos de rede (EXOS, Cisco, Juniper) e com a API REST do GNS3.

## Opções Consideradas
1. **Documentação apenas no final em ficheiro binário (`.docx`):** Risco elevado de perda de detalhe técnico ao longo dos meses e histórico pouco legível no Git.
2. **Docs-as-Code em Markdown (`docs/devlog.md` + `docs/decisions/`) + CI automático:** Registo incremental versionado no GitHub junto ao código, combinado com verificação automática de estilo e testes.

## Decisão
- Manter um diário de bordo (`docs/devlog.md`) atualizado a cada passo verificável e registos de decisões técnicas (`docs/decisions/*.md`).
- Manter o workflow de GitHub Actions (`.github/workflows/ci.yml`) com `ruff`, `yamllint` e `pytest` sobre dados simulados (*fixtures*), deixando os testes contra o GNS3/switches reais para execução local.

## Consequências
- **Positivas:** O histórico Git reflete a evolução real do projeto e serve de base direta para os capítulos de arquitetura, implementação e testes do relatório final; o código mantém qualidade consistente.
- **Negativas / Cuidados:** Requer disciplina para atualizar o `devlog.md` no final de cada marco e separar claramente testes unitários offline (CI) de testes de integração em laboratório (locais).
