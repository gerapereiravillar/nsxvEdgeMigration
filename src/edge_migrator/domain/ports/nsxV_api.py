from typing import Protocol, List, Dict, Any, Optional
from xml.etree import ElementTree as ET
from src.edge_migrator.shared.response import Response
from src.edge_migrator.domain.canonical import fwRule,dnatRule,snatRule,private_network, natrules 

class NSXVApi(Protocol):
    """Puerto para el adapter de NSX-V (solo métodos públicos actuales)."""

    def test_login(self) -> Response:
        """Prueba de login en NSX-V."""
        

    def get_vnics(self, edge_id: str) -> Response[List[Dict[str, str]]]:
        """Lista vNICs del Edge y sus CIDR (primarios/secundarios)."""

    def get_nat_rules(self, edge_id: str) -> Response[natrules]:
        """Obtiene reglas de NAT del Edge en NSX-V."""

