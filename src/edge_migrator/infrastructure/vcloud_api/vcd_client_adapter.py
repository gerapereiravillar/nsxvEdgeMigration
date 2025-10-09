import os, requests
from xml.etree import ElementTree as ET
import re


class VcdApiAdapter:
    def __init__(self, base_url: str, user: str, org: str, password: str, api_version: str = "36.0"):
        self.base = base_url.rstrip("/")
        self.user = f"{user}@{org}"
        self.pw = password
        self.api_version = api_version
        self.session = requests.Session()
        self.session.verify = False
        self.nameSpace="http://www.vmware.com/vcloud/v1.5"

    def _h(self):
        return {"Accept": f"application/*+xml;version={self.api_version}"}

    def login(self) -> dict:
        """Iniciar session en la api. La session dura 30 min: 
        Args: Ninguno 
        Return: - Si ok {"success": token(str)}
                - Si error {"error": error(str)}"""
        
        r = self.session.post(f"{self.base}/api/sessions", headers=self._h(), auth=(self.user, self.pw))
        #Obtener el token api y agregarlo a la sesion
        if r.status_code==200:
           self.session.headers["x-vcloud-authorization"]=r.headers["x-vcloud-authorization"]
           return {"success": r.headers["x-vcloud-authorization"]}
        else: 
            return {"error": str(r.raise_for_status())}


   #Obtener lista de organizaciones
    def get_orgs_urn(self) -> dict:
      """Obtener lista de organizaciones. 
      Args: Ninguno
      Return: - Si ok {"success": org_list([{"name":str, "href":str, "id":str}])}
              - Si error {"error": error(str)}"""
      org_list = []
      r = self.session.get(f"{self.base}/api/org", headers=self._h())
      if r.status_code==200:
        root = ET.fromstring(r.content)
        # Buscar todos los elementos <Org> usando el nombre completo con namespace
        for org in root.findall(f'{{{self.nameSpace}}}Org'):
        # Extraemos los atributos que nos interesan
          id=org.get("href")
          id=id.split(sep="/")[-1]
          item = {
            'name': org.get('name'),
            'href': org.get('href'),
            "id":id
        }
          org_list.append(item)
       
        return {"success":org_list}
      else: 
         return {"error": f"{r.status_code} {r.reason} {r.text}"}
    
#Obtener una organizacion por nombre

    def get_orgs_by_name(self, org_name: str) -> list[dict]:
        """Obtener organizacion por nombre. 
        Args: org_name (str) Obligatorio
        Return: - Si ok {"success": org_list([{"name":str, "id":str}])}
                - Si error {"error": error(str)}"""
        org_list = []

        r = self.session.get(f"{self.base}/api/admin/orgs/query?filter=name=={org_name}*", headers=self._h())
        if r.status_code==200:
           root = ET.fromstring(r.content)
        # Buscar todos los elementos <Org> usando el nombre completo con namespace
           for org in root.findall(f'{{{self.nameSpace}}}OrgRecord'):
        # Extraemos los atributos que nos interesan
             id=org.get("href")
             id=id.split(sep="/")[-1]
             item = {
            'name': org.get('name'),
            "id":id
        }
             org_list.append(item)
       
           return {"success":org_list}
        else: 
           return {"error": f"{r.status_code} {r.reason} {r.text}"}
                   
        
# Obtener lista de VDC de organizacion
    def get_vdc_org_by_id(self, id)->list[dict]:
     """Obtener lista de VDC de una organizacion por id.
     Args: id (str) Obligatorio
     Return: - Si ok {"success": vdc_list([{"name":str, "id":str, "isEnabled":str, "vcName":str}])}
             - Si error {"error": error(str)}"""
     vdc_list=[]
     r=self.session.get(f"{self.base}/api/query?type=adminOrgVdc&filter=org==urn:vcloud:org:{id}", headers=self._h())
     if r.status_code==200:
       root=ET.fromstring(r.content)
       for child in root.findall(f'{{{self.nameSpace}}}AdminVdcRecord'):
         id=child.get("href").split("/")[-1]
         vdc={"name": child.get("name"), "id":id, "isEnabled":child.get("isEnabled") ,"vcName": child.get("vcName")}
         vdc_list.append(vdc)
       return  {"success":vdc_list}
     else:      
        return {"error":f"{r.status_code} {r.reason} {r.text}"}  
         
