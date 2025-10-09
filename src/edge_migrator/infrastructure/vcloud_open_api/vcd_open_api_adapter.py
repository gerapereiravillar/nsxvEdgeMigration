import os, requests, json
from xml.etree import ElementTree as ET
import time
from ipaddress import IPv4Address


class vCloudOpenApiAdap:
    def __init__(self,base_url: str, user: str, org: str, password: str, api_version: str = "39.1"):
        self.base=base_url
        self.user=f"{user}@{org}"
        self.password=password
        self.api_version=api_version
        self.session=requests.session()

    
    #headers de la consulta
    def _h(self):
        return {"Accept": f"application/json;version={self.api_version}"}

    #iniciar sesion 
    def login (self)->dict:
       """Inicia sesion en vcloud y guarda el token en la session
       Return: -si exito {"success":""}
               -si error {"error":error(str)}"""
       r=self.session.post(f"{self.base}/cloudapi/1.0.0/sessions/provider", headers=self._h(), auth=(self.user, self.password))
       if r.status_code ==200:
           self.session.headers["Authorization"]=f"Bearer {r.headers['X-VMWARE-VCLOUD-ACCESS-TOKEN']}"
           return {"success":""}
       elif r.status_code==401:
           return {"error": "Error de credenciales"}
       else:
            return {"error": f"{r.status_code} {r.reason}"}
    
#Obtener los cluster de edge
    def get_edge_cluster(self)-> dict[list[dict]]:
        """Obtiene los cluster de edge
        Return: -si exito {"success":list[{"name":str, "id":str}]}
                -si error {"error":error(str)}"""
        r=self.session.get(f"{self.base}/cloudapi/1.0.0/edgeClusters", headers=self._h())
        edge_cluster_list=[]
        if r.status_code==200:
           cluster_json_list=r.json()["values"]
           for cluster in cluster_json_list:
              edge_cluster_list.append({"name":cluster["name"], "id":cluster["id"]})

           return {"success":edge_cluster_list}
        else:
            return {"error": f"{r.status_code} {r.reason}"}
        
    
#Obetner las redes externas
    def get_edge_external_network(self)-> dict[list[dict]] :
        """Obtiene las redes externas
        Return: -si exito {"success":list[{"name":str, "id":str, "subnets":dict, "ipsFree":int}]}
                -si error {"error":error(str)}"""
        r=self.session.get(f"{self.base}/cloudapi/1.0.0/externalNetworks?pageSize=1000", headers=self._h())
        network_list=[]
        if r.status_code==200:
           network_json_list=r.json()["values"]
           for network in network_json_list:
               item={"name":network["name"], "id":network["id"], "subnets":network["subnets"], 
                     "ipsFree":int(network["totalIpCount"] if network["totalIpCount"] is not None else 0) - int(network["usedIpCount"] if network["usedIpCount"] is not None else 0)}
               network_list.append(item)
           return {"success":network_list}
        else:
            return {"error": f"{r.status_code} {r.reason}"}
    
    

#Obtener Organizaciones
    def get_orgs(self)-> dict[list[dict]]:
        """Obtiene las organizaciones
        Return: -si exito {"success":list[{"name":str, "id":str, "isEnabled":bool}]}
                -si error {"error":error(str)}"""
        org_list=[]
        r=self.session.get(f"{self.base}/cloudapi/1.0.0/orgs?pageSize=1000", headers=self._h())
        if r.status_code==200:
           orgs=r.json()["values"]
           for org in orgs:
               org_list.append({"name":org["name"], "id":org["id"], "isEnabled":org["isEnabled"]})
           return {"success":org_list}
        else:
            return {"error": f"{r.status_code} {r.reason}"}
    
    
#Obtener organizacin por nombre 
    def get_orgs_by_name(self, org_name)->dict:
        """Obtiene las organizaciones por nombre (puede devolver mas de una si el nombre es comun)
        Args: org_name (str) obligatorio    
        Return: -si exito {"success":list[{"name":str, "id":str, "isEnabled":bool}]}
                -si error {"error":error(str)}"""
        org_list=[]
        r=self.session.get(f"{self.base}/cloudapi/1.0.0/orgs?pageSize=1000&filter=name=={org_name}*", headers=self._h())
        if r.status_code==200:
           orgs=r.json()["values"]
           for org in orgs:
               org_list.append({"name":org["name"], "id":org["id"], "isEnabled":org["isEnabled"]})
           
           return {"success":org_list}
        else:
            return {"error": f"{r.status_code} {r.reason}"}
            


