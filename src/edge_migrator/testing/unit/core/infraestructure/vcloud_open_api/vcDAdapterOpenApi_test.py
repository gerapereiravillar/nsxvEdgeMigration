import os
import sys
sys.path.append(os.path.abspath("./src/edge_migrator/infrastructure/vcloud_open_api/"))
from vcd_open_api_adapter import vCloudOpenApiAdap
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
base_url="https://domain.example.com"
user="user"
org="system"
password="passwd"
api_version="39.1"
api_adapter=vCloudOpenApiAdap(base_url=base_url, user=user, org=org, password=password, api_version=api_version)
login_result=api_adapter.login()

#Login 
if "success" in login_result:
    print ("Resultado del login: ok ,id de session:", login_result["success"] ) 
else:
    print ("Resultado del login: error ", login_result["error"] )
    sys.exit("Error de login, se detiene ejecucion")


#Obtener organizaciones max 128 reg
get_orgs_result=api_adapter.get_orgs()
if "success" in get_orgs_result:
    print ("Obtener organizaciones: ok, cantidad de org", len(get_orgs_result["success"])) 
else:
    print ("Obtener organizaciones: error ", get_orgs_result["error"] )


#Obtener organizaciones por nombre
get_orgs_by_name_result=api_adapter.get_org_by_name(org_name="MVDCOMM_TEST")
if "success" in get_orgs_by_name_result:
    print ("Obtener organizaciones por nombre A*: ok, cantidad de org", len(get_orgs_by_name_result["success"]), get_orgs_by_name_result["success"][0]["id"])
else:
    print ("Obtener organizaciones por nombre: error ", get_orgs_by_name_result["error"] )


#VDC DE UNA ORG
get_vdc_result=api_adapter.get_vdc_for_org_id(get_orgs_by_name_result["success"][0]["id"])
if "success" in get_vdc_result:
    print ("Obtener vdcs para la primera org de la lista (nombre %s): ok:", get_vdc_result["success"])
else:
    print("Obtener vdc para la primera org de la lista: error", get_vdc_result["error"])    



#Obtener los edge cluster 
get_edge_cluster_result=api_adapter.get_edge_cluster()
if "success" in get_edge_cluster_result:
    print ("Obtener edge cluster: ok, cantidad de edge cluster", get_edge_cluster_result["success"])
else:
    print ("Obtener edge cluster: error ", get_edge_cluster_result["error"] )

#Obtener redes externas
get_external_network_result=api_adapter.get_edge_external_network()
if "success" in get_external_network_result:
    print ("Obtener external network: ok, cantidad de external network", len(get_external_network_result["success"]))
    for net in get_external_network_result["success"]:
        print (net, "\n")
else:
    print ("Obtener external network: error ", get_external_network_result["error"] )



#Crear el edge 
edge_name="appTest"
edge_desc="Test de creacion desde edgeMigrator"
vdc_id=get_vdc_result["success"][1]["id"]
edge_cluster_id=get_edge_cluster_result["success"][1]["id"]


#external_network_id=get_external_network_result["success"][0]["id"]
external_network_id="urn:vcloud:network:0628f348-fe0e-4129-9f36-2df353db0f1c"
#Mandamos a crear el edge 

#create_edge_result=api_adapter.create_edge(edge_name,vdc_id,edge_cluster_id,external_network_id,total_ips=1,edge_desc=edge_desc)
#if "success" in create_edge_result:
#   print ("Crear edge: ok", create_edge_result)
#else:
#    print ("Crear edge: error ", create_edge_result )

#Ver el estado de una tarea 
#task_status=api_adapter.get_task_status(url="https://serviciosnube.mvdcloud.uy/api/task/a29da9cd-bbb6-45ff-b58a-da020556ef9e")
#print ("Obtener estado de una tarea:", task_status)


#Crear una red en un vdc 
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
private_net_info={"name":"Red_interna_2", "description":"Red interna", 
               "vdcId":get_vdc_result["success"][1]["id"], "edge_id":"urn:vcloud:gateway:5b668f38-8207-4c4e-9716-5479d64dfc4b","gateway":"192.168.1.1", "prefixLength":24,
               "dnsServer1":"8.8.8.8", "dnsServer2":"8.8.4.4",
               "enable":True, "shared":False,
               "ipRanges":[{"startAddress":"192.168.1.2", "endAddress":"192.168.1.255"}]
 }
#create_net_result=api_adapter.create_private_networks(private_net_info)
#if "success" in create_net_result:
#   print ("Crear red interna: ok", create_net_result)
#else:
#    print ("Crear red interna: error ", create_net_result )

