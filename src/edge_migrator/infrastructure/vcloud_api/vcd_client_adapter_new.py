import os, requests
from xml.etree import ElementTree as ET
import re
from typing import Optional, Generic, TypeVar, List, Dict, Any
import xml.dom.minidom
from src.edge_migrator.shared.response import Response
import urllib3
from src.edge_migrator.domain.canonical import fwRule, dnatRule, snatRule, private_network, edgeGateway, staticRoute, org, vdc
from src.edge_migrator.infrastructure.vcloud_api.policy import xmlApiPolicy
from src.edge_migrator.infrastructure.vcloud_api.mapper import xmlMapper



#Desactivar avisos de certificados no validos 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class VcdApiAdapter:
    def __init__(self, base_url: str, user: str, org: str, password: str, api_version: str = "36.2"):
        self.base = base_url.rstrip("/")
        self.user = f"{user}@{org}"
        self.pw = password
        self.api_version = api_version
        self.session = requests.Session()
        self.session.verify = False
        self.nameSpace = "http://www.vmware.com/vcloud/v1.5"
        self.policy=xmlApiPolicy(suport_any_in_rules=True)
        self.mapper=xmlMapper(self.policy)



    # ------------------------
    # Helpers para respuestas
    # ------------------------
    def _ok(self, data):
        return Response(ok=True, data=data)

    def _err(self, msg: str):
        return Response(ok=False, error=str(msg))

    def _h(self):
        return {"Accept": f"application/*+xml;version={self.api_version}"}

    # ------------------------
    # Autenticación
    # ------------------------
    def login(self) -> Response[str]:
        """
        Iniciar sesión en la API (dura ~30 min). Devuelve el token.
        """
        r = self.session.post(f"{self.base}/api/sessions", headers=self._h(), auth=(self.user, self.pw))
        if r.status_code == 200:
            token = r.headers.get("x-vcloud-authorization")
            if token:
                self.session.headers["x-vcloud-authorization"] = token
                
                return self._ok(token)
            return self._err("No se recibió x-vcloud-authorization en el login.")
        else:
            return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # Organizaciones
    # ------------------------
    def get_orgs_urn(self) -> Response[List[org]]:
        """
        Lista organizaciones: [{'name','href','id'}, ...]
        """
        org_list: List[Dict[str, str]] = []
        r = self.session.get(f"{self.base}/api/org", headers=self._h())
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for org in root.findall(f'{{{self.nameSpace}}}Org'):
                oid = (org.get("href") or "").split("/")[-1]
                item = {"name": org.get("name"), "href": org.get("href"), "id": oid}
                org_list.append(item)
            return self._ok(self.mapper.orgs_to_canonical(org_list))
        else:
            return self._err(f"{r.status_code} {r.reason} {r.text}")

    def get_orgs_by_name(self, org_name: str) -> Response[List[org]]:
        """
        Busca organizaciones por nombre (prefijo).
        """
        org_list: List[Dict[str, str]] = []
        r = self.session.get(f"{self.base}/api/admin/orgs/query?filter=name=={org_name}*", headers=self._h())
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for org in root.findall(f'{{{self.nameSpace}}}OrgRecord'):
                oid = (org.get("href") or "").split("/")[-1]
                org_list.append({"name": org.get("name"), "id": oid})
            return self._ok(self.mapper.orgs_to_canonical(org_list))
        else:
            return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # VDCs
    # ------------------------
    def get_vdc_org_by_id(self, id: str) -> Response[List[vdc]]:
        """
        Lista VDCs de una organización por ID de org.
        """
        vdc_list: List[Dict[str, str]] = []
        r = self.session.get(
            f"{self.base}/api/query?type=adminOrgVdc&filter=org==urn:vcloud:org:{id}", headers=self._h()
        )
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for child in root.findall(f'{{{self.nameSpace}}}AdminVdcRecord'):
                vid = (child.get("href") or "").split("/")[-1]
                vdc = {
                    "name": child.get("name"),
                    "id": vid,
                    "isEnabled": child.get("isEnabled"),
                    "vcName": child.get("vcName"),
                }
                vdc_list.append(vdc)
            return self._ok(self.mapper.vdc_to_canonical(vdc_list))
        else:
            return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # Edges
    # ------------------------
    def vdc_list_edges(self, vdc_id: str) -> Response[List[edgeGateway]]:
        """
        Lista de edges de un VDC.
        """
        edge_list: List[Dict[str, str]] = []
        r = self.session.get(f"{self.base}/api/admin/vdc/{vdc_id}/edgeGateways", headers=self._h())
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for edge in root.findall(f"{{{self.nameSpace}}}EdgeGatewayRecord"):
                eid = (edge.get("href") or "").split("/")[-1]
                item = {"id": eid, "name": edge.get("name")}
                edge_list.append(item)
            return self._ok(self.mapper.edge_gateway_to_canonical(edge_list))
        else:
            return self._err(f"{r.status_code} {r.reason} {r.text}")

    def get_edge_xml(self, edge_id: str) -> Response[ET.Element]:
        """
        XML del edge.
        """
 

        r = self.session.get(f"{self.base}/api/admin/edgeGateway/{edge_id}", headers=self._h())

        if r.status_code == 200:
            return self._ok(ET.fromstring(r.content))

        else:
            print ("Encontre un error al obtener edge ")
            return self._err(f"{r.status_code} {r.reason} {r.text}")

    def get_edge_general_desc(self, edge_xml: ET.Element) -> Response[edgeGateway]:
        """
        Nombre, id, status y nsxvId del edge.
        """
        if edge_xml is None : 
            return self._err(f"Not found")
        edge_id_el = edge_xml.find(f'.//{{{self.nameSpace}}}gatewayId')
        edge_id = edge_id_el.text if edge_id_el is not None else None
        edge_desc = {
            "name": edge_xml.get("name"),
            "id": edge_xml.get("id"),
            "status": edge_xml.get("status"),
            "nsxvId": edge_id,
        }
        return self._ok(self.mapper.edge_gateway_to_canonical ([edge_desc])[0])

    # ------------------------
    # Utils XML
    # ------------------------
    def _get_children_node_value(self, node: ET.Element, tag: str, NS: str):
        el = node.find(f'{{{NS}}}{tag}')
        return (el.text.strip() if el is not None and el.text else None)
    
    def print_tree(self,element, level=0):
       indent = "  " * level
       tag = element.tag
       text = (element.text or "").strip()
       tail = (element.tail or "").strip()
       attrib = element.attrib

       print(f"{indent}Tag: {tag}")
       if attrib:
         print(f"{indent}  Atributos: {attrib}")
       if text:
          print(f"{indent}  Texto: {repr(text)}")
       if tail and level > 0:
         print(f"{indent}  Tail: {repr(tail)}")

       for child in element:
        self.print_tree(child, level + 1)
    # ------------------------
    # Redes externas (uplinks)
    # ------------------------
    def get_external_networks(self, edge_xml: ET.Element) -> Response[List[Dict[str, Any]]]:
        """
        Subredes externas del Edge (interfaces 'uplink').
        """
        NS = self.nameSpace
        ext_net_list: List[Dict[str, Any]] = []

        for gi in edge_xml.findall(f'.//{{{NS}}}GatewayInterface'):
            itype = self._get_children_node_value(node=gi, tag='InterfaceType', NS=NS)
            if (itype or '').lower() != 'uplink':
                continue

            netref = gi.find(f'{{{NS}}}Network')
            net_id = netref.get('id') if netref is not None else None
            name_el = gi.find(f'{{{NS}}}Name')
            name = name_el.text if name_el is not None else None

            subp = gi.find(f'{{{NS}}}SubnetParticipation')
            if subp is None:
                continue

            gateway = self._get_children_node_value(subp, 'Gateway', NS)
            netmask = self._get_children_node_value(subp, 'Netmask', NS)
            prefix = self._get_children_node_value(subp, 'SubnetPrefixLength', NS)
            ipaddr = self._get_children_node_value(subp, 'IpAddress', NS)
            total = self._get_children_node_value(subp, 'TotalIpCount', NS)

            ip_ranges = []
            for r in subp.findall(f'{{{NS}}}IpRanges/{{{NS}}}IpRange'):
                start = self._get_children_node_value(r, 'StartAddress', NS)
                end = self._get_children_node_value(r, 'EndAddress', NS)
                ip_ranges.append({"start": start, "end": end})

            rate_limit = self._get_children_node_value(gi, 'ApplyRateLimit', NS)
            in_rl = self._get_children_node_value(gi, 'InRateLimit', NS)
            out_rl = self._get_children_node_value(gi, 'OutRateLimit', NS)

            item = {
                "id": net_id,
                "name": name,
                "gateway": gateway,
                "mask": netmask,
                "prefixLength": (int(prefix) if prefix else None),
                "primaryIp": ipaddr,
                "total_ips": (int(float(total)) if total else None),
                "ipRanges": ip_ranges,
                "rateLimit": (rate_limit.lower() == 'true') if rate_limit else None,
                "inRateLimit": (float(in_rl) if in_rl else None),
                "outRateLimit": (float(out_rl) if out_rl else None),
            }
            ext_net_list.append(item)
        

        return self._ok(ext_net_list)

    def _netmask_to_prefix_length(self, netmask: str) -> str:
        """Convert netmask to prefix length (e.g., 255.255.255.0 -> 24)"""
        try:
            binary_str = ''
            for octet in netmask.split('.'):
                binary_str += bin(int(octet))[2:].zfill(8)
            return str(binary_str.count('1'))
        except Exception:
            return ''

    # ------------------------
    # Redes internas
    # ------------------------
    def get_id_internal_networks(self, edge_xml: ET.Element) -> Response[List[str]]:
        """
        IDs (UUID) de las Org VDC Networks conectadas como 'internal' al Edge.
        """
        NS = self.nameSpace
        ids: List[str] = []

        for gi in edge_xml.findall(f'.//{{{NS}}}GatewayInterface'):
            itype = (self._get_children_node_value(gi, 'InterfaceType', NS) or '').lower()
            if itype != 'internal':
                continue

            netref = gi.find(f'{{{NS}}}Network')
            if netref is None:
                continue

            net_id = netref.get('id')
            if net_id:
                if net_id.startswith('urn:vcloud:network:'):
                    net_id = net_id.split(':')[-1]
            else:
                href = netref.get('href')
                if href:
                    net_id = href.rstrip('/').rsplit('/', 1)[-1]
                else:
                    net_id = None

            if net_id:
                ids.append(net_id)

        return self._ok(ids)

    def get_networks_info(self, net_id_list: List[str]) -> Response[List[private_network]]:
        """
        Info de redes (OrgVdcNetwork) desde /api/network/{id}.
        """
        NS = self.nameSpace
        gc = self._get_children_node_value

        out: List[Dict[str, Any]] = []
        errors: List[str] = []

        for net_id in net_id_list:
            url = f"{self.base}/api/network/{net_id}"
            r = self.session.get(url, headers=self._h())
            if not r.ok:
                errors.append(f"{net_id}: {r.status_code} {r.reason}")
                continue

            root = ET.fromstring(r.content)

            item = {
                "name": root.get("name") or "",
                "description": gc(root, "Description", NS) or "",
                "shared": (gc(root, "IsShared", NS) or "").lower() == "true",
                "gateway": None,
                "prefixLength": None,
                "dnsServer1": None,
                "dnsServer2": None,
                "ipRanges": [],
            }

            ipscope = root.find(f'{{{NS}}}Configuration/{{{NS}}}IpScopes/{{{NS}}}IpScope')
            if ipscope is not None:
                item["gateway"] = gc(ipscope, "Gateway", NS)
                pref = gc(ipscope, "SubnetPrefixLength", NS)
                item["prefixLength"] = int(pref) if pref and pref.isdigit() else None
                item["dnsServer1"] = gc(ipscope, "Dns1", NS)
                item["dnsServer2"] = gc(ipscope, "Dns2", NS)

                for rng in ipscope.findall(f'{{{NS}}}IpRanges/{{{NS}}}IpRange'):
                    start = gc(rng, "StartAddress", NS)
                    end = gc(rng, "EndAddress", NS)
                    item["ipRanges"].append({"startAddress": start, "endAddress": end})

            out.append(item)

        if errors and not out:
            return self._err(" | ".join(errors))
        elif errors:
            # Éxito parcial: devolvemos data y un error informativo
            return Response(ok=True, data=out, error="Parcial: " + " | ".join(errors))
        else:
            return self._ok(self.mapper.priv_network_to_canonical(out))
        



    def get_vm_ips(self, vm_id: str) -> Response[List[str]]:
        """
        Dado un id de VM, retorna lista de IPs.
        """
        ip_list: List[str] = []
        r = self.session.get(f"{self.base}/api/vApp/vm-{vm_id}/networkConnectionSection", headers=self._h())
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for connection in root.findall(f'{{{self.nameSpace}}}NetworkConnection'):
                ip_address = connection.find(f'{{{self.nameSpace}}}IpAddress')
                if ip_address is not None and ip_address.text:
                    ip_list.append(ip_address.text)
            return self._ok(ip_list)
        else:
            return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # Firewall
    # ------------------------
    def _get_firewall_rules_aux_vnic_in_list(self, vnics_list: List[Dict[str, str]], vnic_name: str) -> Dict[str, str]:
        """
        Si la vnic está en la lista, retorna {"true": "network_CIDR"}, si no {"false": ""}.
        """
        for vnic in vnics_list:
            if vnic_name in vnic:
                return {"true": vnic[vnic_name]}
        return {"false": ""}

    def get_firewall_rules(
        self,
        edge_id: str,
        internal_net: List[private_network],
        vnic_newt_list: List[Dict[str, str]],
        public_ips_list: List[str],
    ) -> Response[List[fwRule]]:
        """
        Reglas de firewall del edge traducidas a redes.
        """
        respons = self.session.get(f"{self.base}/network/edges/{edge_id}/firewall/config", headers=self._h())
        if respons.status_code != 200:
            return self._err(f"{respons.status_code} {respons.reason}")

        root = ET.fromstring(respons.content)
        firewall_rules_list: List[Dict[str, Any]] = []

        for rule in root.findall(".//firewallRule"):
            if rule.findtext("ruleType") !="user": 
                continue
            item = {
                "ruleTag": rule.findtext("ruleTag"),
                "name": rule.findtext("name"),
                "enabled": rule.findtext("enabled"),
                "loggingEnabled": rule.findtext("loggingEnabled"),
                "action": rule.findtext("action"),
            }

            source = rule.find("source")
            destination = rule.find("destination")
            application = rule.find("application")

            source_list: Dict[str, Any] = {}
            destination_list: Dict[str, Any] = {}
            application_list: List[Dict[str, str]] = []
            not_maping_source_rules: List[Dict[str, str]] = []
            not_maping_destination_rules: List[Dict[str, str]] = []

            if source is not None:
                source_list = self._get_fir_rules_aux_get_dest_or_sorce(
                    source, internal_net, vnic_newt_list, public_ips_list
                )
                if "not_maped" in source_list:
                    not_maping_source_rules.extend(source_list["not_maped"])

            if destination is not None:
                destination_list = self._get_fir_rules_aux_get_dest_or_sorce(
                    destination, internal_net, vnic_newt_list, public_ips_list
                )
                if "not_maped" in destination_list:
                    not_maping_destination_rules.extend(destination_list["not_maped"])

            if application is not None:
                application_list = self._get_firewall_rules_aux_get_ports_and_protocols(application)

            item["source_ips"] = source_list.get("rules", []) if source_list else []
            item["dest_ips"] = destination_list.get("rules", []) if destination_list else []
            item["services"] = application_list
            item["not_maped_source"] = not_maping_source_rules
            item["not_maped_destination"] = not_maping_destination_rules

            firewall_rules_list.append(item)
    
        return self._ok(self.mapper.fw_rule_to_canonical(firewall_rules_list))

    def _get_fir_rules_aux_get_dest_or_sorce(
        self,
        payload: ET.Element,
        internal_net: List[private_network],
        vnic_newt_list: List[Dict[str, str]],
        public_ips_list: List[str],
    ) -> Dict[str, Any]:
        """
        Dado un <source> o <destination>, devuelve subredes/ips mapeadas y no mapeadas.
        """
        rules_list: List[str] = []
        not_maping_rules: List[Dict[str, str]] = []

        if payload is None:
            return {"rules": rules_list, "not_maped": not_maping_rules}

        for item in payload.iter():
            if item.tag == "ipAddress":
                rules_list.append(item.text)

            elif item.tag == "vnicGroupId" and re.search("internal", item.text) is not None:
                # Todas las internas como CIDR
                for net in internal_net:
                    gateway = net.get_gateway()
                    prefix = net.get_prefix_length()
                    if gateway and prefix:
                        rules_list.append(f"{gateway}/{prefix}")

            elif item.tag == "vnicGroupId" and re.search("vnic", item.text) is not None:
                vnic_result = self._get_firewall_rules_aux_vnic_in_list(vnic_newt_list, item.text)
                if "true" in vnic_result:
                    rules_list.append(vnic_result["true"])
                else:
                    not_maping_rules.append({item.tag: item.text})

            elif item.tag == "groupingObjectId" and re.search("urn:vcloud:vm:", item.text) is not None:
                vm_id = item.text.split(":")[-1]
                ips_resp = self.get_vm_ips(vm_id)
                if ips_resp.ok and ips_resp.data:
                    rules_list.extend(ips_resp.data)
                else:
                    not_maping_rules.append({item.tag: item.text})

            elif item.tag == "groupingObjectId" and re.search("urn:vcloud:network", item.text) is not None:
                net_id = item.text.split(":")[-1]
                net_resp = self.get_networks_info([net_id])
                if net_resp.ok and net_resp.data and len(net_resp.data):
                    gateway = net_resp.data[0].get_gateway()
                    prefix = net_resp.data[0].get_prefix_length()
                    if gateway and prefix:
                        rules_list.append(f"{gateway}/{prefix}")
                    else:
                        not_maping_rules.append({item.tag: item.text})
                else:
                    not_maping_rules.append({item.tag: item.text})

            elif item.tag == "vnicGroupId" and (
                re.search("external", item.text) is not None or re.search("vse", item.text) is not None
            ):
                if public_ips_list:
                    rules_list.extend(public_ips_list)
                else:
                    not_maping_rules.append({item.tag: item.text})

            elif item.tag in ("source", "destination", "exclude"):
                # omitimos
                pass
            else:
                # no se pudo mapear
                not_maping_rules.append({item.tag: item.text})
                
        return {"rules": rules_list, "not_maped": not_maping_rules}

    def _get_firewall_rules_aux_get_ports_and_protocols(self, payload: ET.Element) -> List[Dict[str, str]]:
        """
        Retorna lista de servicios: [{'protocol','port','sourcePort','icmpType'}, ...]
        """
        application_list: List[Dict[str, str]] = []
        if payload is not None:
            for serv in payload.iter():
                if serv.tag != "service":
                    continue

                item: Dict[str, str] = {}
                protocol = serv.find("protocol")
                if (protocol is not None) and protocol.text:
                    item["protocol"] = protocol.text

                if protocol is not None and protocol.text == "icmp":
                    icmp_type = serv.find("icmpType")
                    if icmp_type is not None and icmp_type.text:
                        item["icmpType"] = icmp_type.text

                port = serv.find("port")
                source_port = serv.find("sourcePort")

                if port is not None and port.text:
                    item["port"] = port.text
                if source_port is not None and source_port.text:
                    item["sourcePort"] = source_port.text

                application_list.append(item)

        return application_list

    # ------------------------
    # Rutas estáticas
    # ------------------------
    def get_static_routes(self, edge_xml: ET.Element) -> Response[List[staticRoute]]:
        """
        Devuelve rutas estáticas del Edge.
        """
        static_routes: List[Dict[str, Optional[str]]] = []
        for rule in edge_xml.findall(f'.//{{{self.nameSpace}}}StaticRoute'):
            Name = rule.find(f'{{{self.nameSpace}}}Name')
            Network = rule.find(f'{{{self.nameSpace}}}Network')
            NextHopIp = rule.find(f'{{{self.nameSpace}}}NextHopIp')
            item = {
                "Name": Name.text if Name is not None else None,
                "Network": Network.text if Network is not None else None,
                "NextHopIp": NextHopIp.text if NextHopIp is not None else None,
            }
            static_routes.append(item)
        return self._ok(self.mapper.static_route_to_canonical(static_routes))
    
    
    def get_edge_external_ips(self, edge_xml: ET.Element)->Response[list]:
            """Extrae las IPs públicas de las redes externas del Edge."""
            ext_ips_list=[]
            
            ext_net_list=self.get_external_networks(edge_xml)
            if ext_net_list.ok:
                ext_net_list=ext_net_list.data
            else : return ext_net_list
           
            for net in ext_net_list:
                  #Me quedo con la primera subred, si hay más se ignoran.
                   #Agrego la ip primaria
                   subnet=net
                   if "primaryIp" in subnet and subnet["primaryIp"] and subnet["primaryIp"] not in ext_ips_list:
                       ext_ips_list.append(subnet["primaryIp"])

                  #Agrego las IPs de los ranfos si existen
                   if "ipRanges" in subnet and len(subnet["ipRanges"]):
                          for ip_range in subnet["ipRanges"]:
                            start=None
                            end=None
                            if "start" in ip_range and ip_range["start"]:
                                start=ip_range["start"]
                            if "end" in ip_range and ip_range["end"]:
                                end=ip_range["end"]
                            if start and end:
                                #Asumo que las IPs son del mismo rango A.B.C.x
                                start_index=start.split('.')[-1]
                                end_index=end.split('.')[-1]
                                for i in range(int(start_index), int(end_index)+1):
                                    ip='.'.join(start.split('.')[:-1])+f'.{i}'
                                    if ip not in ext_ips_list:
                                        ext_ips_list.append(ip)

            return Response.success(ext_ips_list)     