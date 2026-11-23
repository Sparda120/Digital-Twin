from __future__ import annotations

from pathlib import Path

import yaml

from src.models import Topology
from src.validator import validate_topology


def load_topology_from_yaml(file_path: str | Path) -> Topology:
    """Lê um ficheiro YAML de topologia, carrega para o modelo Pydantic e valida regras de rede."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Ficheiro de topologia não encontrado: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Formato inválido no ficheiro {path}: esperado dicionário YAML.")

    topology = Topology.model_validate(data)
    validate_topology(topology)
    return topology
