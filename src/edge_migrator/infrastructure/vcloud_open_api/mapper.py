from src.edge_migrator.infrastructure.vcloud_open_api.policy import openApiPolicy
from src.edge_migrator.domain.canonical import fwRule, dnatRule, snatRule, private_network, edgeGateway, staticRoute, edgeCluster, external_network, protoPorts, org, vdc
from src.edge_migrator.infrastructure.vcloud_open_api.policy import openApiPolicy
from datetime import datetime
import ipaddress




class openApiMapper:
    def __init__(self, policy:openApiPolicy):
        self.policy=policy
        pass

##adapter_format->canonical
    def snat_to_canonical(self, snat_rules:list )->list[snatRule]:
        pass

    def dnat_to_canonical(self, dnat_rules:list )->list[dnatRule]:
        pass

    def fw_rule_to_canonical(self, fw_rules:list )->list[fwRule]:
        
        pass

    
    def priv_network_to_canonical(self, priv_networks:list )->list[private_network]:
        pass
    
    def edge_gateway_to_canonical(self, edge_gateway:dict)->edgeGateway:
        pass

    
    def static_route_to_canonical(self, static_routes:list ):
        pass    
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
    
    
    


#canonical->adap

    def edge_cluster_to_canonical(self, edge_cluster:list)->list[edgeCluster]:
        edge_list=[]
        for edge in edge_cluster: 
            new_edge=edgeCluster(name=edge["name"], id=edge["id"])
            edge_list.append(new_edge)
        return edge_list
    
    
    def ext_network_to_canonical(self, external_networks:list )->list[external_network]:
        new_list=[]
        for net in external_networks: 
            gateway=net["subnets"]["values"][0]["gateway"] if "gateway" in net["subnets"]["values"][0] else None
            prefix=net["subnets"]["values"][0]["prefixLength"] if "prefixLength" in net["subnets"]["values"][0] else None
            totalIpCount=net["subnets"]["values"][0]["totalIpCount"] if "totalIpCount" in net["subnets"]["values"][0] else 0
            usedIpCount=net["subnets"]["values"][0]["usedIpCount"] if "usedIpCount" in net["subnets"]["values"][0] else 0
            net_cidr=f"{gateway}/{prefix}"
            ipsFree=int (totalIpCount)-int(usedIpCount)
            new_net=external_network(name=net["name"], id=net["id"], network_cidr=net_cidr,gateway=gateway, prefix_length=prefix, ipsFree=ipsFree)
            new_list.append(new_net)
        return new_list
    





    def canonical_to_snat(self, snat_rules:list [snatRule] )->list[dict]:
        new_snat_rules=[]
        for snat in snat_rules:
            #Adaptamos campos:
            current_date_time=  datetime.now()
            now = f"{current_date_time.date()} {current_date_time.time().strftime('%H:%M:%S')} {current_date_time.microsecond}"
            desc=snat.get_name() if snat.get_name() else f"migra_{now}"
            snat_des_cidr=snat.get_dest_cidr() if str(snat.get_dest_cidr()).lower()!="any" else None
            snat_orig_cidr=snat.get_original_cidr() if str(snat.get_original_cidr()).lower()!="any" else None
            snat_trans_cidr=snat.get_translated_cidr() if str(snat.get_translated_cidr()).lower()!="any" else None
            item={"name": desc, 
                  "internalAddresses":snat_orig_cidr, 
                  "externalAddresses":snat_trans_cidr,
                  "snatDestinationAddresses":snat_des_cidr, 
                    "priority":0, 
                    "active":snat.get_active(), 
                    "logging":snat.get_loggin() } 
            new_snat_rules.append(item)
            
        return new_snat_rules





    def canonical_to_dnat(self, dnat_rules:list[dnatRule] ):
               new_dnat_rules=[]

               for dnat in dnat_rules:
                        #Adaptamos campos:
                        internalAddresses=dnat.get_translated_cidr() if dnat.get_translated_cidr() else "any"
                        externalAddresses=dnat.get_original_cidr() if dnat.get_original_cidr() else "any"
                        externalPort=dnat.get_external_port() if dnat.get_external_port() else "any"
                        internalPort=dnat.get_internal_port() if dnat.get_internal_port() else "any"


                        if str(internalAddresses).lower()=="any" and not self.policy.get_suport_any_in_rules():
                            internalAddresses=None
                        if str(externalAddresses).lower()=="any" and not self.policy.get_suport_any_in_rules():
                            externalAddresses=None
                        if str(externalPort).lower()=="any" and not self.policy.get_suport_any_in_rules():
                            externalPort=None
                        if str(internalPort).lower()=="any" and not self.policy.get_suport_any_in_rules():
                            internalPort=None


                        dnat_item={
                       "name":dnat.get_name() if dnat.get_name() else f"migra_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                       "internalAddresses":internalAddresses,
                       "externalAddresses":externalAddresses,
                       "dnatExternalPort":externalPort,
                       "dnatInternalPort":internalPort,
                       "protocol":dnat.get_protocol(),
                       "applicationPortProfile":None, 
                       "priority":0,
                       "active":dnat.get_active(),
                       "logging":dnat.get_logging()
                   }
                        new_dnat_rules.append(dnat_item)

                    
               return new_dnat_rules 


        
    def canonical_to_fw_rule(self, fw_rule:fwRule )->list[dict]:
        ICMPV4_PROFILE_ID = "urn:vcloud:applicationPortProfile:3ebe3fa5-3b5a-5f93-b8cc-bd820ff55ff2"

        def _to_bool(v):
            if isinstance(v, bool): return v
            if isinstance(v, str): return v.strip().lower() == "true"
            return bool(v)

        def _none_if_empty(seq):
            return None if (seq is None or (isinstance(seq, (list, tuple)) and len(seq) == 0)) else seq

        def _normalize_l4_services(protoPortsL:list[protoPorts]):
           """
           Devuelve:
          - raw_protocols: lista de dicts layer4Item (solo TCP/UDP) o None si hay ANY
          - has_icmp: True si hay al menos un servicio ICMP

        Reglas:
         - 'icmp' -> se maneja afuera (regla separada)
           - 'any'  -> NO se puede enviar como layer4Item; si aparece, devolvemos None (match Any)
          - TCP/UDP -> se agrega con puertos (None = Any ports)
         """
           raw_protocols = []
           has_icmp = False
           any_seen = False

           for p in protoPortsL or []:
              proto = str(p.get_protocol()).strip().lower()

              if proto == "icmp":
                has_icmp = True
                continue

              if proto == "any":
                  any_seen = True
                  continue  # no agregamos layer4Item para 'any'

              if proto not in ("tcp", "udp"):
                # protocolo desconocido -> lo ignoramos para evitar nulls
                  continue

              sp = p.get_orgin_ports()[0]
              dp = p.get_dest_ports()[0]
              s_ports = None if (sp is None or str(sp).lower() == "any" and not self.policy.get_suport_any_in_rules()) else [str(sp)]
              d_ports = None if (dp is None or str(dp).lower() == "any" and not self.policy.get_suport_any_in_rules()) else [str(dp)]

              raw_protocols.append({
            "layer4Item": {
                "protocol": proto.upper(),           # <-- SIEMPRE TCP/UDP
                "sourcePorts": s_ports,              # None = Any
                "destinationPorts": d_ports          # None = Any
            }
        })

           if any_seen:
             # Si hubo 'any' en servicios, la semántica correcta es permitir cualquier L4:
            return None, has_icmp

           if not raw_protocols:
             raw_protocols = None

           return raw_protocols, has_icmp


        created_payloads = []

        action_value = "ALLOW" if str(fw_rule.get_action()).upper() == "ALLOW" else "REJECT"
        name = fw_rule.get_name() or None
        active = _to_bool(fw_rule.get_active())
        logging = _to_bool(fw_rule.get_loggin())
        src = _none_if_empty(fw_rule.get_origin_cidr())
        dst = _none_if_empty(fw_rule.get_dest_cidr())
        raw_l4, has_icmp = _normalize_l4_services(fw_rule.get_protoPorts())
        rule_position = {"rulePosition": "BOTTOM"}
        if dst!=None and "any" in dst and not self.policy.get_suport_any_in_rules(): 
            dst=None
        if src!=None and "any" in src and not self.policy.get_suport_any_in_rules(): 
            src=None
            
        # 1) Regla ICMP (si corresponde)
        if has_icmp:
                icmp_item = {
                "name": f"{name}_icmp" if name else None,
                "active": active,
                "logging": logging,
                "actionValue": action_value,
                "sourceFirewallIpAddresses": src ,
                "destinationFirewallIpAddresses": dst ,
                "applicationPortProfiles": [{"id": ICMPV4_PROFILE_ID}],  # <--- A mano
                "relativePosition": rule_position,
            }
                new_rule={"icmp":has_icmp, "item": icmp_item}
                created_payloads.append(new_rule)

        # 2) Regla normal (sin ICMP)
        normal_item = {
            "name": name,
            "active": active,
            "logging": logging,
            "actionValue": action_value,
            "sourceFirewallIpAddresses": src ,
            "destinationFirewallIpAddresses": dst ,
            "rawPortProtocols": raw_l4,      # None o lista de layer4Item
            "relativePosition": rule_position,
        }
        new_rule={"icmp":False, "item": normal_item}
        created_payloads.append(new_rule)

        return created_payloads
        
    def canonical_to_priv_network(self, priv_networks:list [private_network]):
        new_priv_networks=[]
        for priv in priv_networks:
            #Adaptamos campos:
            #calcular el rango 
          #  subnet_cidr=priv.get_network_cidr() 
          #  network = ipaddress.ip_network(subnet_cidr, strict=False)
            #Obtener el rango de ips
            # IPs utilizables (host más bajo y más alto) 
           # primera_host = list(network.hosts())[0]
           # ultima_host = list(network.hosts())[-1]
            ipRanges=[{"startAddress": priv.get_ipRange_start(), "endAddress": priv.get_ipRange_end()}] if priv.get_ipRange_start() and priv.get_ipRange_end() else []
            net_item={
                "name":priv.get_name(), 
                "description": priv.get_name(),
                "gateway":priv.get_gateway(), 
                "prefixLength":priv.get_prefix_length(), 
                "dnsServer1":priv.get_dns1(), 
                "dnsServer2":priv.get_dns2(), 
                "ipRanges":ipRanges, 
                "shared":priv.get_shared()
            }
            new_priv_networks.append(net_item)
        return new_priv_networks
    
    def canonical_to_edge_gateway(self, edge_gateway:dict ):
        pass    
    
    def canonical_to_static_route(self, static_routes:list[staticRoute] )->list[dict]:
        new_static_routes=[]
        for static in static_routes:
            static_item={
                "name":static.get_name(), 
                "description": static.get_name(),
                "networkCidr":static.get_network_cidr(), 
                "nextHops":[{"ipAddress":static.get_next_hop_ip(), "adminDistance":1}]}
            new_static_routes.append(static_item)
        return new_static_routes
    


    


    