from src.edge_migrator.domain.ports.nsxV_api import NSXVApi
from src.edge_migrator.domain.ports.vcd_api import VcdXmlApi
from src.edge_migrator.domain.ports.vcd_openApi import VcdOpenApi
from src.edge_migrator.shared.response import Response
from src.edge_migrator.domain.canonical import fwRule, natrules,edgeCluster,edgeGateway, external_network,dnatRule, snatRule, org, vdc, staticRoute, private_network
import xml.etree.ElementTree as ET
import ipaddress  
class edgeMigration :
    def __init__(self, nsxv_api:NSXVApi, xml_api:VcdXmlApi, api_open:VcdOpenApi):
        self.nsxv_api=nsxv_api
        self.xml_api=xml_api
        self.api_open=api_open

        
    def login_in_origin(self)->Response:
        """Inicia sesión en vCloud Director legacy (XML API)."""
        return self.xml_api.login()
    
    def login_in_dest(self)->Response:
        """Inicia sesión en vCloud Director Open API."""
        return self.api_open.login()
    
    def login_in_nsxv(self)->Response:
        """Inicia sesión en NSX-V."""
        return self.nsxv_api.test_login()
    
    def get_origin_orgs(self)->Response[list[org]]:
        """Lista organizaciones en vCloud Director legacy (XML API)."""
        return self.xml_api.get_orgs_urn()
    
    def get_origin_orgs_by_name(self, name:str)->Response[list[org]]:
        """Lista organizaciones en vCloud Director legacy (XML API)."""
        return self.xml_api.get_orgs_by_name(name)
    
    def get_origin_vdc_by_org_id(self, org_id:str)->Response[list[vdc]]:
        """Lista VDCs de una organización en vCloud Director legacy (XML API)."""
        return self.xml_api.get_vdc_org_by_id(id=org_id)
    
    def get_origin_vdc_edges(self, vdc_id:str)->Response[list[edgeGateway]]:
        """Lista Edge Gateways de un VDC en vCloud Director legacy (XML API)."""
        return self.xml_api.vdc_list_edges(vdc_id=vdc_id)
    
    def get_origin_edge_ext_ips(self , edge_id )->list:
        edge_xml=self.xml_api.get_edge_xml(edge_id)
        return self.xml_api.get_edge_external_ips(edge_xml.data)
    
    def get_origin_edge_info(self, edge_id)->Response[edgeGateway]:
        """Obtiene información del Edge en vCloud Director legacy (XML API).El campo warning incluye alertas sobre redes internas de tipo shared."""
        #Obtenemos las redes internas para avisarle si encontramos alguna de tipo shared, estas no se pueden crear en destino. 

        edge_xml=self.xml_api.get_edge_xml(edge_id)
        warnings=[]

        if edge_xml.ok:
            int_net_id=self.xml_api.get_id_internal_networks(edge_xml.data)
            if int_net_id.ok:
                int_net_info=self.xml_api.get_networks_info(int_net_id.data)
                if int_net_info.ok:
                         int_net_info_list:list[private_network]=int_net_info.data
                         for net in int_net_info_list:
                             if int(net.get_shared())==True:
                                 warnings.append(f"La red interna '{net.get_name()}' es de tipo 'shared'. Se crearar como shared=False en destino.")
        else :
               return edge_xml
        
        edge_desc=self.xml_api.get_edge_general_desc(edge_xml.data)
        edge_ips=self.xml_api.get_edge_external_ips(edge_xml.data)
        public_ips=[]
    
       
        
        if edge_desc.ok and edge_ips.ok :
            edge_desc.data.set_alerts(warnings)
            for ip in edge_ips.data:
                ip=ipaddress.ip_address(ip)
                if ip.is_private==False:
                    public_ips.append(ip)
                    
            edge_desc.data.total_ips=len(public_ips)
        
        return edge_desc
    

    def get_dest_ext_newtworks(self, org_id)->Response[list[external_network]]:
        """Lista redes externas en vCloud Director Open API."""
        return self.api_open.get_external_networks(org_id)
    

    def get_dest_edge_clusters(self)->Response[list[edgeCluster]]:
        """Lista Edge Clusters en vCloud Director Open API."""
        return self.api_open.get_edge_cluster()
    

    def get_origin_edge_external_networks(self, edge_id: str)->Response:
        """Obtiene redes externas del Edge en vCloud Director legacy (XML API)."""
        edge_xml=self.xml_api.get_edge_xml(edge_id)
        if edge_xml.ok:
            return self.xml_api.get_external_networks(edge_xml.data)
        else:
            return edge_xml

    
    
    def create_edge_in_dest( self,edge_name:str, edge_desc:str, vdc_id: str,  edge_cluster_id, ext_newtwork_id: str, total_ips) -> Response[edgeGateway]:
        """Crea un Edge Gateway en vCloud Director Open API."""

        
        
        return self.api_open.create_edge(
            edge_name=edge_name,
            vdc_id=vdc_id,
            edge_cluster_id=edge_cluster_id,
            extern_netwrk_id=ext_newtwork_id,
            total_ips=total_ips,
            edge_desc=edge_desc,
        )
        
    def get_origin_internal_networks(self, edge_id:str, edge_xml: ET=None)->Response[list[private_network]]:
        """Lista redes internas en un VDC en vCloud Director legacy (XML API).Si edge xml es None, lo obtiene."""
        if edge_xml==None: 
            edge_xml=self.xml_api.get_edge_xml(edge_id)
            if not edge_xml.ok:
                return edge_xml
            else :
                edge_xml=edge_xml.data

        in_ids =self.xml_api.get_id_internal_networks(edge_xml)
        if not in_ids.ok:
            return in_ids
        net_info=self.xml_api.get_networks_info(in_ids.data)
        if not net_info.ok:
                return net_info
        return net_info

            
    def get_dest_edge_public_ips(self, edge_id: str) -> Response:
            """Obtiene IPs públicas configuradas en el Edge en vCloud Director Open API."""
            return self.api_open.get_edge_public_ips(edge_id=edge_id)  
    def get_dest_orgs(self)->Response[list[org]]:
        return self.api_open.get_orgs()

    def get_dest_org_by_name(self, name:str)->Response[list[org]]:
        return self.api_open.get_orgs_by_name(name)
    def get_dest_vdc_by_org_id(self, org_id:str)->Response[list[org]]:
        return self.api_open.get_vdc_for_org_id(org_id)
    
 
    
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
    def get_origin_edge_firewall_rules(self,edge_nsxv_id:str,edge_id: str,ip_mapping:dict[str, str]) -> Response[list[fwRule]]:
        """Obtiene reglas de firewall del Edge en vCloud Director legacy (XML API)."""
        edge_xml=self.xml_api.get_edge_xml(edge_id)
        if edge_xml.ok:
            
            #Obtener redes internas
            int_net_id=self.xml_api.get_id_internal_networks(edge_xml.data)
            int_net=self.xml_api.get_networks_info(int_net_id.data)
            
            if int_net_id.ok and int_net.ok:
                      int_net=int_net.data
                  #obtener redes externas y extraer ips . 
                      ext_ips_list=self._get_origin_ext_ips_list(edge_xml.data)
                      #Obtener las vnics del edge en nsxv
                      vnics_list=self.nsxv_api.get_vnics(edge_id=edge_nsxv_id)
                      if vnics_list.ok:   
                            vnic_list=vnics_list.data
                            #Obtener las reglas de firewall
                            actual_firewall_rules=self.xml_api.get_firewall_rules(
                                edge_id=edge_id,
                                internal_net=int_net,
                                vnic_newt_list=vnic_list,
                                public_ips_list=ext_ips_list.data,
                            )
                            actual_firewall_rules.data=self.__change_ips_origin_firewall_rules(actual_firewall_rules.data,
                                  ip_map=ip_mapping) 
                                
                            return actual_firewall_rules
                            
                      else:
                            return vnics_list
                      
          
                    
                  
            
            else: return int_net_id if not int_net_id.ok else int_net
           
        else:

            return edge_xml
        
                                 
                             
    def _get_origin_ext_ips_list(self, edge_xml:ET.ElementTree)->Response[list[str]]:
            """Extrae las IPs públicas de las redes externas del Edge."""
            ext_ips_list=self.xml_api.get_edge_external_ips(edge_xml)
            return ext_ips_list   
        


    def __change_ips_origin_firewall_rules(self,firewall_rules:list[fwRule], ip_map:dict[str])->list[fwRule]:
        """Cambia las ips publicas de la regla de firewall."""
        for rule in firewall_rules: 
            source_ips=rule.get_origin_cidr()
            dest_ips=rule.get_dest_cidr()
            new_source_ips=[]
            new_dest_ips=[]
       #     print ("Regla:", rule["name"])
            for item in source_ips:
                #Ip puede estar en formato CIDIR 0.0.0.0/mask 179.27.195.200/24
        #        print("Procesando ip source", item)
                ip=str(item).split("/")[0]
                mask=str(item).split("/")[-1]
                subnet=None
                if mask is not None and mask!=ip and mask:
                   subnet=ipaddress.ip_network(f"{ip}/{mask}", strict=False)
                #Si la ip es exactamente alguna de las ips anteriores. 
                if item in ip_map and item not in new_source_ips:
         #           print ("Cambio ip", item, "por", ip_map[ip])
                    new_source_ips.append(ip_map[ip])
                #Si hay una subred, analizamos si es el subrango publico. Si lo es agregamos las nuevas ips 
                elif subnet is not None and subnet.is_private==False: 
          #          print ("Es una subred", subnet)
                    is_new_public=False
                    for actual_ip in ip_map.keys():
                       if ipaddress.ip_address(actual_ip) in subnet and actual_ip not in new_source_ips:
                           new_source_ips.append(ip_map[actual_ip])
                           is_new_public=True
           #                print ("Cambio ip", actual_ip, "por", ip_map[actual_ip])
                       #Si es red publica pero no es alguna de las interfaces publicas del edge 
                    if not is_new_public and item not in new_source_ips:
                           new_source_ips.append(item)
            #               print ("No cambio ip", item) 
                else: 
              #      print ("No cambio ip", item)
                    new_source_ips.append(item)
            
            for item in dest_ips:
                #Ip puede estar en formato CIDIR
          #      print ("Analizo ip dest", item)
                ip=str(item).split("/")[0]
                mask=str(item).split("/")[-1]
                subnet=None

                if mask is not None and mask !=ip and mask:
                   subnet=ipaddress.ip_network(f"{ip}/{mask}", strict=False)
                #Si la ip es exactamente alguna de las ips anteriores.
                if item in ip_map and item not in new_dest_ips:
                    new_dest_ips.append(ip_map[ip])
           #         print ("Cambio ip", item, "por", ip_map[ip])

                elif subnet is not None: 
                    is_new_public=False
                    for actual_ip in ip_map.keys():
                       if ipaddress.ip_address(actual_ip) in subnet and actual_ip not in new_dest_ips:
                           new_dest_ips.append(ip_map[actual_ip])
                           is_new_public=True
            #               print ("Cambio ip", item, "por", ip_map[actual_ip])
                    if not is_new_public and item not in new_source_ips:
                           new_dest_ips.append(item)
             #              print ("No cambio ip", item) 
                else: 
              #      print ("No cambio ip", item)
                    new_dest_ips.append(item)
            rule.set_origin_cidr(new_source_ips)
            rule.set_dest_cidr(new_dest_ips)
            
        return firewall_rules
    
    def get_nat_rules(self,ip_mapping:dict[str, str], edge_ndxv_id:str)->Response[natrules]:
        """Obtiene reglas de NAT del Edge en vCloud Director legacy (XML API)."""
        #Obtener reglas de nat en origen 
        nat_rules=self.nsxv_api.get_nat_rules(edge_ndxv_id)
        if nat_rules.ok:
            #Transformamos con nuevas ips 
            nat_rules.data=self.__transform_nat_rules(nat_rules.data, ip_mapping)
            return nat_rules

        else:
            return nat_rules
        


    def get_static_routes(self, edge_id:str)->Response[list[staticRoute]]:
        """Obtiene rutas estáticas del Edge en vCloud Director legacy (XML API)."""
        edge_xml=self.xml_api.get_edge_xml(edge_id)
        if not edge_xml.ok:
            return edge_xml
        #OBTENER RUTAS ESTATICAS
        static_routes=self.xml_api.get_static_routes(edge_xml.data)
        if static_routes.ok:
            return static_routes
        else:
            return static_routes



    def __transform_nat_rules(self,nat_rules:natrules, ips_mapping)->list:
        """Cambiar ips reglas de nat"""
        new_dnat_rules=[]
        new_snat_rules=[]
        dnat_rules_list=nat_rules.get_dnat_rules()
        snat_rules_list=nat_rules.get_snat_rules()

        #Cambiar el destination
        for rule in dnat_rules_list: 
            translatedAddress=rule.get_translated_cidr()
            originalAddress=rule.get_original_cidr()
            #Si es CIDIR
            tras_ip=translatedAddress.split("/")[0]
            mask=translatedAddress.split("/")[-1]
            origin_ip=originalAddress.split("/")[0]
            mask=originalAddress.split("/")[-1]

            #Si es una de las ips publicas de forma literal, la cambio 
            if tras_ip in ips_mapping:
                rule.set_translated_cidr=f"{ips_mapping[tras_ip]}"
            #Como no se pueden poner desde la GUI mas de una ip, dejo como esta si no es la ip lit
            if origin_ip in ips_mapping:
                rule.original_cidr=f"{ips_mapping[origin_ip]}"
            new_dnat_rules.append(rule)
             
             
            #SNAT 
        for rule in snat_rules_list: 
            translatedAddress=rule.get_translated_cidr()
            originalAddress=rule.get_original_cidr()
                #Si es CIDIR
            tras_ip=translatedAddress.split("/")[0]
            mask=translatedAddress.split("/")[-1]
            origin_ip=originalAddress.split("/")[0]
            mask=originalAddress.split("/")[-1]


            #Si es una de las ips publicas de forma literal, la cambio 
            if tras_ip in ips_mapping:
              rule.set_translated_cidr(ips_mapping[tras_ip])

            #Como no se pueden poner desde la GUI mas de una ip, dejo como esta si no es la ip lit
            if origin_ip in ips_mapping:
                rule.original_cidr=f"{ips_mapping[origin_ip]}"
            new_snat_rules.append(rule)


        nat_rules.dnatrules=new_dnat_rules
        nat_rules.snatrules=new_snat_rules

        return nat_rules 
    

    #Por ahora no traduce nada,
    #  no tiene sentido si el edge tiene solo salida a internet a traves de una unica inter

    def __transform_static_routes(self, static_routes, ips_mapping):
        new_static_routes=[]
        for route in static_routes:
            new_static_routes.append(route)
        return new_static_routes    
    


