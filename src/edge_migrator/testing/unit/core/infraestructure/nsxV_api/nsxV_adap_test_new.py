import sys 
import os
sys.path.append(os.path.abspath("./src/edge_migrator/"))
from infrastructure.nsxV_api.nsxV_adapter_new import nsxvAdapter
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

vcAdapTest=nsxvAdapter(base_url="domain.example.com",user="user", password="passwd" )
#Obtener vnics de un edge
resp_vnics_list=vcAdapTest.get_vnics(edge_id="edge-43")

if resp_vnics_list.ok:
    print("Lista de vnics:" ,resp_vnics_list.data)  
else:
    print("Error al obtener la lista de vnics:" ,resp_vnics_list.error)
print ("\n")

#Reglas de NAT 
resp_edge_nat_rules=vcAdapTest.get_nat_rules(edge_id="edge-43") 
if resp_edge_nat_rules.ok:
       nat_rules_list=resp_edge_nat_rules.data
       for rule in nat_rules_list:
           print("Nat Rule:", rule)
           print ("\n")
else:
    print("Error al obtener la lista de nat rules:" ,resp_edge_nat_rules.error)
print ("\n")


