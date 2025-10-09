import os
import sys
sys.path.append(os.path.abspath("./src/edge_migrator/infrastructure/nsxV_api/"))
from nsxv_adapter import nsxvAdapter
from xml.etree import ElementTree as ET
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

vcAdapTest=nsxvAdapter(base_url="https://domain.example.com",user="user", password="passwd" )
vnics_list=vcAdapTest.get_vnics(edge_id="edge-43")
print("Lista de vnics:" ,vnics_list)
print ("\n")
edge_nat_rules=vcAdapTest.get_nat_rules(edge_id="edge-43")
print("Lista de nat rules:\n" )
for nat_rule in edge_nat_rules["success"]:
    print("Regla de NAT",nat_rule)
    print ("\n")

    