#Obtener lista de vdc para una org  por id 
    def get_vdc_for_org_id(self, org_id: str )->dict:
        """Obtiene los VDC de una organizacion por id
        Args: org_id (str) obligatorio
        Return: -si exito {"success":list[{"name":str, "id":str, "allocationType":str}]}
                -si error {"error":error(str)}"""   
        vdc_list=[]
        headers_context=self._h()
        headers_context["X-VMWARE-VCLOUD-TENANT-CONTEXT"]=org_id
        r=self.session.get(f"{self.base}/cloudapi/1.0.0/vdcs?pageSize=1000", headers=headers_context)
        if r.status_code==200:
           vdcs=r.json()["values"]
           for vdc in vdcs:
               vdc_list.append({"name":vdc["name"], "id":vdc["id"], "allocationType":vdc["allocationType"]})
           return {"success":vdc_list}
        else:
            return {"error": f"{r.status_code} {r.reason}"}

            

    def create_edge(self, edge_name, vdc_id, edge_cluster_id, extern_netwrk_id, total_ips=1,edge_desc=" ")->dict:
        """Crea un edge en un vdc especifico
        Args: edge_name (str) obligatorio
              vdc_id (str) obligatorio
              edge_cluster_id (str) obligatorio 
              extern_netwrk_id (str) obligatorio
              total_ips (int) opcional, por defecto 1
              edge_desc (str) opcional, por defecto 
              Return: -si exito {"success":""}
                -si error {"error":error(str)}  
                """
        # Obtener la información de la red externa para extraer el gateway y el prefijo
        ext_net_info = None
        get_ext_net_result = self.get_edge_external_network()
        if "success" in get_ext_net_result:
            for net in get_ext_net_result["success"]:
                if net["id"] == extern_netwrk_id:
                    ext_net_info = net
                    break
        
        if not ext_net_info or not ext_net_info["subnets"]["values"]:
            return {"error": "No se pudo obtener la información de la red externa o no tiene subredes configuradas."}

        # Asumiendo que solo hay una subred o que queremos usar la primera
        ext_subnet_gateway = ext_net_info["subnets"]["values"][0]["gateway"]
        ext_subnet_prefix = ext_net_info["subnets"]["values"][0]["prefixLength"]
        payload = {
          "status": "ENABLED",
          "name": edge_name,
          "description": edge_desc,
    "orgVdc": {
        "id": vdc_id
    },
    "deploymentMode": "ACTIVE_STANDBY"
    ,
    "edgeClusterConfig": {
        "primaryEdgeCluster": {
            "edgeClusterRef": {
                "id": edge_cluster_id
            }
        }
    },
    "edgeGatewayUplinks": [
        {
            "uplinkId": extern_netwrk_id,
            "connected": True,
            "subnets": {
                "values": [
                    {
                        "gateway": ext_subnet_gateway,  # Gateway de la subred externa
                        "prefixLength": ext_subnet_prefix,         # Máscara de red
                        "autoAllocateIpRanges": True,
                         "totalIpCount": total_ips
                    }
                ]
            }
        }
    ]
}


        r = self.session.post(
        f"{self.base}/cloudapi/1.0.0/edgeGateways",  
        headers=self._h(),
        json=payload
    )
        
        if r.status_code == 202:
           task_url=r.headers["Location"]
           
           return self.wait_task_final(task_url)
                   
        else:
          return {"error": f"{r.status_code} {r.reason} {r.text}"}
        
