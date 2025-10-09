
import os
import sys

from edge_migrator.infrastructure.nsxV_api.nsxv_adapter import nsxvAdapter
from  edge_migrator.infrastructure.vcloud_api. vcd_client_adapter import VcdApiAdapter
from xml.etree import ElementTree as ET
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

vcAdapTest=VcdApiAdapter(base_url="https://domain.example.com",user="user", org="system" , password="passwd" )
##Test login
login_result=vcAdapTest.login()
if "success" in login_result:
    print ("Resultado del login: ok, id de session:",login_result["success"] ) 
else:
    print ("Resultado del login: error ", login_result["error"] )

# #Obtener organizaciones: 

# orgs_result=vcAdapTest.get_orgs_urn()
# if "success" in orgs_result :
#     print ("Obtener organizaciones: ok, cantidad de org", len(orgs_result["success"])) 
# else:
#     print ("Obtener organizaciones: error ", orgs_result["error"] )

# #Obtener una org por nombre:
# orgs_by_name_result=vcAdapTest.get_orgs_by_name(org_name="cintersa")
# if "success" in orgs_by_name_result :
#     print ("Obtener una org por nombre: ok, org obtenidas por filtro A*", orgs_by_name_result["success"]) 
# else:
#     print ("Obtener una org por nombre: error ", orgs_by_name_result["error"] )

# #Obtener VDC de una org
# vdc_id_list=vcAdapTest.get_vdc_org_by_id(orgs_by_name_result["success"][0]["id"])
# if "success" in vdc_id_list :   
#     print("Obteniendo vdc para la primera org de la lista (nombre %s): ok:", vdc_id_list["success"][0]["name"])
#     print ("\n")
# else:
#     print("Obteniendo vdc para la primera org de la lista: error", vdc_id_list["error"])
#     print ("\n")


# #Obtener edges para el primer vdc de la lista 
# vdc_list_edges=vcAdapTest.vdc_list_edges(vdc_id_list["success"][0]["id"])
# if "success" in vdc_list_edges :   
#     print("Obteniendo edges para el primer vdc de la list(nombre %s): ok", vdc_list_edges["success"][0]["name"])
#     print ("\n")
# else:
#     print("Obteniendo edges para el primer vdc de la lista: error", vdc_list_edges["error"])
#     print ("\n")


#Obtener xml de un edge
edgeXML=vcAdapTest.get_edge_xml("4984684c-21b3-4894-875e-bea12b804927")
if "success" in edgeXML :   
    print("Obteniendo xml de un edge(nombre %s): ok 4984684c-21b3-4894-875e-bea12b804927")
    print ("\n")
    #Imprimir elementos del edge XML 
    edge_info=vcAdapTest.get_edge_general_desc(edgeXML["success"])
    print("Obteniendo informacion general: status: ok , info: ", edge_info)
    print ("\n")
    #Obtener redes externas 
    ext_net_list=vcAdapTest.get_external_networks(edgeXML["success"])
    print("Obteniendo redes externas: ok , info: ", ext_net_list)
    print ("\n")

#     #Obtener redes internas 
#     internal_net_ids=vcAdapTest.get_id_internal_networks(edgeXML["success"])
#     print("Obteniendo redes internas: ok , info: ", internal_net_ids)
#     print ("\n")
#     internal_net_info=vcAdapTest.get_networks_info(internal_net_ids)
#     print("Obteniendo info de redes internas: ok , info: ", internal_net_info)
#     print ("\n")
#     #Obtener ips de vnics 
  
#   #Obtener ips de una vm 
#     vm_ips=vcAdapTest.get_vm_ips("5dd81c6c-f4fc-4a18-a33e-e2633604cf77")
#     if "success" in vm_ips:
#            print("Obteniendo ips de una vm: ok , info: ", vm_ips["success"])
#            print ("\n")
#     else: 
#         print ("Obteniendo ips de una vm: error", vm_ips["error"])
#         print ("\n")



# else:
#     print("Obteniendo xml de un edge: error", edgeXML["error"])
#     print ("\n")
# nsx_adap=nsxvAdapter(base_url="https://nsx-mgr01.mvdcloud.uy/",user="admin", password="Mvd19.Vcloud19" )
# vnics_list=nsx_adap.get_vnics(edge_id=edge_info["nsxvId"])
# print("Lista de vnics:" ,vnics_list)
# print ("\n")
# #Totales
# edge_id=str(edge_info["id"]).split(sep=":")[-1]
# internal_net_info_list=[]
# for net in internal_net_info:
#     if "success" in net:
#         internal_net_info_list.append(net["success"])
         

# #Obtenermos las ips externas de las vnics a redes externas
# ext_ips=[]         
# for ext_net in ext_net_list:
#     ext_ips.append(ext_net["primaryIp"])
#     for range in ext_net["ipRanges"]:
#         start=int(str(range["start"]).split(".")[-1])
#         end=int(str(range["end"]).split(".")[-1])
#         index=start
#         base_ip=range["start"].split(".")[0:3]
#         base_ip=".".join(base_ip)
#         while index <=end:
               
#             ext_ips.append(f"{base_ip}.{index}")
#             index+=1
        
        
# #Ver lista de ips asignadas (redes externas)
# print ("Lista de ips en redes externas  ", ext_ips)
# firewall_rules=vcAdapTest.get_firewall_rules(edge_id, internal_net_info_list, vnics_list, ext_ips)
# cant_rules=len(firewall_rules)
# print ("Transformando reglas de firewall total:" , cant_rules)
# #imprimir las reglas 
# if cant_rules:
#     for rule in firewall_rules:
#         print ("regla:" , rule)
#         print ("\n")


# static_routes_list=vcAdapTest.get_static_rules(edgeXML["success"])
# print ("Onteniendo reglas de ruteo ", static_routes_list)
# print ("\n")