#Crear una regla de firewall: 
"""Crea una regla de firewall en un edge especifico
        Args: edge_id (str) (obligatorio) Sin URN, ej  aab0bf10-fd0c-40b9-a658-07c3d67ee2e1
              firewall_rules (dict)
              campos:
              Todos los campos que adminten valor None, None=Any 
              {"name":str,  "active":bool, "logging":bool, "actionValue":"ALLOW"|"DENY"|str,
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
            
       
destinationFirewallIpAddresses=[
    "190.0.157.45",
    "190.0.132.38",
    "107.180.24.238",
    "104.18.22.19",
    "8.8.8.8",
    "192.168.30.253",
    "179.27.195.4",
    "190.64.1.26"
  ]
sourceFirewallIpAddresses=["192.168.30.25/24"]
rawPortProtocols=[{"layer4Item": { "protocol": "UDP", "sourcePorts": None, "destinationPorts": None }},
                  { "layer4Item": { "protocol": "TCP", "sourcePorts": None, "destinationPorts": ["22"] } }]

relativePosition={ "rulePosition": "BOTTOM", "adjacentRuleId": None }
firewall_rule={"name":"Test Rule_0", "active":True, "logging":True, "actionValue":"ALLOW",
               "sourceFirewallIpAddresses":sourceFirewallIpAddresses, "destinationFirewallIpAddresses":destinationFirewallIpAddresses,
               "rawPortProtocols":rawPortProtocols, "relativePosition":relativePosition}
#create_firewall_result=api_adapter.create_firewall_rules(firewall_rules=firewall_rule, edge_id="urn:vcloud:gateway:5b668f38-8207-4c4e-9716-5479d64dfc4b")
#if "success" in create_firewall_result:
#   print ("Crear firewall: ok", create_firewall_result)
#else:
#    print ("Crear firewall: error ", create_firewall_result )

"""Crea un application profile para un vdc: 
        Args:          
        aplication_profile (dict) Obligatorio 
        Campos {"name":str, "description":str,
        "org_id": str, "vdc_id":str , 
        "applicationPorts":list [dict]}
        
        applicationPorts dict campos: 
        {"name":str, "protocol":"TCP"|"UDP"|None, "destinationPorts":[]|None}
        Return: 
       - si exito {"success":application_profile_id(str)}
       - si error {"error":error(str)}
        """
org_id="urn:vcloud:org:781d506b-c4f4-4de2-89bd-269a6cf80368"
vdc_id=get_vdc_result["success"][1]["id"]
application_ports=[{"name":"ssh_11", "protocol":"TCP", "destinationPorts":["1111"]}]
applicarion_prof={"name":"test_nsg_migration_2", "description":"test", "org_id":org_id, 
                  "vdc_id":vdc_id,"applicationPorts":application_ports }

#create_application_result=api_adapter.create_vdc_application_port_prfile(applicarion_prof, org_id,vdc_id )
#print("Creando application profile", create_application_result)

#Crear DNAT 
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
edge_id="urn:vcloud:gateway:5b668f38-8207-4c4e-9716-5479d64dfc4b"
applicarion_prof={"id":"urn:vcloud:applicationPortProfile:451e5c09-4864-482a-9831-cb363b071baa"}
dnat_rule={"name":"DNAT edge_migra", "externalAddresses":"179.27.195.2", "internalAddresses":"192.168.30.2", "dnatExternalPort":8, 
           "priority":1, "active":True, "logging":False, "applicationPortProfile":applicarion_prof}

#create_dnat_result=api_adapter.create_dnat_rule(edge_id=edge_id, nat_rules=dnat_rule)
#if "success" in create_dnat_result:
#   print ("Crear DNAT: ok", create_dnat_result)
#else:
#    print ("Crear DNAT: error ", create_dnat_result )


    #Crear SNAT 
"""Crear una regla de SNAT en un edge especifico
        Args: nat_rules(dict)
         campos: 
          {"name":str, "internalAddresses":CDIR(str), "externalAddresses":CDIR(str),
          "snatDestinationAddresses":CDIR(str)|None,
          "priority":int, "active":bool, "logging":bool} """


nat_rule={"name":"SNAT edge_migra", "internalAddresses":"192.168.30.2", "externalAddresses":"179.27.195.2", 
          "snatDestinationAddresses":None, "priority":1, "active":True, "logging":False}
#create_snat_result=api_adapter.create_snat_rule(edge_id=edge_id, nat_rules=nat_rule)
#if "success" in create_snat_result:
#   print ("Crear SNAT: ok", create_snat_result)
#else:
#    print ("Crear SNAT: error ", create_snat_result )

"""Crea una ruta estatica en un edge especifico: 
        Args: 
        static_route (dict) Obligatorio 
        edge_id (str) Obligatorio 
        
        static_route campos:
         {"name":str, "description":str, "networkCidr":str, "nextHops":list[dict]}
        
        nexHops campos: 
           {"ipAddress":str, "adminDistance":str} """
nextHops=[{"ipAddress":"192.168.30.2", "adminDistance":"1"}]
static_route={"name":"Test20", "description":"Static route edge migra ","networkCidr":"192.168.30.0/24", "nextHops":nextHops }
#create_static_route_result=api_adapter.create_static_route(edge_id=edge_id, static_route=static_route)
#if "success" in create_static_route_result:
#   print ("Crear static route: ok", create_static_route_result)
#else:
#    print ("Crear static route: error ", create_static_route_result )



#Obtener ips de un edge 
edge_ips=api_adapter.get_edge_public_ips(edge_id="urn:vcloud:gateway:5b668f38-8207-4c4e-9716-5479d64dfc4b")
print(edge_ips)