#Obtener estado de tarea, solo se puede hacer con api xml, no con openApi
    def get_task_status(self, url):
        """Dada la url de una tarea, consulta el estado de la misma 
           Args: url (str) https://ejemplo.com/api/tasks/{id}
           return: -si exito al obtener la tarea {"success":{"task_status":"object_id" |None,"details":str|None}}
                          
                   -si error {"error":connection_error(str)}
                   
           """
        NS="http://www.vmware.com/vcloud/v1.5"
       #Fabircamos nuestra header, no podemos usar las que estan ya que son openapi. 
        headers={"Authorization":self.session.headers["Authorization"]}
        headers["Accept"]=f"application/vnd.vmware.vcloud.task+xml;version={self.api_version}"
        r = self.session.get(url, headers=headers)
        if r.status_code == 200:
            root=ET.fromstring(r.content)
            status_tag=root
            id_tag=root.find(f".//{{{NS}}}Owner")
            id_tag=id_tag.get("id") if id_tag is not None else None 
            status=status_tag.get("status") if status_tag is not None else None 
            details_tag=root.find(f".//{{{NS}}}Details")
            details=details_tag.text if details_tag is not None else None 
            return {"success":{ status:id_tag, "details":details} }
        else: 
            return {"error":f"{r.status_code} {r.reason} {r.text}"}
#Espera hasta que la tarea se complete, tiempo maximo 3 min 


    def wait_task_final(self, url_task)->dict:
        """Hace seguimiento de una tarea hasta que se complete o falle. 
        Args: url_task (str)
        Return: {"task_result":"detail"}"""
        sleep_time=0
        exit=False 
        while sleep_time<180:
           task_status=self.get_task_status(url_task)
           
           if "success" in task_status:
               if "success" in task_status["success"]:
                   return task_status["success"]
                   
               elif "error" in task_status["success"]:
                   return task_status["success"]
               #Esperamos 
               else :
                   sleep_time=sleep_time +1
                   time.sleep(1)
           else :
                  return {"error":f"No se pudo obtener info de tarea {task_status}"  }
           
        return {"TIME_OUT": "La tarea a sobrepasado el tiempo maximo de espera, verifica en vcloud"}
    
    #imprime el xml en la salida por defecto 
    def degub_xml_print (self,root:ET.Element):
        for children in root.iter() : 
            print (children.tag, children.text , "\n")
              
