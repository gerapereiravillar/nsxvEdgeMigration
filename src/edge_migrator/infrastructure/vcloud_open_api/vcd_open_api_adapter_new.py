import os, requests, json
from xml.etree import ElementTree as ET
import time
from ipaddress import IPv4Address
from typing import List, Dict, Any, Optional
import urllib3
from src.edge_migrator.domain.canonical import edgeCluster, org, vdc , fwRule, snatRule, dnatRule, private_network, staticRoute, edgeGateway
from src.edge_migrator.domain.canonical import external_network
from src.edge_migrator.infrastructure.vcloud_open_api.mapper import openApiMapper
from src.edge_migrator.infrastructure.vcloud_open_api.policy import openApiPolicy
from datetime import datetime#Desactivar avisos de certificados no validos
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ajusta este import según tu estructura
# p.ej.: from edge_migrator.domain.shared_objects.response import Response
from src.edge_migrator.shared.response import Response


class vCloudOpenApiAdap:
    def __init__(self, base_url: str, user: str, org: str, password: str, api_version: str = "39.1"):
        self.base = base_url.rstrip("/")
        self.user = f"{user}@{org}"
        self.password = password
        self.api_version = api_version
        self.session = requests.session()
        self.session.verify = False
        self.mapper=openApiMapper(openApiPolicy(suport_any_in_rules=False))

    # ------------------------
    # Headers base (CloudAPI)
    # ------------------------
    def _h(self) -> Dict[str, str]:
        return {"Accept": f"application/json;version={self.api_version}"}

    # ------------------------
    # Helpers de respuesta
    # ------------------------
    def _ok(self, data):
        return Response(ok=True, data=data)

    def _err(self, msg: str):
        return Response(ok=False, error=str(msg))

    # ------------------------
    # Iniciar sesión (provider)
    # ------------------------
    def login(self) -> Response[None]:
        """
        Inicia sesión en CloudAPI y guarda el token en la sesión.
        """
        r = self.session.post(
            f"{self.base}/cloudapi/1.0.0/sessions/provider",
            headers=self._h(),
            auth=(self.user, self.password),
        )
        if r.status_code == 200:
            token = r.headers.get("X-VMWARE-VCLOUD-ACCESS-TOKEN")
            if not token:
                return self._err("No se recibió X-VMWARE-VCLOUD-ACCESS-TOKEN.")
            self.session.headers["Authorization"] = f"Bearer {token}"
            return self._ok(None)
        elif r.status_code == 401:
            return self._err("Error de credenciales")
        else:
            return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # Edge Clusters
    # ------------------------
    def get_edge_cluster(self) -> Response[List[edgeCluster]]:
        """
        Obtiene los clusters de edge: [{'name','id'}, ...]
        """
        r = self.session.get(f"{self.base}/cloudapi/1.0.0/edgeClusters", headers=self._h())
        if r.status_code == 200:
            edge_cluster_list: List[Dict[str, str]] = []
            for cluster in r.json().get("values", []):
                edge_cluster_list.append({"name": cluster.get("name"), "id": cluster.get("id")})
            return self._ok(self.mapper.edge_cluster_to_canonical(edge_cluster_list))
        return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # Redes Externas
    # ------------------------
    def get_external_networks(self, org_id=None) -> Response[List[external_network]]:
        """
        Obtiene redes externas:
        [{'name','id','subnets', 'ipsFree'}, ...]
        """
        headers=self._h()

        if org_id is not None:
            org_id=str(org_id).split(":")[-1]
            headers["x-vmware-vcloud-tenant-context"]=org_id
            
        r = self.session.get(f"{self.base}/cloudapi/1.0.0/externalNetworks?pageSize=1000", headers=headers)
        if r.status_code == 200:
            network_list: List[Dict[str, Any]] = []
            for network in r.json().get("values", []):
                
                net_back_type=network["networkBackings"]["values"][0]["backingType"]
                if net_back_type.upper() =="DV_PORTGROUP": 
                    continue 
                total = network.get("totalIpCount")
                used = network.get("usedIpCount")
                ips_free = int(total or 0) - int(used or 0)
                network_list.append(
                    {
                        "name": network.get("name"),
                        "id": network.get("id"),
                        "subnets": network.get("subnets"),
                        "ipsFree": ips_free
                    }
                )
            return self._ok(self.mapper.ext_network_to_canonical(network_list))
        return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # Organizaciones
    # ------------------------
    def get_orgs(self) -> Response[List[org]]:
        """
        Obtiene organizaciones: [{'name','id','isEnabled'}, ...]
        """
        r = self.session.get(f"{self.base}/cloudapi/1.0.0/orgs?pageSize=1000", headers=self._h())
        if r.status_code == 200:
            org_list: List[Dict[str, Any]] = []
            for org in r.json().get("values", []):
                org_list.append({"name": org.get("name"), "id": org.get("id"), "isEnabled": org.get("isEnabled")})
            return self._ok(self.mapper.orgs_to_canonical(org_list))
        return self._err(f"{r.status_code} {r.reason} {r.text}")

    def get_orgs_by_name(self, org_name: str) -> Response[List[org]]:
        """
        Busca organizaciones por nombre (prefijo).
        """
        r = self.session.get(
            f"{self.base}/cloudapi/1.0.0/orgs?pageSize=1000&filter=name=={org_name}*",
            headers=self._h(),
        )
        if r.status_code == 200:
            org_list: List[Dict[str, Any]] = []
            for org in r.json().get("values", []):
                org_list.append({"name": org.get("name"), "id": org.get("id"), "isEnabled": org.get("isEnabled")})
            return self._ok(self.mapper.orgs_to_canonical(org_list))
        return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # VDCs por Org
    # ------------------------
    def get_vdc_for_org_id(self, org_id: str) -> Response[List[vdc]]:
        """
        Obtiene VDCs de una organización: [{'name','id','allocationType'}, ...]
        """
        headers_context = dict(self._h())
        headers_context["X-VMWARE-VCLOUD-TENANT-CONTEXT"] = org_id
        r = self.session.get(f"{self.base}/cloudapi/1.0.0/vdcs?pageSize=1000", headers=headers_context)
        if r.status_code == 200:
            vdc_list: List[Dict[str, Any]] = []
            for vdc in r.json().get("values", []):
                vdc_list.append({"name": vdc.get("name"), "id": vdc.get("id"), "allocationType": vdc.get("allocationType")})
            return self._ok(self.mapper.vdc_to_canonical(vdc_list))
        return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # Crear Edge
    # ------------------------
    def create_edge(
        self,
        edge_name: str,
        vdc_id: str,
        edge_cluster_id: str,
        extern_netwrk_id: str,
        total_ips: int = 1,
        edge_desc: str = " ",
    ) -> Response[edgeGateway]:
        """
        Crea un Edge en un VDC específico.
        """
        # Obtener info de la red externa
        ext_net_resp = self.get_external_networks()
        if not ext_net_resp.ok or not ext_net_resp.data:
            return self._err(ext_net_resp.error or "No se pudo obtener redes externas")

        ext_net_info = next((n for n in ext_net_resp.data if n.get_id() == extern_netwrk_id), None)
        if not ext_net_info :
            return self._err("No se pudo obtener la información de la red externa o no tiene subredes configuradas.")

        # Tomamos la primera subred
        #first_subnet = ext_net_info["subnets"]["values"][0]
        ext_subnet_gateway = ext_net_info.get_gateway()
        ext_subnet_prefix = ext_net_info.get_prefix_length()
        payload = {
            "status": "ENABLED",
            "name": edge_name,
            "description": edge_desc,
            "orgVdc": {"id": vdc_id},
            "deploymentMode": "ACTIVE_STANDBY",
            "edgeClusterConfig": {
                "primaryEdgeCluster": {
                    "edgeClusterRef": {"id": edge_cluster_id}
                }
            },
            "edgeGatewayUplinks": [
                {
                    "uplinkId": extern_netwrk_id,
                    "connected": True,
                    "subnets": {
                        "values": [
                            {
                                "gateway": ext_subnet_gateway,
                                "prefixLength": ext_subnet_prefix,
                                "autoAllocateIpRanges": True,
                                "totalIpCount": total_ips,
                            }
                        ]
                    },
                }
            ],
        }

        r = self.session.post(f"{self.base}/cloudapi/1.0.0/edgeGateways", headers=self._h(), json=payload)
        if r.status_code == 202:
            task_url = r.headers.get("Location")
            if not task_url:
                return self._err("No se devolvió Location para seguimiento de tarea")
            res=self.wait_task_final(task_url)
            if not res.ok: 
                return res 
            new_edge=edgeGateway(id=res.data["owner_id"], name=edge_name, nsxvId="")
            return self._ok(new_edge)
        return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # Tareas (XML API)
    # ------------------------
    def get_task_status(self, url: str) -> Response[Dict[str, Optional[str]]]:
        """
        Dada la URL de una tarea, devuelve su estado.
        data = {"task_status": str, "owner_id": str|None, "details": str|None}
        """
        NS = "http://www.vmware.com/vcloud/v1.5"
        headers = {
            "Authorization": self.session.headers.get("Authorization", ""),
            "Accept": f"application/vnd.vmware.vcloud.task+xml;version={self.api_version}",
        }
        r = self.session.get(url, headers=headers)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            status = root.get("status")
            owner = root.find(f".//{{{NS}}}Owner")
            owner_id = owner.get("id") if owner is not None else None
            details_el = root.find(f".//{{{NS}}}Details")
            details = details_el.text if details_el is not None else None
            return self._ok({"task_status": status, "owner_id": owner_id, "details": details})
        return self._err(f"{r.status_code} {r.reason} {r.text}")

    def wait_task_final(self, url_task: str) -> Response[Dict[str, Optional[str]]]:
        """
        Espera hasta que la tarea se complete o falle (máx 180s).
        Devuelve el último estado consultado.
        """
        sleep_time = 0
        while sleep_time < 180:
            task = self.get_task_status(url_task)
            if not task.ok or not task.data:
                return self._err(task.error or "No se pudo obtener información de la tarea")

            status = (task.data.get("task_status") or "").lower()
            if status in ("success", "error", "canceled"):
                if status == "success":
                    return self._ok(task.data)
                else:
                    msg = f"Tarea {status}. {task.data.get('details') or ''}".strip()
                    return self._err(msg)

            sleep_time += 1
            time.sleep(1)

        return self._err("TIME_OUT: La tarea sobrepasó el tiempo máximo de espera; verifica en vCloud.")

    # ------------------------
    # Utilidad: imprimir XML (debug)
    # ------------------------
    def degub_xml_print(self, root: ET.Element) -> None:
        for children in root.iter():
            print(children.tag, children.text, "\n")

    # ------------------------
    # Crear regla de Firewall
    # ------------------------
    def create_firewall_rule(self, firewall_rules: fwRule, edge_id: str, isIcmp: bool = False) -> Response[Dict[str, Optional[str]]]:
        """
        Crea una regla de Firewall en un Edge.
        """
        adap_fw_rules = self.mapper.canonical_to_fw_rule(firewall_rules)
     

        for rule in adap_fw_rules:
          isIcmp= bool(rule["icmp"])
          payload_rule=rule["item"]
          print ("Procesando regla de FW:",rule["item"])
   
          if isIcmp:
             payload = {
            "name": payload_rule["name"],
            "active": payload_rule["active"],
            "logging": payload_rule["logging"],
            "direction": "IN_OUT",
            "ipProtocol": payload_rule.get("ipProtocol", "IPV4"),
            "actionValue": payload_rule["actionValue"],
            "sourceFirewallIpAddresses": payload_rule["sourceFirewallIpAddresses"],
            "destinationFirewallIpAddresses": payload_rule["destinationFirewallIpAddresses"],
            "applicationPortProfiles": payload_rule["applicationPortProfiles"],  # [{"id": "<ICMPV4_PROFILE_ID>"}]
            "relativePosition": payload_rule["relativePosition"],
        }
          else : 
           
           payload= {
           "name": payload_rule["name"],
           "active": payload_rule["active"],
           "logging": payload_rule["logging"],
           "direction": "IN_OUT",
           "ipProtocol": "IPV4",
           "actionValue": payload_rule.get("actionValue", "ALLOW"),
            "sourceFirewallIpAddresses": payload_rule["sourceFirewallIpAddresses"] ,
            "destinationFirewallIpAddresses": payload_rule["destinationFirewallIpAddresses"],
            "rawPortProtocols": payload_rule["rawPortProtocols"],
           "relativePosition":payload_rule["relativePosition"]
}     
           print("Creando FW rule en api, payload:", payload)
           r = self.session.post(
            f"{self.base}/cloudapi/2.0.0/edgeGateways/{edge_id}/firewall/rules",
            headers=self._h(),
            json=payload,
        )
           if r.status_code == 202:
            loc = r.headers.get("Location")
            if not loc:
                return self._err("No se devolvió Location para seguimiento de tarea")
            return self.wait_task_final(loc)
           return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # Crear SNAT
    # ------------------------
    def create_snat_rule(self, snat_rule: snatRule, edge_id: str) -> Response[Dict[str, Optional[str]]]:
        """
        Crea una regla de SNAT en un Edge.
        """
        snat_rule=self.mapper.canonical_to_snat([snat_rule])[0] 

        payload = {
            "name": snat_rule["name"],
            "type": "SNAT",
            "internalAddresses": snat_rule["internalAddresses"],
            "externalAddresses": snat_rule["externalAddresses"],
            "snatDestinationAddresses": snat_rule.get("snatDestinationAddresses"),
            "firewallMatch": "MATCH_INTERNAL_ADDRESS",
            "priority": snat_rule["priority"],
            "active": snat_rule["active"],
            "logging": snat_rule["logging"],
        }
        r = self.session.post(
            f"{self.base}/cloudapi/2.0.0/edgeGateways/{edge_id}/nat/rules",
            headers=self._h(),
            json=payload,
        )
        if r.status_code == 202:
            loc = r.headers.get("Location")
            if not loc:
                return self._err("No se devolvió link (Location) para seguimiento de tarea")
            return self.wait_task_final(loc)
        return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # Crear DNAT
    # ------------------------
    def create_dnat_rule(self, dnat_rule: dnatRule, edge_id: str, vdc_id:str, org_id:str) -> Response[Dict[str, Optional[str]]]:
        """
        Crea una regla de DNAT en un Edge.
        """
        #Convertir a formato API
        dnat_rule=self.mapper.canonical_to_dnat([dnat_rule])[0]      
        name=dnat_rule["name"]   
        name=name + datetime.now().strftime("_%Y%m%d%H%M%S")            
        is_one_one_nat=(dnat_rule["dnatExternalPort"] is None )
        transPort=dnat_rule["dnatInternalPort"]
        protocol=dnat_rule["protocol"].upper()

        print ("Porcesando regla ",dnat_rule["name"])
         #Si es Nat uno a uno, no hace falta crear perfil de puertos)
        print ("Valor de is_one_one", is_one_one_nat)
               
               #No es Nat uno a uno
                
        if not is_one_one_nat:

            if "protocol" in dnat_rule and str(dnat_rule["protocol"]).lower =="icmp":
                protocol="ICMPv4" 
            ap_ports=[{"name":name, "protocol":protocol, "destinationPorts":[transPort]}] 
               
            ap_profile={"name":name, 
                                "description": name, 
                                "org_id":org_id, 
                                "vdc_id": vdc_id, 
                               "applicationPorts":ap_ports } 
            create_app=self.create_vdc_application_port_prfile(aplication_profile=ap_profile, org_id=org_id, vdc_id=vdc_id)

            #Si no se puede crear el app profile devolver error 
            if not create_app.ok:
                return create_app
               


