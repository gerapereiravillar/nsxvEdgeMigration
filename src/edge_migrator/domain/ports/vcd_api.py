from typing import Protocol, List, Dict, Any, Optional
from xml.etree import ElementTree as ET
from src.edge_migrator.shared.response import Response
from src.edge_migrator.domain.canonical import fwRule, edgeGateway, staticRoute, org, vdc, network, private_network





class VcdXmlApi(Protocol):
    """Puerto para el adapter XML de vCloud Director (legacy)."""

    def login(self) -> Response[str]:
        """Inicia sesión y devuelve el token."""

    def get_orgs_urn(self) -> Response[List[org]]:
        """Lista organizaciones [{'name','href','id'}, ...]."""

    def get_orgs_by_name(self, org_name: str) -> Response[List[org]]:
        """Busca organizaciones por prefijo de nombre."""

    def get_vdc_org_by_id(self, id: str) -> Response[List[vdc]]:
        """Obtiene VDCs de una organización por su ID (URN)."""

    def vdc_list_edges(self, vdc_id: str) -> Response[List[edgeGateway]]:
        """Lista los Edge Gateways del VDC."""

    def get_edge_xml(self, edge_id: str) -> Response[ET.Element]:
        """Devuelve el XML del Edge (admin/edgeGateway/{id}).El id es sin URN, ej: 
        4984684c-21b3-4894-875e-bea12b804927"""

    def get_edge_general_desc(self, edge_xml: ET.Element) -> Response[edgeGateway]:
        """Datos básicos del Edge (name, id, status, nsxvId) a partir del XML."""

    def get_external_networks(self, edge_xml: ET.Element) -> Response[List[Dict[str, Any]]]:
        """Interfaces uplink y subredes externas del Edge."""

    def get_id_internal_networks(self, edge_xml: ET.Element) -> Response[List[str]]:
        """IDs de redes internas (OrgVdcNetwork) conectadas al Edge."""

    def get_networks_info(self, net_id_list: List[str]) -> Response[List[network]]:
        """Info detallada de redes internas /api/network/{id}."""

    def get_vm_ips(self, vm_id: str) -> Response[List[str]]:
        """IPs de una VM (networkConnectionSection)."""

    def get_firewall_rules(
        self,edge_nsxv_id: str,
        edge_id: str,
        internal_net: List[private_network],
        vnic_newt_list: List[Dict[str, str]],
        public_ips_list: List[str],
    ) -> Response[List[fwRule]]:
        """Reglas de firewall del Edge mapeadas a IPs/redes."""

    def get_static_routes(self, edge_xml: ET.Element) -> Response[List[staticRoute]]:
        """Rutas estáticas del Edge (desde el XML)."""

    def get_edge_external_ips(self, edge_xml: ET.Element)->Response[list]:     
        """Retorna las ips de las interfaces externas de un edge """       