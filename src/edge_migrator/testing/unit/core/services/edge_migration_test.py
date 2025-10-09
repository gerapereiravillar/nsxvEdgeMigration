import sys
import os
import json
from edge_migrator.startup.composition_root import build_edge_service
from edge_migrator.domain.canonical import fwRule, private_network, natrules, dnatRule, snatRule

# --- Helpers bonitos ---
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"

def print_title(text):
    print(f"\n{BOLD}{CYAN}{'='*50}\n{text}\n{'='*50}{RESET}")

def print_section(text):
    print(f"\n{BOLD}{YELLOW}--- {text} ---{RESET}")

def print_dict(obj, indent=2):
    try:
        print(json.dumps(obj, indent=indent, ensure_ascii=False))
    except:
        print(obj)

# --- Configuración inicial ---
origin_organization_name = "CB_SA"
origin_vdc_number = 0
dest_organization_name = "MVDCOMM_TEST"
dest_vdc_number = 1
dest_external_network_id = "urn:vcloud:network:0628f348-fe0e-4129-9f36-2df353db0f1c"
list_dest_ext_net = False
dest_edge_cluster = 1
ip_mapping = {
    "190.64.204.147":"179.27.196.37",
    "190.64.204.148": "179.27.196.37", 
    "190.64.204.162":"179.27.196.38",
    "190.64.204.163":"179.27.196.39"
}
create_edge_in_dest = True
create_private_net_in_dest = True
create_firewall_rules_in_dest = True
create_static_routes_in_dest = True
crete_snat_rules = True
create_dnat_rules = True 
total_ips = 3

cfg = {
    "VCD_XML_BASE": "https://origin.domain.example.com",
    "VCD_XML_USER": "originUser",
    "VCD_XML_ORG": "system",
    "VCD_XML_PASS": "passwd",
    "VCD_XML_VERSION": "36.2",
    "NSXV_BASE": "https://nsxvManager.domain.example.com",
    "NSXV_USER": "user",
    "NSXV_PASS": "passwd",
    "VCD_OPEN_BASE": "https://dest.domain.example.com",
    "VCD_OPEN_USER": "user",
    "VCD_OPEN_ORG": "system",
    "VCD_OPEN_PASS": "passwd",
    "VCD_OPEN_VERSION": "39.1"
}

# Composition root
edge_service = build_edge_service(cfg)

# --- Logins ---
print_title("LOGIN EN ORIGEN Y DESTINO")
login_origin_result = edge_service.login_in_origin()
login_dest_result = edge_service.login_in_dest()

if not login_origin_result.ok:
    print(f"{RED}❌ Error de login en origen:{RESET}", login_origin_result.error)
    sys.exit(0)
else:
    print(f"{GREEN}✅ Login en origen OK{RESET}")

if not login_dest_result.ok:
    print(f"{RED}❌ Error de login en destino:{RESET}", login_dest_result.error)
    sys.exit(0)
else:
    print(f"{GREEN}✅ Login en destino OK{RESET}")

# --- EdgeCluster destino ---
print_title("EDGE CLUSTER DESTINO")
dest_get_edge_cluster = edge_service.get_dest_edge_clusters()
if dest_get_edge_cluster.ok:
    dest_edge_cluster_id = dest_get_edge_cluster.data[dest_edge_cluster].get_id()
    print_dict(dest_get_edge_cluster.data[dest_edge_cluster].__dict__)
else:
    print(f"{RED}❌ Error al obtener edgeClusters:{RESET}", dest_get_edge_cluster.error)
    sys.exit(0)

# --- Org origen ---
print_title("ORGANIZACIÓN ORIGEN")
org_origin_result = edge_service.get_origin_orgs_by_name(origin_organization_name)
if org_origin_result.ok:
    origin_org = org_origin_result.data[0]
    print_dict(origin_org.__dict__)
else:
    print(f"{RED}❌ Error al obtener org origen:{RESET}", org_origin_result.error)
    sys.exit(0)

# --- VDC origen ---
print_title("VDC ORIGEN")
origin_get_vdc_result = edge_service.get_origin_vdc_by_org_id(origin_org.get_id())
if origin_get_vdc_result.ok:
    origin_vdc = origin_get_vdc_result.data[origin_vdc_number]
    print_dict(origin_vdc.__dict__)
else:
    print(f"{RED}❌ Error al obtener VDCs de org:{RESET}", origin_get_vdc_result.error)
    sys.exit(0)

# --- Edge origen ---
print_title("EDGE ORIGEN")
origin_get_edge = edge_service.get_origin_vdc_edges(origin_vdc.get_id())
if origin_get_edge.ok:
    origin_edge = origin_get_edge.data[0]
    print_dict(origin_edge.__dict__)