#Obtener lista de edges de un vdc 
    def vdc_list_edges(self, vdc_id: str) -> list[dict]:
        """Obtener lista de edges de un vdc.
        Args: vdc_id (str) Obligatorio
        Return: - Si ok {"success": edge_list([{"id":str, "name":str}])}
                - Si error {"error": error(str)}"""
        edge_list=[]
        r = self.session.get(f"{self.base}/api/admin/vdc/{vdc_id}/edgeGateways", headers=self._h()); 
        if r.status_code==200:

          root = ET.fromstring(r.content)
          for edge in root.findall(f"{{{self.nameSpace}}}EdgeGatewayRecord"):
            id=edge.get("href").split("/")[-1]
            item={"id":id, "name":edge.get("name")}
            edge_list.append(item)
          return {"success":edge_list}
        else :
         return {"error":f"{r.status_code} {r.reason} {r.text}"}  


#Obtener el xml de un edge
    def get_edge_xml(self, edge_id: str) -> dict:
        """Obtener el xml de un edge. 
        Args: edge_id (str) Obligatorio
        Return: - Si ok {"success": edge_xml(ET.Element)}
                - Si error {"error": error(str)}"""
        r = self.session.get(f"{self.base}/api/admin/edgeGateway/{edge_id}", headers=self._h())
        if r.status_code==200:
           return {"success":ET.fromstring(r.content)}
        else :
           return {"error":f"{r.status_code} {r.reason} {r.text}"}
        
#Obtener info general del edge
    def get_edge_general_desc(self, edge_xml: ET.Element)->dict:
         """Retorna el nombre y desc del edge
              Args: edge_xml (ET.Element) Obgligatorio
              Retruns: {"name":str, "id":str, "status": bool, "nsxvId":str}
              """
         edge_id=edge_xml.find(f'.//{{{self.nameSpace}}}gatewayId').text
         edge_desc={"name":edge_xml.get('name'), "id":edge_xml.get('id'), "status":edge_xml.get('status')
                    , "nsxvId":edge_id}

         return {"success":edge_desc }
        # return {"name":desc.get("name"), "id":desc.get("id"), "status":desc.get("status")}
         
     
    def _get_children_node_value(self,node: ET.Element, tag: str, NS:str):
            """Retorna el valor de un nodo hijo, o None si no existe o no tiene texto.
            Args: node (ET.Element) Obligatorio
                  tag (str) Obligatorio
                  NS (str) Obligatorio
            Returns: str|None
            """
            el = node.find(f'{{{NS}}}{tag}')
            return (el.text.strip() if el is not None and el.text else None)       


    def get_external_networks(self, edge_xml: ET.Element) -> list[dict]:
        """
        Retorna subredes externas del Edge (interfaces 'uplink').
        Args: edge_xml (ET.Element) Obligatorio
        Returns:  -Si ok:  ext_net_list (list[dict])
        ext_net_list = [{
           "id": str, "name": str, "gateway": str, "mask": str, "prefixLength": int|None,
            "primaryIp": str, "total_ips": int|None, "ipRanges": [{"start":str,"end":str},...],
            "rateLimit": bool|None, "inRateLimit": float|None, "outRateLimit": float|None
         }]
        """
        NS = self.nameSpace  # "http://www.vmware.com/vcloud/v1.5"
        ext_net_list = []

        # Buscar todas las interfaces en el edge (en cualquier profundidad)
        for gi in edge_xml.findall(f'.//{{{NS}}}GatewayInterface'):
            itype = self._get_children_node_value(node=gi, tag='InterfaceType',NS= NS)

            #Si no se encuentra uplink se salta esta iteracion del for
            if (itype or '').lower() != 'uplink':
                continue  # solo externas

            # referencia a la red externa (para id/name)
            netref = gi.find(f'{{{NS}}}Network')
            net_id = netref.get('id') if netref is not None else None
            name_el = gi.find(f'{{{NS}}}Name')
            name = name_el.text if name_el is not None else None

            subp = gi.find(f'{{{NS}}}SubnetParticipation')
            #Si no tiene ip asignada en la red se salta 
            if subp is None:
                continue

            gateway = self._get_children_node_value(subp, 'Gateway', NS)
            netmask = self._get_children_node_value(subp, 'Netmask', NS)
            prefix = self._get_children_node_value(subp, 'SubnetPrefixLength', NS)
            ipaddr  = self._get_children_node_value(subp, 'IpAddress', NS)
            total   = self._get_children_node_value(subp, 'TotalIpCount', NS)

            # rangos de IP
            ip_ranges = []
            for r in subp.findall(f'{{{NS}}}IpRanges/{{{NS}}}IpRange'):
                start = self._get_children_node_value(r, 'StartAddress', NS)
                end   = self._get_children_node_value(r, 'EndAddress', NS)
                ip_ranges.append({"start": start, "end": end})

            # rate limit está a nivel de la interfaz
            rate_limit = self._get_children_node_value(gi, 'ApplyRateLimit', NS)
            in_rl  = self._get_children_node_value(gi, 'InRateLimit', NS)
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

        return {"success":ext_net_list}
    

    def _netmask_to_prefix_length(self, netmask: str) -> str:
        """Convert netmask to prefix length (e.g., 255.255.255.0 -> 24)"""
        try:
            # Convertir la máscara de red a entero binario y contar los bits en 1
            binary_str = ''
            for octet in netmask.split('.'):
                binary_str += bin(int(octet))[2:].zfill(8)
            return str(binary_str.count('1'))
        except:
            return ''  

                   
