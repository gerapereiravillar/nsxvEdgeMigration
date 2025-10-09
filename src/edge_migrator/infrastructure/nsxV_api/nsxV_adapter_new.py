import os, requests
from xml.etree import ElementTree as ET
from typing import List, Dict, Optional, Any

from src.edge_migrator.shared.response import Response
from src.edge_migrator.domain.canonical import natrules, dnatRule, snatRule
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
class nsxvAdapter:
    def __init__(self, base_url: str, user: str, password: str):
        self.base = base_url.rstrip("/")
        self.user = user
        self.pw = password
        self.session = requests.Session()
        self.session.verify = False

    def _h(self):
        return {"Accept": "application/xml"}
    


    def test_login(self) -> Response:
        """Prueba de login en NSX-V."""
        url = f"{self.base}/api/4.0/edges"
        r = self.session.get(url, headers=self._h(), auth=(self.user, self.pw))
        if r.status_code == 200:
            return Response(ok=True, data="Login exitoso")
        else:
            return Response(ok=False, error=f"Login fallido: {r.status_code} {r.reason} {r.text}")

    def _get_edge_xml(self, edge_id: str) -> Response[ET.Element]:
        """
        (Privado) Trae el XML crudo del edge en NSX-V.
        """
        url = f"{self.base}/api/4.0/edges/{edge_id}"
        r = self.session.get(url, headers=self._h(), auth=(self.user, self.pw))
        if r.status_code == 200:
            try:
                return Response(ok=True, data=ET.fromstring(r.content))
            except Exception as e:
                return Response(ok=False, error=f"Error parseando XML: {e}")
        else:
            return Response(ok=False, error=f"{r.status_code} {r.reason} {r.text}")

    def get_vnics(self, edge_id: str) -> Response[List[Dict[str, str]]]:
        """Retorna la lista de vNICs y la subred a la cual están conectadas.
        Args: edge_id (str) Obligatorio
        Returns: Response con data = [{"vnic-<index>":"<IP>/<PREFIX>"}...]
                 EJ: [{"vnic-0":"192.168.0.1/24"}, {"vnic-1":"192.168.0.2/24"}]
        """
        vnics_list: List[Dict[str, str]] = []

        edge_xml_resp = self._get_edge_xml(edge_id)
        if not edge_xml_resp.ok or edge_xml_resp.data is None:
            return Response(ok=False, error=edge_xml_resp.error or "No se pudo obtener el XML del edge")

        edge_xml = edge_xml_resp.data

        # NSX-V: sin namespace en estas etiquetas
        vnics = edge_xml.findall(".//vnic")
        for vnic in vnics:
            # índice
            index_elem = vnic.find("index")
            if index_elem is None or index_elem.text is None:
                continue
            vnic_index = index_elem.text.strip()

            # conectada
            is_connected_elem = vnic.find("isConnected")
            if is_connected_elem is not None and is_connected_elem.text == "false":
                continue

            # addressGroups
            address_groups = vnic.find("addressGroups")
            if address_groups is None:
                continue

            for address_group in address_groups.findall("addressGroup"):
                # IP primaria
                primary_address_elem = address_group.find("primaryAddress")
                if primary_address_elem is None or primary_address_elem.text is None:
                    continue
                primary_address = primary_address_elem.text.strip()

                # prefix o netmask -> prefix
                prefix_length_elem = address_group.find("subnetPrefixLength")
                if prefix_length_elem is not None and prefix_length_elem.text:
                    prefix_length = prefix_length_elem.text.strip()
                else:
                    netmask_elem = address_group.find("subnetMask")
                    if netmask_elem is not None and netmask_elem.text:
                        prefix_length = self._netmask_to_prefix_length(netmask_elem.text.strip())
                    else:
                        prefix_length = "32"

                cidr = f"{primary_address}/{prefix_length}"
                vnics_list.append({f"vnic-{vnic_index}": cidr})

                # secundarias
                secondary_addresses = address_group.find("secondaryAddresses")
                if secondary_addresses is not None:
                    for ip_elem in secondary_addresses.findall("ipAddress"):
                        if ip_elem.text:
                            secondary_ip = ip_elem.text.strip()
                            secondary_cidr = f"{secondary_ip}/{prefix_length}"
                            vnics_list.append({f"vnic-{vnic_index}": secondary_cidr})

        return Response(ok=True, data=vnics_list)

    def _netmask_to_prefix_length(self, netmask: str) -> str:
        """Convierte netmask a prefix length (e.g., 255.255.255.0 -> 24)"""
        try:
            binary_str = "".join(bin(int(o))[2:].zfill(8) for o in netmask.split("."))
            return str(binary_str.count("1"))
        except Exception:
            return "32"  # por defecto si hay error

    def get_nat_rules(self, edge_id: str) -> Response[natrules]:
        """Recibe el edge_id y devuelve las reglas de NAT del Edge en NSX-V.
        Returns: Response con data = list[ dict ] por regla:
            {
              "ruleTag": str|None,
              "loggingEnabled": str|None,
              "enabled": str|None,
              "description": str|None,
              "translatedAddress": str|None,
              "action": str|None,
              "originalAddress": str|None,
              "snatMatchDestinationAddress": str|None,
              "protocol": str|None,
              "originalPort": str|None,
              "translatedPort": str|None,
              "snatMatchDestinationPort": str|None
            }
        """
        url = f"{self.base}/api/4.0/edges/{edge_id}/nat/config"
        r = self.session.get(url, headers=self._h(), auth=(self.user, self.pw))
        if r.status_code != 200:
            return Response(ok=False, error=f"{r.status_code} {r.reason} {r.text}")

        try:
            root = ET.fromstring(r.content)
        except Exception as e:
            return Response(ok=False, error=f"Error parseando XML de NAT: {e}")

        dnat_list: List[Dict[str, Optional[str]]] = []
        snat_list: List[Dict[str, Optional[str]]] = []
        for rule in root.findall(".//natRule"):
            def txt(tag: str) -> Optional[str]:
                el = rule.find(tag)
                return el.text if el is not None else None
            
            if str(txt("ruleType")).lower()!="user":
                   continue
            
            if txt("action").lower()=="dnat":
                dnat_rule=dnatRule(
                    name=txt("description") or "",
                    original_cidr=txt("originalAddress") or None,
                    translated_cidr=txt("translatedAddress") or None,
                    external_port=txt("originalPort") or None,
                    internal_port=txt("translatedPort") or None,
                    prtiority=0, 
                    active=txt("enabled").lower()=="true",
                    loggin=txt("loggingEnabled").lower()=="true",
                    protocol=txt("protocol") or "all"
                )
                dnat_list.append(dnat_rule)
            elif txt("action").lower()=="snat":
                snat_rule=snatRule(
                    name=txt("description") or "",
                    original_cidr=txt("originalAddress") or None,
                    translated_cidr=txt("translatedAddress") or None,
                    dest_cidr=txt("snatMatchDestinationAddress") or None,
                    priority=0, 
                    active=txt("enabled").lower()=="true",
                    loggin=txt("loggingEnabled").lower()=="true",
                    protocol=txt("protocol") or "all"
                )
                snat_list.append(snat_rule)



        nat_list=natrules(dnatrules=dnat_list,snatrules=snat_list)
        return Response(ok=True, data=nat_list)
