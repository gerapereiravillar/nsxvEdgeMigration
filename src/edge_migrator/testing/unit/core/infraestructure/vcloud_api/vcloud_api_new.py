import sys 
import os
sys.path.append(os.path.abspath("./src/edge_migrator/"))
from edge_migrator.infrastructure.vcloud_api.vcd_client_adapter_new import VcdApiAdapter
from edge_migrator.infrastructure.nsxV_api.nsxv_adapter import nsxvAdapter
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)




vcAdapTest=VcdApiAdapter(base_url="https://domain.example.com",user="user", org="system" , password="passwd" )
##Test login
login_result=vcAdapTest.login()
if login_result.ok:
    print ("Resultado del login: ok, id de session:",login_result.data )
else:
    print ("Resultado del login: error ", login_result.error )
    sys.exit()
#Obtener organizaciones:
orgs_result=vcAdapTest.get_orgs_urn()
if orgs_result.ok :
    print ("Obtener organizaciones: ok, cantidad de org", len(orgs_result.data))
else:
    print ("Obtener organizaciones: error ", orgs_result.error)
    sys.exit()
#Obtener una org por nombre:
orgs_by_name_result=vcAdapTest.get_orgs_by_name(org_name="cintersa")
if orgs_by_name_result.ok :
    print ("Obtener organizaciones por nombre: ok, cantidad de org", len(orgs_by_name_result.data))
else:
    print ("Obtener organizaciones por nombre: error ", orgs_by_name_result.error)
    sys.exit()
#Obtener VDC de una org
vdc_id_list=vcAdapTest.get_vdc_org_by_id(orgs_by_name_result.data[0]["id"])
if vdc_id_list.ok :
    print ("Obtener VDC de una org: ok, cantidad de VDC", len(vdc_id_list.data))
else:
    print ("Obtener VDC de una org: error ", vdc_id_list.error)
    sys.exit()

    
#Obtener edges para el primer vdc de la lista
vdc_list_edges=vcAdapTest.vdc_list_edges(vdc_id_list.data[0]["id"])
if vdc_list_edges.ok :
    print ("Obtener edges para el primer vdc de la lista: ok, cantidad de edges", vdc_list_edges.data[0])
else:
    print ("Obtener edges para el primer vdc de la lista: error ", vdc_list_edges.error)
    sys.exit()


#Obtener xml de un edge
edgeXML=vcAdapTest.get_edge_xml(vdc_list_edges.data[0]["id"])
if edgeXML.ok :
    print ("Obtener xml de un edge: ok, xml", edgeXML.data)
    
else:
    print ("Obtener xml de un edge: error ", edgeXML.error)
    sys.exit()
    
#Obtener info general del edge
edgeinfo=vcAdapTest.get_edge_general_desc(edgeXML.data)
if edgeinfo.ok : 
    print ("Obtener info general del edge: ok, info general", edgeinfo.data)    
else:
    print ("Obtener info general del edge: error ", edgeinfo.error)
    sys.exit()

#Obtener redes externas del edge 
extnets=vcAdapTest.get_external_networks(edgeXML.data)
if extnets.ok : 
    print ("Obtener redes externas del edge: ok, redes externas", extnets.data)
else:
    print ("Obtener redes externas del edge: error ", extnets.error)
    sys.exit()
#Obtener ids redes internas del edge
intnets=vcAdapTest.get_id_internal_networks(edgeXML.data)
if intnets.ok : 
    print ("Obtener ids redes internas del edge: ok, redes internas", intnets.data)
else:
    print ("Obtener ids redes internas del edge: error ", intnets.error)
    sys.exit()



#Obtener info redes internas del edge
intnetsinfo=vcAdapTest.get_networks_info(intnets.data)
if intnetsinfo.ok : 
    print ("Obtener info redes internas del edge: ok, info redes internas", intnetsinfo.data)
else:
    print ("Obtener info redes internas del edge: error ", intnetsinfo.error)
    sys.exit()  


    


