from abc import ABC, abstractmethod    

class edgeGateway:
    def __init__(self, name:str, description:str, total_ips:str=1, alerts:list=[], id:str=None):
        self.name = name
        self.description = description
        self.total_ips = total_ips
        self.id = id
        self.alerts = alerts


    #Getters
    def get_name(self):
        return self.name
    def get_description(self):
        return self.description
    def get_total_ips(self):
        return self.total_ips
    def get_alerts(self):
        return self.alerts
    def get_id(self):
        return self.id
    
    def set_alerts(self, alerts):
        self.alerts=alerts
    
    def set_total_ips(self, total_ips:int ):
        self.total_ips=total_ips
    
    
class staticRoute:
    def __init__(self, name:str, network_cidr:str, next_hop_ip:str):
        self.name = name
        self.network_cidr = network_cidr
        self.next_hop_ip = next_hop_ip
    
    def get_name(self):
        return self.name
    
    def get_network_cidr(self):
        return self.network_cidr
    
    def get_next_hop_ip(self):
        return self.next_hop_ip
    
    def set_name(self,name):
        self.name = name
    
    def set_network_cidr(self,network_cidr):
        self.network_cidr = network_cidr
    
    def set_next_hop_ip(self,next_hop_ip):
        self.next_hop_ip



class protoPorts:
    protocols=["ANY", "TCP","UDP","ICMP"]

    def __init__(self, protocol: str, orgin_ports:list[str], dest_ports:list[str]):
        if protocol.upper() not in protoPorts.protocols:
            raise ValueError(f"Protocolo invalido: {protocol}. Debe de ser una de las siguientes:{protoPorts.protocols}")   
        self.protocol = protocol
        self.orgin_ports = orgin_ports
        self.dest_ports = dest_ports


    def get_protocol(self):
        return self.protocol
    
    def get_orgin_ports(self):
        return self.orgin_ports
    
    def get_dest_ports(self):
        return self.dest_ports 
       

    @classmethod
    def get_availables_protocols(cls):
        return protoPorts.protocols


class fwRule:
    actions=["allow","deny"]
    
    def __init__(self, name :str ,origin_cidr:list[str], 
                 dest_cidr:list[str], protoPorts:list[protoPorts],
                 not_maped_source_cidr:list[str]=[],
                 not_maped_destination_cidr:list[str]=[],
                 action="allow",
                 active:bool=False, loggin:bool=False):
        if action not in  fwRule.actions: #TODO: Add custom exception
            raise ValueError(f"Accion invalida: {action}. Debe de ser una de las siguientes:{fwRule.actions}")

            
        self.action=action
        self.name = name
        self.origin_cidr = origin_cidr
        self.dest_cidr = dest_cidr
        self.not_maped_source_cidr = not_maped_source_cidr
        self.not_maped_destination_cidr = not_maped_destination_cidr
        self.active = active
        self.loggin = loggin
        self.protoPorts = protoPorts
        
    
#Getters 
    def get_name(self):
        return self.name
    
    def get_origin_cidr(self):
        return self.origin_cidr
    
    def get_dest_cidr(self):
        return self.dest_cidr
    
    def get_protoPorts(self):
        return self.protoPorts
    
    def get_not_maped_source(self):
        return self.not_maped_source_cidr
    def get_not_maped_destination(self):
        return self.not_maped_destination_cidr
    def get_active(self):
        return self.active
    def get_loggin(self):
        return self.loggin
    def get_action(self):
        return self.action


    
#Setters 

    def set_name(self,name):
        self.name = name
    
    def set_origin_cidr(self,origin_cidr:list[str]):
        self.origin_cidr = origin_cidr
    
    def set_dest_cidr(self,dest:list[str]):
        self.dest_cidr = dest
    
    def set_protoPorts(self, protoPorts:list[protoPorts]):
        self.protoPorts = protoPorts

    def set_not_maped_source(self,not_maped_source_cidr:list[str]):
        self.not_maped_source_cidr = not_maped_source_cidr
    
    def set_not_maped_destination(self,not_maped_destination_cidr:list[str]):
        self.not_maped_destination_cidr = not_maped_destination_cidr

    def set_active(self,active):
        self.active = active
    
    def set_loggin(self,loggin):
        self.loggin = loggin



class snatRule:
    
    def __init__(self,name:str,original_cidr:str,translated_cidr:str, dest_cidr:str=None, priority:int=0, active:bool=True, loggin:bool=False, protocol:str="all"):
    
        self.name = name
        self.original_cidr = original_cidr
        self.translated_cidr = translated_cidr
        self.dest_cidr = dest_cidr
        self.priority = priority
        self.active = active
        self.loggin = loggin
        self.protocol = protocol

   #Getters 
    def get_protocol(self):
        return self.protocol
    def get_name(self):
        return self.name
    
    def get_original_cidr(self):
        return self.original_cidr
    
    def get_translated_cidr(self):
        return self.translated_cidr
   
    def get_dest_cidr(self):
        return self.dest_cidr

    def get_priority(self):
        return self.priority
    def get_active(self):
        return self.active
    def get_loggin(self):
        return self.loggin


    #Setters 
    def set_protocol(self,protocol):
        self.protocol = protocol

    def set_name(self,name):
        self.name = name
    
    def set_original_cidr(self,original_cidr):
        self.original_cidr = original_cidr

    def set_translated_cidr(self,translated_cidr):
        self.translated_cidr = translated_cidr
    
    def set_dest_cdir(self,dest_cidr):
        self.dest_cidr = dest_cidr
    def set_priority(self,priority):
        self.priority = priority    
    def set_active(self,active):
        self.active = active
    def set_logging(self,loggin):
        self.loggin = loggin
    #DTOS    

