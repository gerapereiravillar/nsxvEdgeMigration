from src.edge_migrator.infrastructure.vcloud_api.policy import xmlApiPolicy
from src.edge_migrator.domain.canonical import fwRule, org, vdc, private_network, edgeGateway, staticRoute, protoPorts



class xmlMapper:
    def __init__(self, policy:xmlApiPolicy):
        self.policy=policy
        pass

##adapter_format->canonical

    def fw_rule_to_canonical(self, fw_rules:list )->list[fwRule]:
        new_fw_rules=[]
        for rule in fw_rules:
              
        #Transformamos a canonico
        # 1) Obtener protocolos y puertos:
            proto_ports=[] 
            origin_ports=[]
            dest_ports=[]
            origin_cidr=[]
            dest_cidr=[]
            not_maped_source_cidr=[]
            not_maped_destination_cidr=[]


            for serv in rule["services"]:
                if "protocol" in serv:
                   protocol=serv["protocol"].upper() 
                elif "icmpType" in serv:
                    protocol="ICMP"
                else:
                    protocol="ANY"
                dest_ports=[serv["port"] ]if "port" in serv else []
                origin_ports=[serv["sourcePort"]] if "sourcePort" in serv else []
                new_protoPo=protoPorts(protocol=protocol, orgin_ports=origin_ports, dest_ports=dest_ports)
                proto_ports.append(new_protoPo)

            action="allow" if rule["action"].lower()=="accept" else "deny"

            name=rule["name"]

            origin_cidr=rule["source_ips"]
            dest_cidr=rule["dest_ips"]
            not_maped_source_cidr=rule["not_maped_source"]
            not_maped_destination_cidr=rule["not_maped_destination"]
            new_fw=fwRule(name=name,origin_cidr=origin_cidr,
                              dest_cidr=dest_cidr,protoPorts=proto_ports,
                              not_maped_source_cidr=not_maped_source_cidr,
                              not_maped_destination_cidr=not_maped_destination_cidr,action=action, 
                              active=rule["enabled"], loggin=rule["loggingEnabled"])
            new_fw_rules.append(new_fw)   
        
        return new_fw_rules
                

    def priv_network_to_canonical(self, priv_networks:list )->list[private_network]:
        new_priv_networks=[]
        for priv_net in priv_networks:
            print ("Mapper, red privada a canonico:", priv_net)
            new_priv_net = private_network(name=priv_net["name"],
                                           gateway=priv_net["gateway"],
                                           network_cidr=str(priv_net["gateway"]) + "/" + str(priv_net["prefixLength"]),
                                           dns1=priv_net["dnsServer1"],
                                           dns2=priv_net["dnsServer2"],
                                           prefix_length=priv_net["prefixLength"],
                                           shared=priv_net["shared"], 
                                           ipRange_start=priv_net["ipRanges"][0]["startAddress"] if "ipRanges" in priv_net and len(priv_net["ipRanges"])>0 else None,
                                           ipRange_end=priv_net["ipRanges"][0]["endAddress"] if "ipRanges" in priv_net and len(priv_net["ipRanges"])>0 else None)
            new_priv_networks.append(new_priv_net)
        return new_priv_networks

    def orgs_to_canonical(self, orgs:list )->list[org]:
        new_orgs=[]
        for org_data in orgs:
            new_org=org(name=org_data["name"], id=org_data["id"])
            new_orgs.append(new_org)
        return new_orgs
    
    def vdc_to_canonical(self, vdc_list:list )->list[vdc]:
        new_vdcs=[]
        for vdc_data in vdc_list:
            new_vdc=vdc(name=vdc_data["name"], id=vdc_data["id"])
            new_vdcs.append(new_vdc)
        return new_vdcs
    

    
    def edge_gateway_to_canonical(self, edge_gateway_list:list)->list[edgeGateway]:
        new_edge=[]
        for edge_gateway  in edge_gateway_list:
             new_edge_gateway = edgeGateway(name=edge_gateway["name"], id=edge_gateway["id"],
                                        status=edge_gateway["status"] if "status" in edge_gateway else None, 
                                       nsxvId=edge_gateway["nsxvId"] if "nsxvId" in edge_gateway else None)
             new_edge.append(new_edge_gateway)
        
        return new_edge

    
    def static_route_to_canonical(self, static_routes:list )->list[staticRoute]:
        new_static_routes=[]
        for static_route in static_routes:
            new_static_route=staticRoute(name=static_route["Name"],
                                          network_cidr=static_route["Network"],
                                          next_hop_ip=static_route["NextHopIp"])
            new_static_routes.append(new_static_route)
        return new_static_routes


#canonical->adap


    def canonical_to_snat(self, snat_rules:list ):
        pass

    def canonical_to_dnat(self, dnat_rules:list ):
        pass
    def canonical_to_fw_rule(self, fw_rules:list ):
        pass
        
    def canonical_to_priv_network(self, priv_networks:list ):
        pass
    
    def canonical_to_edge_gateway(self, edge_gateway:dict ):
        pass    
    
    def canonical_to_static_route(self, static_routes:list ):
        pass
    


    