##############################################

    def create_dest_firewall_rules(self, fw_rules: list[fwRule], edge_id: str) -> Response:
     """Crear reglas de firewall en vCloud Director destino. """
     for fw_rule in fw_rules:
        created_result=self.api_open.create_firewall_rule(fw_rule, edge_id)
        if not created_result.ok:
            return created_result
     
     
     return Response.success(data=f"Se crearon {len(fw_rules)} reglas de firewall.")


        
    def create_dest_snat_rules(self, snat_rules: list[snatRule], edge_id: str)-> Response:
        """Crear reglas de SNAT en vCloud Director destino."""

        #Ahora las creamos 
        for snat in snat_rules:
            result=self.api_open.create_snat_rule(snat, edge_id)
            if not result.ok:
                return result
        
        return Response.success(data=snat_rules)
            
               

        
    def create_dest_dnat_rules(self, edge_id: str, dnat_rules:list[dnatRule], vdc_id:str, org_id :str)->Response:
           
           for dnat in dnat_rules:
 
               result=self.api_open.create_dnat_rule(dnat, edge_id, vdc_id, org_id)

               if not result.ok:
                       return result

           return Response.success(data=dnat_rules)


    def __is_aplication_profile(self, protocol: str, ports: str, aProfile :dict )->Response: 
        """Determina si un application profile cumple con los puertos y protocolos:"""
        aProtocol=str(aProfile["protocol"]).lower if "protocol" in aProfile and aProfile["protocol"] else None
        aPorts=aProfile["ports"] if "ports" in aProfile and aProfile["ports"] else None

        if aProtocol==protocol and ports in aPorts: 
            return Response.success(aProfile)
        else : return Response.error()     
                   

    def created_dest_int_networks(self, int_nets: list[private_network ], vdc_id: str, edge_id:str)->Response:
        """Crear redes internas en vCloud Director destino."""
        for net in int_nets:
            result=self.api_open.create_private_network(net, vdc_id, edge_id)
            if not result.ok:
                return result
        return Response.success(data=int_nets)
    

    def create_dest_static_routes(self , static_routes: list[staticRoute], edge_id: str)->Response:
        """Crear rutas estáticas en vCloud Director destino."""
        for route in static_routes:
            result=self.api_open.create_static_route(route, edge_id)
            if not result.ok:
                return result
        return Response.success(data=static_routes)
            

                
            
        
     


            
            

          