####################
        payload = {
            "name": dnat_rule["name"],
            "type": "DNAT",
            "externalAddresses": dnat_rule["externalAddresses"],
            "firewallMatch": "MATCH_EXTERNAL_ADDRESS",
            "internalAddresses": dnat_rule["internalAddresses"],
            "dnatExternalPort": dnat_rule["dnatExternalPort"],
            "applicationPortProfile": dnat_rule["applicationPortProfile"],
            "priority": dnat_rule["priority"],
            "active": dnat_rule["active"],
            "logging": dnat_rule["logging"],
        }
        r = self.session.post(
            f"{self.base}/cloudapi/2.0.0/edgeGateways/{edge_id}/nat/rules",
            headers=self._h(),
            json=payload,
        )
        if r.status_code == 202:
            loc = r.headers.get("Location")
            if not loc:
                return self._err("No se devolvió Location para seguimiento de tarea")
            return self.wait_task_final(loc)
        return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # IPs públicas del Edge
    # ------------------------
    def get_edge_public_ips(self, edge_id: str) -> Response[List[str]]:
        """
        Retorna las IPs públicas IPv4 de un Edge específico (primaryIp + rangos).
        """
        url = f"{self.base}/cloudapi/1.0.0/edgeGateways/{edge_id}?fields=edgeGatewayUplinks"
        resp = self.session.get(url, headers=self._h())
        if resp.status_code != 200:
            return self._err(f"{resp.status_code} {resp.reason} {resp.text}")

        data = resp.json()
        uplinks = data.get("edgeGatewayUplinks") or []
        ips_set: set[str] = set()

        for upl in uplinks:
            subnets = (upl.get("subnets") or {}).get("values") or []
            for sn in subnets:
                # si viene el flag enabled y está en False, salteamos
                if sn.get("enabled") is False:
                    continue

                # 1) primaryIp
                primary = sn.get("primaryIp")
                if primary:
                    try:
                        IPv4Address(primary)
                        ips_set.add(primary)
                    except ValueError:
                        pass

                # 2) Rangos explícitos (pueden venir como {"values":[...]} o lista)
                ranges = sn.get("ipRanges") or []
                if isinstance(ranges, dict):
                    ranges = ranges.get("values") or []

                for rng in ranges:
                    start = rng.get("startAddress") or rng.get("start")
                    end = rng.get("endAddress") or rng.get("end") or start
                    if not start:
                        continue
                    try:
                        s = int(IPv4Address(start))
                        e = int(IPv4Address(end))
                    except ValueError:
                        continue

                    if s > e:
                        s, e = e, s

                    for val in range(s, e + 1):
                        ips_set.add(str(IPv4Address(val)))

        # ordenar por valor numérico IPv4
        return self._ok(sorted(ips_set, key=lambda ip: int(IPv4Address(ip))))

    # ------------------------
    # Rutas estáticas
    # ------------------------
    def create_static_route(self, static_route: staticRoute, edge_id: str) -> Response[Dict[str, Optional[str]]]:
        """
        Crea una ruta estática en un Edge.
        """
        static_route=self.mapper.canonical_to_static_route([static_route])[0]
        payload = {
            "name": static_route["name"],
            "description": static_route["description"],
            "networkCidr": static_route["networkCidr"],
            "nextHops": static_route["nextHops"],
        }
        r = self.session.post(
            f"{self.base}/cloudapi/2.0.0/edgeGateways/{edge_id}/routing/staticRoutes",
            headers=self._h(),
            json=payload,
        )
        if r.status_code == 202:
            loc = r.headers.get("Location")
            if not loc:
                return self._err("No se devolvió Location para seguimiento de tarea")
            return self.wait_task_final(loc)
        return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # Crear red privada (Org VDC Network)
    # ------------------------
    def create_private_network(self, private_network: private_network, vdc_id:str, edge_id:str) -> Response[Dict[str, Optional[str]]]:
        """
        Crea una red interna (NAT_ROUTED) en un VDC.
        """
        private_network=self.mapper.canonical_to_priv_network([private_network])[0]

        payload = {
            "name": private_network["name"],
            "description": private_network["description"],
            "networkType": "NAT_ROUTED",
            "ownerRef": {"id": vdc_id},
            "connection": {
                "routerRef": {"id": edge_id},
                "connectionType": "INTERNAL",
                "connected": "true",
            },
            "subnets": {
                "values": [
                    {
                        "gateway": private_network["gateway"],
                        "prefixLength": private_network["prefixLength"],
                        "dnsServer1": private_network["dnsServer1"],
                        "dnsServer2": private_network["dnsServer2"],
                        "ipRanges": {"values": private_network["ipRanges"]},
                        "enabled": "true",
                    }
                ]
            },
            "strictIpMode": "false",
            "guestVlanTaggingAllowed": "false",
            "routeAdvertised": "false",
            "shared": False , #Por ahora lo creamos como no compartido
        }
        print ("Creando red privada en api, payload:", payload)
        r = self.session.post(f"{self.base}/cloudapi/1.0.0/orgVdcNetworks", headers=self._h(), json=payload)
        if r.status_code == 202:
            loc = r.headers.get("Location")
            if not loc:
                return self._err("No se devolvió Location para seguimiento de tarea")
            return self.wait_task_final(loc)
        return self._err(f"{r.status_code} {r.reason} {r.text}")

    # ------------------------
    # Application Port Profile (VDC)
    # ------------------------
    def create_vdc_application_port_prfile(
        self, aplication_profile: Dict[str, Any]
    , org_id:str, vdc_id:str) -> Response[Dict[str, Optional[str]]]:
        """
        Crea un Application Port Profile en un VDC.
        """
        payload = {
            "name": aplication_profile["name"],
            "description": aplication_profile["description"],
            "orgRef": {"id": aplication_profile["org_id"]},
            "scope": "TENANT",
            "contextEntityId": aplication_profile["vdc_id"],
            "applicationPorts": aplication_profile["applicationPorts"],
            "usableForNAT": True,
        }
        print ("creando application port ", payload )
        print ("\n")
        r = self.session.post(f"{self.base}/cloudapi/1.0.0/applicationPortProfiles", headers=self._h(), json=payload)
        if r.status_code == 202:
            loc = r.headers.get("Location")
            if not loc:
                return self._err("No se devolvió Location para seguimiento de tarea")
            return self.wait_task_final(loc)
        return self._err(f"{r.status_code} {r.reason} {r.text}")
    


    def get_application_port_prfile(self, name, scope)-> Response[Dict[str, Optional[str]]]:
        scopes_list=["SYSTEM", "TENANT"]
        if scope not in scopes_list: 
           return Response(ok=False, data="El parametro scope debe de ser SYSTEM o TENANT")
        index=1
        r=self.session.get(f"{self.base}/cloudapi/1.0.0/applicationPortProfiles?page={index}&pageSize=128&filterEncoded=true&filter=(name=={name};scope=={scope})&sortAsc=name", headers=self._h())
        if r.status_code == 200:
            data = r.json()
            return self._ok(data)
        return self._err(f"{r.status_code} {r.reason} {r.text}") 
        