else:
    print(f"{RED}❌ Error al obtener edges de vdc:{RESET}", origin_get_edge.error)
    sys.exit(0)

# --- Info edge origen ---
print_title("INFO EDGE ORIGEN")
origin_edge_info = edge_service.get_origin_edge_info(origin_edge.get_id())
if origin_edge_info.ok:
    origin_edge_info = origin_edge_info.data
    print_dict(origin_edge_info.__dict__)
else:
    print(f"{RED}❌ Error al obtener info de edge:{RESET}", origin_edge_info.error)
    sys.exit(0)

# --- Reglas NAT origen ---
print_title("NAT RULES ORIGEN")
origin_get_nat_rules = edge_service.get_nat_rules(
    ip_mapping=ip_mapping,
    edge_ndxv_id=origin_edge_info.get_nsxvId()
)
if origin_get_nat_rules.ok:
    print(f"{GREEN}✅ Reglas NAT obtenidas OK{RESET}")
    print_section("Reglas DNAT")
    for rule in origin_get_nat_rules.data.get_dnat_rules():
        print_dict(rule.__dict__)
    print_section("Reglas SNAT")
    for rule in origin_get_nat_rules.data.get_snat_rules():
        print_dict(rule.__dict__)
else:
    print(f"{RED}❌ Error al obtener NAT rules:{RESET}", origin_get_nat_rules.error)
    sys.exit(0)

# --- Org destino ---
print_title("ORGANIZACIÓN DESTINO")
get_dest_org = edge_service.get_dest_org_by_name(dest_organization_name)
if get_dest_org.ok:
    dest_org_id = get_dest_org.data[0].get_id()
    print_dict(get_dest_org.data[0].__dict__)
else:
    print(f"{RED}❌ Error al obtener org destino:{RESET}", get_dest_org.error)
    sys.exit(0)

# --- VDC destino ---
print_title("VDC DESTINO")
get_dest_vdc = edge_service.get_dest_vdc_by_org_id(dest_org_id)
if get_dest_vdc.ok:
    dest_vdc_id = get_dest_vdc.data[dest_vdc_number].get_id()
    print_dict(get_dest_vdc.data[dest_vdc_number].__dict__)
else:
    print(f"{RED}❌ Error al obtener VDC destino:{RESET}", get_dest_vdc.error)
    sys.exit(0)

origin_edge_id = str(origin_edge_info.get_id().split(":")[-1]).strip()
origin_edge_nsxv_id = origin_edge_info.get_nsxvId()
new_edge_id = "urn:vcloud:gateway:ea76a92f-189a-47f6-b9f3-cc7535649c61"

# --- Redes externas destino ---
if list_dest_ext_net:
    print_title("REDES EXTERNAS DESTINO")
    dest_get_ext_net = edge_service.get_dest_ext_newtworks()
    if dest_get_ext_net.ok:
        print(f"{GREEN}✅ Redes externas obtenidas OK{RESET}")
        for net in dest_get_ext_net.data:
            print_dict(net.__dict__)
    else:
        print(f"{RED}❌ Error al obtener redes externas:{RESET}", dest_get_ext_net.error)
        sys.exit(0)

# --- Firewall origen ---
print_title("FIREWALL ORIGEN")
origin_get_edge_fw_rules = edge_service.get_origin_edge_firewall_rules(
    edge_id=origin_edge_id,
    edge_nsxv_id=origin_edge_nsxv_id,
    ip_mapping=ip_mapping
)
if origin_get_edge_fw_rules.ok:
    print(f"{GREEN}✅ Reglas de firewall obtenidas OK{RESET}")
    for rule in origin_get_edge_fw_rules.data:
        print_dict(rule.__dict__)
        proto_list = rule.get_protoPorts()
        for proto in proto_list:
            print_dict(proto.__dict__)
else:
    print(f"{RED}❌ Error al obtener firewall rules:{RESET}", origin_get_edge_fw_rules.error)

#Static routes origen
origin_get_edge_route_rules = edge_service.get_static_routes(edge_id=origin_edge_id)
if origin_get_edge_route_rules.ok:
        print(f"{GREEN}✅ Rutas estáticas obtenidas OK{RESET}")
        for route in origin_get_edge_route_rules.data:
            print_dict(route.__dict__)

else:
        print(f"{RED}❌ Error al obtener rutas estáticas:{RESET}", origin_get_edge_route_rules.error)
        sys.exit(0)    

print_title("CREACIÓN EN DESTINO")