#Crear reglas de firewall 
    def create_firewall_rule(self, firewall_rules:dict, edge_id:str, isIcmp=False):
       
       """Crea una regla de firewall en un edge especifico
        Args: edge_id (str) (obligatorio) Sin URN, ej  aab0bf10-fd0c-40b9-a658-07c3d67ee2e1
              firewall_rules (dict)
              campos:
              Todos los campos que adminten valor None, None=Any 
              {"name":str,  "active":bool, "logging":bool, "actionValue":"ALLOW"|"DENY" (str),
               "sourceFirewallIpAddresses":list[CDIR(str)]|None, "destinationFirewallIpAddresses":list[CDIR(str)|None],
               "rawPortProtocols":list[(dict)]|None, "relativePosition":dict] }
                rawPortProtocols campos
                               [
                       { "layer4Item": { "protocol": "UDP"|None, "sourcePorts": ["CDIR"]|None, "destinationPorts": ["ports"]|None } },
                       { "layer4Item": { "protocol": "TCP"|None, "sourcePorts": ["CDIR"]|None, "destinationPorts": ["22"]|None } }
                         ]                
                relativePosition campos:
                {"adjacentRuleId":str, "rulePosition":"BEFORE"|"AFTER"|TOP|BUTTOM(str), 
                "adjacentRuleId":"<id_de_regla_existente>"}
                """
       if isIcmp:
           payload={
              "name": firewall_rules["name"],
              "active": firewall_rules["active"],
              "logging": firewall_rules["logging"],
               "direction": "IN_OUT",
              "ipProtocol": "IPV4",
             "actionValue": firewall_rules["actionValue"],
             "sourceFirewallIpAddresses": firewall_rules["sourceFirewallIpAddresses"],
           "destinationFirewallIpAddresses":firewall_rules["destinationFirewallIpAddresses"],
           "icmpType": "IPV4_ANY",
           "relativePosition": firewall_rules["relativePosition"]
}
       else : 
           
           payload= {
           "name": firewall_rules["name"],
           "active": firewall_rules["active"],
           "logging": firewall_rules["logging"],
           "direction": "IN_OUT",
           "ipProtocol": "IPV4",
           "actionValue": firewall_rules.get("actionValue", "ALLOW"),
            "sourceFirewallIpAddresses": firewall_rules["sourceFirewallIpAddresses"] ,
            "destinationFirewallIpAddresses": firewall_rules["destinationFirewallIpAddresses"],
            "rawPortProtocols": firewall_rules["rawPortProtocols"],
           "relativePosition":firewall_rules["relativePosition"]
}      

       
       r=self.session.post(f"{self.base}/cloudapi/2.0.0/edgeGateways/{edge_id}/firewall/rules", headers=self._h(), json=payload)
       if r.status_code==202:
           return self.wait_task_final(r.headers["Location"])
       else: 
          return   {"error":f"{r.status_code} {r.reason} {r.text}"}
    
    
    def create_snat_rule (self, nat_rules:dict, edge_id:str)->dict:
        """Crear una regla de SNAT en un edge especifico
        Args:
        edge_id str (obgligatorio )
        nat_rules(dict)
         campos: 
          {"name":str, "internalAddresses":CDIR(str), "externalAddresses":CDIR(str),
          "snatDestinationAddresses":CDIR(str)|None,
          "priority":int, "active":bool, "logging":bool} """
        payload={
        "name": nat_rules["name"],
        "type": "SNAT",
        "internalAddresses": nat_rules["internalAddresses"],
        "externalAddresses": nat_rules["externalAddresses"],
       "snatDestinationAddresses": nat_rules["snatDestinationAddresses"],
       "firewallMatch": "MATCH_INTERNAL_ADDRESS",
       "priority": nat_rules["priority"],
       "active": nat_rules["active"],
       "logging": nat_rules["logging"]
      }
        r=self.session.post(f"{self.base}/cloudapi/2.0.0/edgeGateways/{edge_id}/nat/rules", headers=self._h(), json=payload)
        if r.status_code ==202:
            return self.wait_task_final(r.headers["Location"])
        else:
            return {"error":f"{r.status_code} {r.reason} {r.text}"}
        
    
    def create_dnat_rule (self, nat_rules, edge_id:str)->dict:
        """Crear una regla de DNAT en un edge especifico
        Args: nat_rules(dict) (obligatorio)
         campos: 
            {"name":str,"externalAddresses":CDIR (str), 
            "internalAddresses":CDIR (str), "dnatExternalPort":int,
            "priority":int, "active":bool, "logging":bool, 
            "applicationPortProfile":dict} 
            applicationPortProfile campos:
               { "id": "urn:vcloud:applicationPortProfile:XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" } 
                
                 
            edge_id str (obgligatorio ) """
        payload=   {
      "name": nat_rules["name"],
      "type": "DNAT",
      "externalAddresses": nat_rules["externalAddresses"],
      "firewallMatch": "MATCH_EXTERNAL_ADDRESS", 
      "internalAddresses": nat_rules["internalAddresses"],
      "dnatExternalPort": nat_rules["dnatExternalPort"],
      "applicationPortProfile": nat_rules["applicationPortProfile"],
      "priority": nat_rules["priority"],
      "active": nat_rules["active"],
      "logging": nat_rules["logging"]
     }    
        
        r=self.session.post(f"{self.base}/cloudapi/2.0.0/edgeGateways/{edge_id}/nat/rules", headers=self._h(), json=payload)
        if r.status_code ==202:
            return self.wait_task_final(r.headers["Location"])
        else:
            return {"error":f"{r.status_code} {r.reason} {r.text}"}

 
#Obtener ips de la redes externas conectadas. 
    def get_edge_public_ips(self, edge_id: str) -> list[str]:
        """Retorna las IPs públicas IPv4 de un Edge específico (primaryIp + rangos)."""
        url = f"{self.base}/cloudapi/1.0.0/edgeGateways/{edge_id}?fields=edgeGatewayUplinks"
        resp = self.session.get(url, headers=self._h())
        if resp.status_code != 200:
            return {"error": f"{resp.status_code} {resp.reason}"}  

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
                    end   = rng.get("endAddress")   or rng.get("end") or start
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
        return {"success":sorted(ips_set, key=lambda ip: int(IPv4Address(ip)))}



    