class dnatRule:
    
    def __init__(self,name:str,original_cidr:str,translated_cidr:str, external_port:str, internal_port:str, protocol:str="all", prtiority:int=0, active:bool=False, loggin:bool=False):
        self.name = name
        self.original_cidr = original_cidr
        self.translated_cidr = translated_cidr
        self.external_port = external_port
        self.internal_port = internal_port
        self.protocol = protocol
        self.prtiority = prtiority
        self.active = active
        self.loggin = loggin

    


   #Getters 
    def get_name(self):
        return self.name
    
    def get_original_cidr(self):
        return self.original_cidr
    
    def get_translated_cidr(self):
        return self.translated_cidr
   
    
    def get_external_port(self):
        return self.external_port

    def get_internal_port(self):
        return self.internal_port
    
    def get_protocol(self):
        return self.protocol
    
    def get_priority(self):
        return self.prtiority
    
    def get_active(self):
        return self.active
    def get_logging(self):
        return self.loggin
    
    #Setters 
    def set_name(self,name):
        self.name= name
    
    def set_original_cidr(self,original_cidr):
        self.original_cidr = original_cidr

    def set_translated_cidr(self,translated_cidr):
        self.translated_cidr = translated_cidr
    

    def set_internal_port(self,internal_port):
        self.internal_port = internal_port

    def set_external_port(self,external_port):
        self.external_port = external_port
    
    def set_protocol(self,protocol):
        self.protocol = protocol
    def set_priority(self,priority):
        self.prtiority = priority
    def set_active(self,active):
        self.active = active
    def set_logging(self,loggin):
        self.loggin = loggin

  #DTOS 

class edgeGateway:
    def __init__(self,id:str, nsxvId:str,name:str, total_ips:str=1, alerts:list=[], status:str=None):
        self.nsxvId = nsxvId
        self.name = name
        self.total_ips = total_ips
        self.id = id
        self.alerts = alerts
        self.status = status




    #Getters
    def get_name(self):
        return self.name
    def get_description(self):
        return self.description
    def get_total_ips(self):
        return self.total_ips
    def get_alerts(self):
        return self.alerts
    def get_id(self):
        return self.id
    def get_status(self):
        return self.status
    def get_nsxvId(self):
        return self.nsxvId
    
    def set_alerts(self, alerts):
        self.alerts=alerts
    

    
    



class org: #TODO: Define org class
    def __init__(self, name:str, id :str):
        self.name = name
        self.id = id


    def get_name(self):
        return self.name
    
    def get_id(self):
        return self.id
    


class vdc:
    def __init__(self, name:str, id:str ):
        self.name = name
        self.id = id

    def get_name(self):
        return self.name
    
    def get_id(self):
        return self.id





class natrules:
    def __init__(self, dnatrules:list[dnatRule], snatrules:list[snatRule]):
        self.dnatrules = dnatrules
        self.snatrules = snatrules
        
    def get_dnat_rules(self):
        return self.dnatrules
    
    def get_snat_rules(self):
        return self.snatrules
    
class network(ABC):
    @abstractmethod
    def get_name(self):
        pass
    @abstractmethod
    def get_gateway(self):
        pass
    @abstractmethod
    def get_network_cidr(self):
        pass



class private_network(network):
    def __init__(self,name:str, gateway:str, network_cidr:str, dns1:str, dns2:str, prefix_length:str,ipRange_start:str=None,ipRange_end:str=None,mask:str=None, dns_suffix=None, shared:bool=False):
        self.name = name
        self.gateway = gateway
        self.network_cidr = network_cidr
        self.dns1 = dns1
        self.dns2 = dns2
        self.dns_suffix = dns_suffix
        self.shared=shared
        self.prefix_length = prefix_length
        self.mask=mask
        self.shared=shared
        self.ipRange_start=ipRange_start
        self.ipRange_end=ipRange_end

        

        
    
    #Getters
    def get_name(self):
        return self.name
    
    def get_gateway(self):
        return self.gateway
    
    def get_network_cidr(self):
        return self.network_cidr
    
    def get_dns1(self):
        return self.dns1
    
    def get_dns2(self):
        return self.dns2
    
    def get_dns_suffix(self):
        return self.dns_suffix
    
    def get_prefix_length(self):
        return self.prefix_length
    
    def get_mask(self):
        return self.mask
    
    def get_shared(self):
        return self.shared
    def get_ipRange_start(self):
        return self.ipRange_start       
    def get_ipRange_end(self):
        return self.ipRange_end
    

    
    
class external_network(network):
    def __init__(self,name:str,id:str, gateway:str, network_cidr:str,prefix_length:str,mask:str=None, ipsFree:str=0):
        self.name = name
        self.id = id
        self.gateway = gateway
        self.network_cidr = network_cidr
        self.ipsfree=ipsFree
        self.prefix_length = prefix_length
        self.mask=mask
        
    
    #Getters
    def get_name(self):
        return self.name
    
    def get_id(self):
        return self.id
    
    def get_gateway(self):
        return self.gateway
    
    def get_network_cidr(self):
        return self.network_cidr

    def get_prefix_length(self):
        return self.prefix_length
    
    def get_mask(self):
        return self.mask
    
    def get_ips_free(self):
        return self.ipsfree
           






class edgeCluster:
    def __init__(self, name:str, id:str):
        self.name = name
        self.id = id


    #getters 
    def get_name(self):
        return self.name
    
    def get_id(self):
        return self.id