# --- Crear Edge ---
if create_edge_in_dest:
    if total_ips == 0:
        get_ips_origin = edge_service._get_origin_ext_ips_list(origin_edge_id)
        if get_ips_origin.ok:
            total_ips = len(get_ips_origin.data)
        else:
            print(f"{RED}❌ Error al obtener IPs de edge origen:{RESET}", get_ips_origin.error)
            sys.exit(0)
    dest_create_edge_result = edge_service.create_edge_in_dest(
        vdc_id=dest_vdc_id,
        edge_cluster_id=dest_edge_cluster_id,
        edge_id=origin_edge_id,
        ext_newtwork_id=dest_external_network_id,
        total_ips=total_ips
    )
    if dest_create_edge_result.ok:
        print(f"{GREEN}✅ Edge creado en destino OK{RESET}")
        print_dict(dest_create_edge_result.data.__dict__)
        new_edge_id = dest_create_edge_result.data.get_id()
        print(f"Nuevo edge ID: {new_edge_id}")
    else:
        print(f"{RED}❌ Error al crear Edge en destino:{RESET}", dest_create_edge_result.error)
        sys.exit(0)
else:
    print("⚠️ Saltando creación de Edge en destino")



#Crear redes internas : 
if create_private_net_in_dest:
    origin_get_private_nets = edge_service.get_origin_internal_networks(origin_edge_id)
    if origin_get_private_nets.ok:
        print(f"{GREEN}✅ Redes internas obtenidas OK{RESET}")
        for net in origin_get_private_nets.data:
            print_dict(net.__dict__)
    else:
        print(f"{RED}❌ Error al obtener redes internas:{RESET}", origin_get_private_nets.error)
        sys.exit(0)

    dest_create_private_net = edge_service.created_dest_int_networks(
    edge_id=new_edge_id,
    int_nets=origin_get_private_nets.data,
    vdc_id=dest_vdc_id
        )
    if dest_create_private_net.ok:
            print(f"{GREEN}✅ Red interna creada en destino OK{RESET}")
           
    else:
            print(f"{RED}❌ Error al crear red interna en destino:{RESET}", dest_create_private_net.error)
            sys.exit(0)

# --- Crear firewall ---
if create_firewall_rules_in_dest:
    print_section("Firewall")
    origin_get_fw_openapi = edge_service.create_dest_firewall_rules(
        origin_get_edge_fw_rules.data,
        edge_id=new_edge_id
    )
    if origin_get_fw_openapi.ok:
        print(f"{GREEN}✅ Reglas de firewall creadas OK{RESET}")
    else:
        print(f"{RED}❌ Error al crear reglas de firewall:{RESET}", origin_get_fw_openapi.error)
        sys.exit(0)
else:
    print("⚠️ Saltando creación de reglas de firewall")

# --- Crear NAT ---
if create_dnat_rules or crete_snat_rules:
    origin_get_edge_nat_rules = edge_service.get_nat_rules(
        ip_mapping=ip_mapping,
        edge_ndxv_id=origin_edge_nsxv_id
    )
    if origin_get_edge_nat_rules.ok:
        snat_rules = origin_get_nat_rules.data.get_snat_rules()
        dnat_rules = origin_get_nat_rules.data.get_dnat_rules()
        print(f"{GREEN}✅ Reglas NAT obtenidas OK{RESET}")
    else:
        print(f"{RED}❌ Error al obtener NAT rules:{RESET}", origin_get_edge_nat_rules.error)
        sys.exit(0)

    if dnat_rules and create_dnat_rules:

        dest_create_dnat = edge_service.create_dest_dnat_rules(new_edge_id, dnat_rules, dest_vdc_id, dest_org_id)
        if not dest_create_dnat.ok:
            print(f"{RED}❌ Error al crear DNAT en destino:{RESET}", dest_create_dnat.error)
            sys.exit(0)

    if snat_rules and crete_snat_rules:
        dest_create_snat = edge_service.create_dest_snat_rules(snat_rules, new_edge_id)
        if not dest_create_snat.ok:
            print(f"{RED}❌ Error al crear SNAT en destino:{RESET}", dest_create_snat.error)
            sys.exit(0)
else:
    print("⚠️ Saltando creación de reglas NAT")

# --- Static routes ---


if create_static_routes_in_dest:
    dest_create_static_routes = edge_service.create_dest_static_routes(
        edge_id=new_edge_id,
        static_routes=origin_get_edge_route_rules.data
    )
    if dest_create_static_routes.ok:
        print(f"{GREEN}✅ Rutas estáticas creadas OK{RESET}")
    else : 
        print(f"{RED}❌ Error al crear rutas estáticas en destino:{RESET}", dest_create_static_routes.error)
        sys.exit(0)
else:
    print("⚠️ Saltando creación de rutas estáticas")