#Crear rutas estaticas    
    def create_static_route(self, static_route:dict, edge_id:str)->dict:
        """Crea una ruta estatica en un edge especifico: 
        Args: 
        static_route (dict) Obligatorio 
        edge_id (str) Obligatorio 
        
        static_route campos:
         {"name":str, "description":str, "networkCidr":str, "nextHops":list[dict]}
        
        nexHops campos: 
           {"ipAddress":str, "administrativeDistance":str} """
        

        payload={
              "name":static_route["name"], 
              "description":static_route["description"], 
              "networkCidr":static_route["networkCidr"], 
              "nextHops":static_route["nextHops"]
        }

        r=self.session.post(f"{self.base}/cloudapi/2.0.0/edgeGateways/{edge_id}/routing/staticRoutes", headers=self._h(), json=payload)
        if r.status_code==202:
            return self.wait_task_final(r.headers["Location"])  
        else : 
            return {"error":f"{r.status_code} {r.reason} {r.text}"}
    
#Crear las redes privadas
    def create_private_network(self, private_network:dict)->dict:
        """crea una red interna en un VDC. 
        Args:private_networks (dict)
         campos:
               {"name":str, "description":str, 
               "vdcId":str, "edge_id":str, 
               "gateway":str, "prefixLength":int,
               "dnsServer1":str, "dnsServer2":str,
               "enable":bool, "shared":bool,
               "ipRanges":ip_ranges_list(list[dict])
               }                
               ip_ranges 
        campos
               {"startAddress":str, "endAddress":str"}
               
        Return: -si ok {"success":net_id(str)}
                -si error {"error":error(str)}
        """
        payload={
           "name": private_network["name"],
           "description": private_network["description"],
           "networkType": "NAT_ROUTED",
           "ownerRef": { "id": private_network ["vdcId"] },
           "connection": {
            "routerRef": { "id": private_network["edge_id"] },
           "connectionType": "INTERNAL",
           "connected": "true"
                        },
           "subnets": {
             "values": [
                     {
            "gateway": private_network["gateway"],
            "prefixLength": private_network["prefixLength"],
            "dnsServer1": private_network["dnsServer1"],
            "dnsServer2": private_network["dnsServer2"],
            "ipRanges": {
             "values": private_network["ipRanges"]
             },
             "enabled": "true"
          }
          ]
        },
       "strictIpMode": "false",
       "guestVlanTaggingAllowed": "false",
       "routeAdvertised": "false",
       "shared": private_network["shared"]

         }
        r=self.session.post(f"{self.base}/cloudapi/1.0.0/orgVdcNetworks", headers=self._h(), json=payload)
        if r.status_code==202:
            return self.wait_task_final(r.headers["Location"])
        else :
            return {"error":f"{r.status_code} {r.reason} {r.text}"}
        
    
        



    def create_vdc_application_port_prfile(self, aplication_profile:dict, org_id:str, vdc_id:str)-> dict:
        """Crea un application profile para un vdc: 
        Args:          
        aplication_profile (dict) Obligatorio 
        Campos {"name":str, "description":str,
        "org_id": str, "vdc_id":str , 
        "applicationPorts":list [dict]}
        
        applicationPorts dict campos: 
        {"name":str, "protocol":"TCP"|"UDP"|ICMPv4, "destinationPorts":[]|None}
        Return: 
       - si exito {"success":application_profile_id(str)}
       - si error {"error":error(str)}
        """
        payload={
     "name": aplication_profile["name"],
     "description": aplication_profile["description"],
      "orgRef":{"id":aplication_profile["org_id"]},
     "scope": "TENANT",
     "contextEntityId":aplication_profile["vdc_id"],
     "applicationPorts": aplication_profile["applicationPorts"],
     "usableForNAT": True
     }
        header=self._h()
        r=self.session.post(f"{self.base}/cloudapi/1.0.0/applicationPortProfiles", headers=header, json=payload)
        if r.status_code==202:
            return self.wait_task_final(r.headers["Location"])  
        else: 
            return {"error":f"{r.status_code} {r.reason} {r.text}"}
        
