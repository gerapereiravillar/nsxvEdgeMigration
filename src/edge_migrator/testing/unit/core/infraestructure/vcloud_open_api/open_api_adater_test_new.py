import sys 
import os
sys.path.append(os.path.abspath("./src/edge_migrator/"))
from infrastructure.vcloud_open_api.vcd_open_api_adapter_new import vCloudOpenApiAdap
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url="https://domain.example.com"
user="user"
org="system"
password="passwd"
api_version="39.1"
api_adapter=vCloudOpenApiAdap(base_url=base_url, user=user, org=org, password=password, api_version=api_version)
login_result=api_adapter.login()

#Teste de login 
if login_result.ok:
    print("Login ok")
    print(login_result.data)
else:
    print("Login failed")
    print(login_result.error)
    sys.exit(0)

#Obtener todas las organizaciones
result_get_orgs=api_adapter.get_orgs()
if result_get_orgs.ok:  
    print("Ontener organizaciones ok: cant", len (result_get_orgs.data))
else:
    print("Obtener organizaciones error")
    print(result_get_orgs.error)
    sys.exit(0)


#Obtener organización por nombre
org_name="MVDCOMM_TEST"
result_get_org_by_name=api_adapter.get_orgs_by_name(org_name=org_name)

if result_get_org_by_name.ok:
    print("Obtener organización por nombre ok")
    print(result_get_org_by_name.data)
    org_id=result_get_org_by_name.data[0]['id']
else:
    print("Obtener organización por nombre error")
    print(result_get_org_by_name.error)
    sys.exit(0)



#VDC DE UNA ORG
org_id=result_get_org_by_name.data[0]['id']
result_get_vdcs=api_adapter.get_vdc_for_org_id(org_id=org_id)

if result_get_vdcs.ok:
    print("Obtener VDCs de una org ok", result_get_vdcs.data)
else :
    print("Obtener VDCs de una org error")
    print(result_get_vdcs.error)
    sys.exit(0)


#Obtener los edge cluster 
result_get_edge_clusters=api_adapter.get_edge_cluster()
if result_get_edge_clusters.ok:
    print("Obtener edge clusters ok", result_get_edge_clusters.data)
else:
    print("Obtener edge clusters error")
    print(result_get_edge_clusters.error)
    sys.exit(0)

#Obtener redes externas
result_get_external_networks=api_adapter.get_edge_external_network()
if result_get_external_networks.ok:
    print("Obtener redes externas ok: cant:", len(result_get_external_networks.data))
else:
    print("Obtener redes externas error")
    print(result_get_external_networks.error)
    sys.exit(0)


#Crear un edge 
edge_name="appTest"
edge_desc="Test de creacion desde edgeMigrator"
vdc_id=result_get_vdcs.data[1]['id']
edge_cluster_id=result_get_edge_clusters.data[1]['id']
external_network_id="urn:vcloud:network:0628f348-fe0e-4129-9f36-2df353db0f1c"

result_create_edge=api_adapter.create_edge(edge_name=edge_name, edge_desc=edge_desc, vdc_id=vdc_id, edge_cluster_id=edge_cluster_id,extern_netwrk_id=external_network_id)
if result_create_edge.ok:
    print("Crear edge ok")
    print(result_create_edge.data)
    edge_id=result_create_edge.data["owner_id"]
else:
    print("Crear edge error")
    print(result_create_edge.error)
    sys.exit(0)

#Crear red privada en vdc 
private_net_info={"name":"Red_interna_2", "description":"Red interna", 
               "vdcId":vdc_id, "edge_id":edge_id,"gateway":"192.168.1.1", "prefixLength":24,
               "dnsServer1":"8.8.8.8", "dnsServer2":"8.8.4.4",
               "enable":True, "shared":False,
               "ipRanges":[{"startAddress":"192.168.1.2", "endAddress":"192.168.1.255"}]
 }

result_create_priv_net=api_adapter.create_private_network(private_network=private_net_info)
if result_create_priv_net.ok:
    print("Crear red privada ok")
    print(result_create_priv_net.data)
else:
    print("Crear red privada error")
    print(result_create_priv_net.error)
    sys.exit(0)

#Crear una regla de firewall: 
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
result_create_fw_rule=api_adapter.create_firewall_rule(edge_id=edge_id, firewall_rules=firewall_rule)
if result_create_fw_rule.ok:
    print("Crear regla de firewall ok")
    print(result_create_fw_rule.data)
else: 
    print("Crear regla de firewall error")
    print(result_create_fw_rule.error)
    sys.exit(0)


#Crear una ruta estatica: 
nextHops=[{"ipAddress":"192.168.30.2", "adminDistance":"1"}]
static_route={"name":"Test20", "description":"Static route edge migra ","networkCidr":"192.168.30.0/24", "nextHops":nextHops }
result_create_static_route=api_adapter.create_static_route(edge_id=edge_id, static_route=static_route)
if result_create_static_route.ok:
    print("Crear ruta estatica ok")
    print(result_create_static_route.data)
else:
    print("Crear ruta estatica error")
    print(result_create_static_route.error)
    sys.exit(0)


#Crear un application profile
# application_ports=[{"name":"ssh_11", "protocol":"TCP", "destinationPorts":["1111"]}]
# application_prof={"name":"test_nsg_migration_2", "description":"test", "org_id":org_id, 
#                   "vdc_id":vdc_id,"applicationPorts":application_ports }
# result_create_app_profile=api_adapter.create_vdc_application_port_prfile( aplication_profile=application_prof)
# if result_create_app_profile.ok:
#     print("Crear application profile ok")
#     print(result_create_app_profile.data)
#     app_profile_id=result_create_app_profile.data["id"]
# else:
#     print("Crear application profile error")
#     print(result_create_app_profile.error)
#     sys.exit(0)

#Crear regla DNAT 
applicarion_prof={"id":"urn:vcloud:applicationPortProfile:451e5c09-4864-482a-9831-cb363b071baa"}
dnat_rule={"name":"DNAT edge_migra", "externalAddresses":"179.27.195.2", "internalAddresses":"192.168.30.2", "dnatExternalPort":8, 
           "priority":1, "active":True, "logging":False, "applicationPortProfile":applicarion_prof}
result_create_dnat_rule=api_adapter.create_dnat_rule(edge_id=edge_id, nat_rules=dnat_rule)
if result_create_dnat_rule.ok:
    print("Crear regla DNAT ok")
    print(result_create_dnat_rule.data)
else:
    print("Crear regla DNAT error")
    print(result_create_dnat_rule.error)
    sys.exit(0)

