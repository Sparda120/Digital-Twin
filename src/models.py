from __future__ import annotations

import ipaddress
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class DeviceType(str, Enum):
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    HOST = "host"


class Interface(BaseModel):
    name: str = Field(..., description="Nome da interface, ex: eth0, GigabitEthernet0/1")
    ip_address: str | None = Field(
        None, description="Endereço IPv4 com máscara CIDR, ex: 192.168.1.1/24"
    )
    vlan_id: int | None = Field(None, ge=1, le=4094, description="VLAN ID (1-4094)")
    enabled: bool = Field(True, description="Estado operacional da interface")

    @field_validator("ip_address")
    @classmethod
    def validate_ipv4(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                ipaddress.IPv4Interface(v)
            except ValueError as e:
                raise ValueError(f"Endereço IP inválido: {v}") from e
        return v


class Device(BaseModel):
    name: str = Field(..., description="Identificador único do equipamento de rede")
    device_type: DeviceType = Field(..., description="Tipo de dispositivo na topologia")
    model: str = Field("generic", description="Modelo ou imagem de emulação (ex: EXOS, Cisco-IOS)")
    management_ip: str | None = Field(None, description="IP de gestão do dispositivo")
    interfaces: list[Interface] = Field(default_factory=list, description="Lista de interfaces")

    @field_validator("management_ip")
    @classmethod
    def validate_mgmt_ip(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                ipaddress.IPv4Address(v)
            except ValueError as e:
                raise ValueError(f"IP de gestão inválido: {v}") from e
        return v


class Link(BaseModel):
    source_device: str = Field(..., description="Dispositivo de origem")
    source_interface: str = Field(..., description="Interface de origem")
    target_device: str = Field(..., description="Dispositivo de destino")
    target_interface: str = Field(..., description="Interface de destino")
    latency_ms: float = Field(0.0, ge=0.0, description="Latência em milissegundos")
    bandwidth_mbps: int = Field(1000, gt=0, description="Largura de banda em Mbps")


class Topology(BaseModel):
    name: str = Field(..., description="Nome da topologia de rede do Digital Twin")
    description: str | None = Field(None, description="Descrição detalhada do cenário")
    devices: list[Device] = Field(default_factory=list, description="Equipamentos da topologia")
    links: list[Link] = Field(default_factory=list, description="Conexões físicas entre interfaces")
