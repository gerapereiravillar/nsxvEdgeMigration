from typing import Protocol, List, Dict, Any, Optional
from src.edge_migrator.shared.response import Response
from src.edge_migrator.domain.canonical import fwRule,edgeCluster, external_network,edgeGateway, staticRoute, org, vdc, network, snatRule, dnatRule, private_network


class VcdOpenApi(Protocol):
    """Puerto para el adapter CloudAPI (NSX-T / vCloud Director moderno)."""

    # Auth / sesión
    def login(self) -> Response[None]:
        """Inicia sesión (Bearer token) para CloudAPI."""

    # Infra lookups
    def get_edge_cluster(self) -> Response[List[edgeCluster]]:
        """Lista Edge Clusters disponibles."""

    def get_external_networks(self, org_id:str=None) -> Response[List[external_network]]:
        """Lista redes externas con subredes y conteo de IPs libres."""

    def get_orgs(self) -> Response[List[org]]:
        """Lista organizaciones (nombre, id, estado)."""

    def get_orgs_by_name(self, org_name: str) -> Response[List[org]]:
        """Busca organizaciones por prefijo de nombre."""

    def get_vdc_for_org_id(self, org_id: str) -> Response[List[vdc]]:
        """Lista VDCs para una organización dada."""

    # Operaciones sobre Edge / Networking
    def create_edge(
        self,
        edge_name: str,
        vdc_id: str,
        edge_cluster_id: str,
        extern_netwrk_id: str,
        total_ips: int = 1,
        edge_desc: str = " ",
    ) -> Response[edgeGateway]:
        """Crea un Edge Gateway conectado a una red externa."""

    def create_firewall_rule(self, firewall_rules: fwRule, edge_id: str) -> Response[Dict[str, Optional[str]]]:
        """Crea una regla de firewall en un Edge."""

    def create_snat_rule(self, snat_rule: snatRule, edge_id: str) -> Response[Dict[str, Optional[str]]]:
        """Crea una regla de SNAT en un Edge."""

    def create_dnat_rule(self, dnat_rule: dnatRule, edge_id: str, vdc_id:str, org_id:str) -> Response[Dict[str, Optional[str]]]:
        """Crea una regla de DNAT en un Edge."""

    def get_edge_public_ips(self, edge_id: str) -> Response[List[str]]:
        """Obtiene IPs públicas (primary + rangos) configuradas en el Edge."""

    def create_static_route(self, static_route: staticRoute, edge_id: str) -> Response[Dict[str, Optional[str]]]:
        """Crea una ruta estática en el Edge."""

    def create_private_network(self, private_network: private_network, vdc_id: str, edge_id:str) -> Response[Dict[str, Optional[str]]]:
        """Crea una Org VDC Network interna (NAT_ROUTED)."""

    def create_vdc_application_port_prfile(
        self, aplication_profile: Dict[str, Any], org_id: str, vdc_id: str
    ) -> Response[Dict[str, Optional[str]]]:
        """Crea un Application Port Profile a nivel de VDC (TENANT-scope)."""


    def get_application_port_prfile(self, name, vdc_id)-> Response[Dict[str, Optional[str]]]:
        """Obtiene un Application Port Profile a nivel de VDC (TENANT-scope)."""