#Obtener redes internas
    def get_id_internal_networks(self, edge_xml: ET.Element) -> list[str]:
        """
        Retorna los IDs (UUID) de las Org VDC Networks conectadas como 'internal' al Edge.
        Args: edge_xml (ET.Element) Obligatorio
        Returns: list[str] con los IDs (UUID) de las redes internas conectadas al Edge.
        """
        NS = self.nameSpace  # "http://www.vmware.com/vcloud/v1.5"
        ids: list[str] = []

        for gi in edge_xml.findall(f'.//{{{NS}}}GatewayInterface'):
            itype = (self._get_children_node_value(gi, 'InterfaceType', NS) or '').lower()
            if itype != 'internal':
                continue

            netref = gi.find(f'{{{NS}}}Network')
            if netref is None:
                continue

            # 1) intentar con el atributo 'id' (urn:vcloud:network:<uuid>)
            net_id = netref.get('id')
            if net_id:
                if net_id.startswith('urn:vcloud:network:'):
                    net_id = net_id.split(':')[-1]  # -> <uuid>
            else:
                # 2) fallback: parsear el UUID del href .../api/network/<uuid>
                href = netref.get('href')
                if href:
                    net_id = href.rstrip('/').rsplit('/', 1)[-1]
                else:
                    net_id = None

            if net_id:
                ids.append(net_id)

        return {"success":ids}
    



      #Retornar info completa de redes por id 

    def get_networks_info(self, net_id_list: list[str]) -> list[dict]:
        """
        Retorna la info de una lista de redes internas (OrgVdcNetwork) desde /api/network/{id}.
        Formato por red:
        -Si ok:  {"success":net_info(dict)}
        - Si error {"error":error(str)}
           net_info={
            "name": str, "description": str, 
            "shared": bool,
            "gateway": str|None,
            "prefixLength": int|None,
            "dnsServer1": str|None, "dnsServer2": str|None,
            "ipRanges": [{"startAddress": str|None, "endAddress": str|None}, ...]
            "FenceMode":str(tipo de red, aislada o enrutada)
          }
        """
        NS = self.nameSpace  # "http://www.vmware.com/vcloud/v1.5"
        gc = self.get_child if hasattr(self, "get_child") else self._get_children_node_value

        out = []

        for net_id in net_id_list:
            url = f"{self.base}/api/network/{net_id}"
            r = self.session.get(url, headers=self._h())
            if not r.ok:
               # si querés loguear el error:
               out.append({"error": f"{r.status_code} {r.reason} {r.text}"})
               continue

            root = ET.fromstring(r.content)  # <OrgVdcNetwork ...>

            item = {
                "name": root.get("name") or "",
                "description": gc(root, "Description", NS) or "",
                "shared": (gc(root, "IsShared", NS) or "").lower() == "true",
                "gateway": None,
                "prefixLength": None,
                "dnsServer1": None,
                "dnsServer2": None,
                "ipRanges": []
            }

        # IpScope principal
            ipscope = root.find(f'{{{NS}}}Configuration/{{{NS}}}IpScopes/{{{NS}}}IpScope')
            if ipscope is not None:
                item["gateway"]    = gc(ipscope, "Gateway", NS)
                pref               = gc(ipscope, "SubnetPrefixLength", NS)   # viene en el XML
                item["prefixLength"] = int(pref) if pref and pref.isdigit() else None
                item["dnsServer1"] = gc(ipscope, "Dns1", NS)
                item["dnsServer2"] = gc(ipscope, "Dns2", NS)

                for rng in ipscope.findall(f'{{{NS}}}IpRanges/{{{NS}}}IpRange'):
                    start = gc(rng, "StartAddress", NS)
                    end   = gc(rng, "EndAddress", NS)
                    item["ipRanges"].append({
                       "startAddress": start,
                       "endAddress": end
                    })
            element={"success":item}
            out.append(element)

        return out 
    




    #Obtener las ips de una vm 
    def get_vm_ips(self, vm_id: str)->list[str]:
        """Dado un id de una vm, retorna una lista de ips de la vm
         Args: vm_id (str) Obligatorio
        Returns: -si ok{"success":ip_list ([str])} 
                  - si error {"error":str}
        """
        ip_list = []
        r = self.session.get(f"{self.base}/api/vApp/vm-{vm_id}/networkConnectionSection", headers=self._h())
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for connection in root.findall(f'{{{self.nameSpace}}}NetworkConnection'):
                ip_address = connection.find(f'{{{self.nameSpace}}}IpAddress')
                if ip_address is not None and ip_address.text:
                    ip_list.append(ip_address.text)
        
            return {"success":ip_list }
        else: 
            return {"error", f"{r.status_code} {r.reason} {r.text}" }
        




    def _get_firewall_rules_aux_vnic_in_list(self, vnics_list:list[dict], vnic_name :str)->dict:
        """Retorna true si la vnic esta en la lista de vnic y tiene una subred asignada
            Args: vnics_list ([{"vnic-index":"net_CIDR_FORMAT"}])
                  vnic_name (str) formato vnic-index Obligatoro
            Returns: - Si esta {"true": "network_CIDR_FORMAT"}
                     - Si no esta {"false":""} """
        for vnic in vnics_list:
            if vnic_name in vnic:
                return {"true":vnic[vnic_name]}
                     
        return {"false":""}


    #Ontener reglas de firewall
    def get_firewall_rules(self, edge_id: str, internal_net :list [dict], vnic_newt_list: list[dict],ext_net_list:list[str])->list[dict]:
        """Obtener reglas de firewall de un edge traducidas solo a redes. 
            Args: edge_id (str) Obgligatorio
            Retruns: 
            -si ok {"success":firewall_rules_list:[{"name":str, "ruleTag":str, "enabled":str, "loggingEnabled":str, "action" :str,
            "source_ips":[CDIR1, CDIR2..], "dest_ips":[CDIR1, CDIR2..], "services":[dict], "not_maped_source":[str], "not_maped_destination":[str]"}]
             Si hay algo que no se pudo mapear del origen o destino estara en not_maped_source o not_maped_destination

            -si error {"error":error(str)} """
        respons=self.session.get(f"{self.base}/network/edges/{edge_id}/firewall/config", headers=self._h()) 
        if respons.status_code ==200: 
           root= ET.fromstring(respons.content)           
           firewall_rules_list=[]   
           for rule in root.findall('.//firewallRule'):
               #Obtener info general 
               item={"ruleTag":rule.find("ruleTag").text, "name":rule.find("name").text,
                      "enabled":rule.find("enabled").text
                    ,"loggingEnabled":rule.find("loggingEnabled").text, "action":rule.find("action").text}
               #Obtener los source destintation y los (puertos, protocolos asociados ) 

               source=rule.find("source")
               destination=rule.find("destination")
               application=rule.find("application")
               source_list=[]
               destination_list=[]
               application_list=[]
               not_maping_source_rules=[]
               not_maping_destination_rules=[]
               #Obtenemos los source, todo se tranforma a subredes formato CIDR 
               if source != None: 
                   source_list=self._get_fir_rules_aux_get_dest_or_sorce(source, internal_net, vnic_newt_list, ext_net_list)
                   if "not_maped" in source_list:
                       not_maping_source_rules.extend(source_list["not_maped"])
               #Obtenemos los destination, todo se tranforma a subredes formato CIDR    
               if destination != None:     
                   destination_list=self._get_fir_rules_aux_get_dest_or_sorce(destination, internal_net, vnic_newt_list,ext_net_list)
                   if "not_maped" in destination_list:
                       not_maping_destination_rules.extend(destination_list["not_maped"])
               if application != None:
                   application_list  =self._get_firewall_rules_aux_get_ports_and_protocols(application)
               if "rules" in source_list and len(source_list["rules"]):
                   item["source_ips"]=source_list["rules"]
               else:
                   item["source_ips"]=[]
               if "rules" in destination_list and len(destination_list["rules"]):
                   item["dest_ips"]=destination_list["rules"]
               else:
                   item["dest_ips"]=[]
               item["services"]=application_list
               item["not_maped_source"]=not_maping_source_rules
               item["not_maped_destination"]=not_maping_destination_rules
               firewall_rules_list.append(item)
           return {"success":firewall_rules_list}
        else: 
            return {"error":f"{respons.status_code } {respons.reason}"}



    def _get_fir_rules_aux_get_dest_or_sorce(self, payload : ET.Element, internal_net :list [dict], vnic_newt_list: list[dict], ext_net_list:list)->dict:
               """Dado un source o un destination devuelve las ips traducidas.
        Args:   -peyload(ET.element) formato (ningun campo es obligatorio) 
                <ipAddress>IP/MASK</ipAddress>
                <vnicGroupId>vnic-id</vnicGroupId>
                <groupingObjectId>urn:vcloud:network:aab0bf10-fd0c-40b9-a658-07c3d67ee2e1</groupingObjectId>
                <groupingObjectId>urn:vcloud:vm:5dd81c6c-f4fc-4a18-a33e-e2633604cf77</groupingObjectId>
                -internal_net (list[dict]) Obligatorio
                -vnic_newt_list (list[dict]) Obligatorio 
        Return:    respons{"rules":[list], "not_maped":{"source":[], "destination":[]}}

             """
               rules_list=[]
               not_maping_rules=[]
               #Obtenemos los source, todo se tranforma a subredes formato CIDR 
               if payload != None: 
                   for item in payload.iter():
                       if item.tag=="ipAddress":
                           rules_list.append(item.text) 
                               #El source son todas las  interfaz de tipo internal 
                       elif item.tag=="vnicGroupId" and re.search("internal",item.text)!=None :
                           #Obtengo las ips de las redes internas 
                           for net in internal_net:
                               gateway=net["gateway"]
                               prefix=net["prefixLength"]
                               subnet=f"{gateway}/{prefix}"
                               rules_list.append(subnet)
                               #si vnic, Obtengo la subred donde esta conectada la vnic 
                       elif item.tag=="vnicGroupId" and re.search("vnic",item.text)!=None :
                            #Verifico que la vnic este en la lista de vnic
                            vnic_result=self._get_firewall_rules_aux_vnic_in_list(vnic_newt_list,item.text)
                            if "true" in vnic_result:
                               rules_list.append(vnic_result["true"])
                            else:    
                               not_maped_dict={item.tag:item.text}
                               not_maping_rules.append(not_maped_dict)
                               #Si maquina virtual, obtengo las ips de la vm
                       elif item.tag=="groupingObjectId" and re.search("urn:vcloud:vm:",item.text)!=None :
                           vm_id=item.text.split(":")[-1]
                           ips=self.get_vm_ips(vm_id)
                           if "success" in ips and len(ips):
                               rules_list.extend(ips["success"])
                           else: 
                               #Si no pude mapear ips la agrego a reglas no mapeadas 
                               error=ips["error"]
                               not_maped_dict={item.tag:item.text}
                               not_maping_rules.append(not_maped_dict)
                               #Si es una subred 
                       elif item.tag=="groupingObjectId" and re.search("urn:vcloud:network",item.text)!=None:
                           net_ips=self.get_networks_info([item.text.split(":")[-1]])
                           if "success" in net_ips[0] and len(net_ips):
                               gateway=net_ips[0]["success"]["gateway"]
                               prefix=net_ips[0]["success"]["prefixLength"]
                               subnet=f"{gateway}/{prefix}"
                               rules_list.append(subnet)
                           else:
                               error=net_ips[0]["error"]
                               #Si no pude mapear ips la agrego a reglas no mapeadas 
                               not_maped_dict={item.tag:item.text}
                               not_maping_rules.append(not_maped_dict)
                               #Si son las interfaces externas del edge(uplinks) 
                       elif item.tag=="vnicGroupId" and (re.search("external",item.text)!=None or re.search("vse",item.text)!=None):
                                  if len(ext_net_list):
                                      for ip in ext_net_list:
                                          rules_list.append(ip)
                                  else: 
                                       not_maped_dict={item.tag:item.text}
                                       not_maping_rules.append(not_maped_dict)
                                          
                       elif item.tag=="source" or item.tag=="destination" or item.tag=="exclude" :
                              #No hacemos nada si estamos en las etiquetas padre, o si encontramos exclude,
                              # que no es relevante, ya 
                              #que no se pude config en vcloud de origen 
                              pass
                       else: 
                           #Si no es ninhuna de las anteriores, no puedo mapear y agrego a lista
                           not_maped_dict={item.tag:item.text}
                           not_maping_rules.append(not_maped_dict)
                   return {"rules":rules_list, "not_maped":not_maping_rules}

                            

    def _get_firewall_rules_aux_get_ports_and_protocols(self, payload : ET.Element)->list[dict]: 
            """Retorna la lista de servicios. 
            Args: payload(ET.element) en el sig formato Ej:
                <application>
                <service>
                    <protocol>udp</protocol>
                    <port>any</port>
                    <sourcePort>any</sourcePort>
                </service>
                <service>
                    <protocol>tcp</protocol>
                    <port>10-12</port>
                    <sourcePort>2025-2026</sourcePort>
                </service>
                <service>
                    <protocol>icmp</protocol>
                    <icmpType>any</icmpType>
                </service>
            Return: apllication_list (list[dict])) 
                  dict={"protocol":str|None, "port":str|None, "sourcePort":str|None, "icmpType":str|None}
               """

            apllication_list=[]
            if payload !=None: 
                
                for serv in payload.iter():
                    if serv.tag!="service":
                        continue

                    item={}
                    protocol=serv.find("protocol")
                    if (protocol is not None) and protocol.text:
                        item["protocol"]=protocol.text

                    if  protocol is not None and protocol.text=="icmp":
                            # No hay puertos para ICMP, solo tipo ICMP
                        icmp_type = serv.find("icmpType")
                        if icmp_type is not None and icmp_type.text:
                            item["icmpType"] = icmp_type.text
                                
                    port=serv.find("port")
                    source_port=serv.find("sourcePort")

                    if port is not None and port.text:
                        item["port"]=port.text
                    if source_port is not None and source_port.text:
                        item["sourcePort"]=source_port.text
                    apllication_list.append(item)

            return apllication_list

    #Obtener reglas estaticas.                     
    def get_static_routes(self, edge_xml: ET.Element)->list[dict]:
        """Retorna una lista de reglas de ruteo estaticas. 
        Args: edge_xml (ET.element) Obligatorio
        Returns: static_rules_list(list[dict])
        Por cada regla: 
         {"Name":str|None, 
         "Network":str|None, 
         "NextHopIp":str|None 
           }"""
        static_routes=[] 
        for rule in edge_xml.findall(f'.//{{{self.nameSpace}}}StaticRoute'):
            Name=rule.find(f'{{{self.nameSpace}}}Name')
            Network=rule.find(f'{{{self.nameSpace}}}Network')
            NextHopIp=rule.find(f'{{{self.nameSpace}}}NextHopIp')
            item={"Name":Name.text if Name is not None else None,
                  "Network":Network.text if Network is not None else None,
                  "NextHopIp":NextHopIp.text if NextHopIp is not None else None}
            static_routes.append(item)
        return static_routes
    



                       
                       






               
            
