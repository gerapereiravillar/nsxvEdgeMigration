from flask import Blueprint, Response, send_from_directory, request , jsonify, session
from functools import wraps
import os 
from apps.api.blueprints.auth_utils import login_required, loginTest, json_required
from src.edge_migrator.shared.response import Response
from src.edge_migrator.domain.canonical import fwRule, natrules,edgeCluster,edgeGateway, external_network,dnatRule, snatRule, org, vdc, staticRoute, private_network, protoPorts
from src.edge_migrator.domain.services.edge_migration import edgeMigration
from src.edge_migrator.domain.ports.nsxV_api import NSXVApi
from src.edge_migrator.domain.ports.vcd_api import VcdXmlApi
from src.edge_migrator.domain.ports.vcd_openApi import VcdOpenApi
from apps.api.wiring import get_edge_migration
import requests
import socket
bp = Blueprint("migrate", __name__)


###Control de errores #########
def handle_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        # Errores comunes de requests / red
        except requests.exceptions.ConnectTimeout as e :
            return jsonify({"error": "Tiempo de espera agotado al conectar con el servidor :" }), 504

        except requests.exceptions.ReadTimeout:
            return jsonify({"error": "El servidor tardó demasiado en responder"}), 504

        except requests.exceptions.ConnectionError:
            return jsonify({"error": "No se pudo establecer la conexión con el servidor"}), 502

        except requests.exceptions.HTTPError as e:
            return jsonify({"error": f"Error HTTP recibido: {str(e)}"}), 502

        except requests.exceptions.TooManyRedirects:
            return jsonify({"error": "Demasiadas redirecciones al intentar conectar"}), 502

        # Errores más bajos de socket
        except socket.gaierror:
            return jsonify({"error": "Nombre de host no válido o no se pudo resolver"}), 502

        except socket.timeout:
            return jsonify({"error": "Tiempo de espera agotado en la conexión de socket"}), 504

        # Cualquier otro error inesperado
        except Exception as e:
            print("Error inesperado:" , str(e.args))
            return jsonify({"error": "Ocurrió un error inesperado en el servidor",
                            "detalle": str(e)}), 500
    return wrapper









###############################


@bp.route("/", methods=["GET"])
def index():
    current_dir = os.path.dirname(__file__)
    return send_from_directory(current_dir, 'edge-migration-tool.html')



@bp.route("/login/checkLogin", methods=["POST"])
@json_required
@handle_exceptions
def verifyLogin():
    """Verifica las credenciales de usuario y las url de los endpoinds, VDC (origen y dest ) y NSX V"""
    ##Obtener los datos del POST en formato JSON
    data = request.get_json()
    conf={}
    conf["VCD_XML_BASE"] = data.get("VCD_XML_BASE", None)
    conf["VCD_XML_USER"] = data.get("VCD_XML_USER", None)
    conf["VCD_XML_ORG"] = data.get("VCD_XML_ORG", None)
    conf["VCD_XML_PASS"] = data.get("VCD_XML_PASS", None)
    conf["VCD_XML_VERSION"] = data.get("VCD_XML_VERSION", "36.2")
    conf["NSXV_BASE"] = data.get("NSXV_BASE", None)
    conf["NSXV_USER"] = data.get("NSXV_USER", None)
    conf["NSXV_PASS"] = data.get("NSXV_PASS", None)
    conf["VCD_OPEN_BASE"] = data.get("VCD_OPEN_BASE", None)
    conf["VCD_OPEN_USER"] = data.get("VCD_OPEN_USER", None )
    conf["VCD_OPEN_ORG"] = data.get("VCD_OPEN_ORG", None)
    conf["VCD_OPEN_PASS"] = data.get("VCD_OPEN_PASS", None)
    conf["VCD_OPEN_VERSION"] = data.get("VCD_OPEN_VERSION", "39.1")
    pref=("http://", "https://")
    for item in conf: 
        if conf[item] is None:
            return jsonify({"error":"Faltan campos necesarios", "data":conf})
        
    edge_ser=get_edge_migration(conf)
    res=loginTest(edge_ser, conf)
    
    if res.ok :
        return jsonify({"success": "Login exitoso", "data":conf})
    else:
        return jsonify({"error": res.error}) , 401
     


#################################Origen ################################################

@bp.route("/getOriginOrgs", methods=["GET"])
@login_required
@handle_exceptions
def get_origin_orgs():
    """ Retorna una lista de organizaciones, si el parametro name esta en la consulta, se filtra por nombre."""
    edge_serv=get_edge_migration(session.get("conf"))
    edge_serv.login_in_origin()
    if  "name" in request.args:
        name= request.args["name"]
        res=edge_serv.get_origin_orgs_by_name(name )
    else:
        res=edge_serv.get_origin_orgs()


    if not res.ok:
        return jsonify({"error":res.error}) , 401
    

    org_list=[]
    for organization in res.data : 
        org_list.append(organization.__dict__)


    return jsonify(org_list)
         



@bp.route("/getOriginVdc", methods=["GET"])
@login_required
@handle_exceptions
def get_origin_vdc():
    """ Obtener lista de vdc de una org. El parametro org_id indica el id de la org"""
    if "org_id" in request.args:
        
        edge_serv=get_edge_migration(session.get("conf"))
        edge_serv.login_in_origin()

        res=edge_serv.get_origin_vdc_by_org_id(request.args["org_id"])
        if res.ok :
            vdc_list=[]

            for vdc in res.data:
                vdc_list.append(vdc.__dict__)
            return jsonify(vdc_list)
        
        
        else :
            return jsonify({"error":res.error}) , 400
 
    else:
        return jsonify({"error":"Falta el parametro org_id"}) , 400





@bp.route("/getOriginEdge", methods=["GET"])
@login_required
@handle_exceptions
def get_edge():
    """ Retorna una lista de edge de un VDC. El parametro vdc_id indica el id del VDC"""
    
    if "vdc_id" in request.args:
        edge_serv=get_edge_migration(session.get("conf"))
        edge_serv.login_in_origin()
        res=edge_serv.get_origin_vdc_edges(request.args["vdc_id"])
        if res.ok: 
            edge_lis=[]
            for edge in res.data:
                edge_lis.append(edge.__dict__)
            return jsonify(edge_lis)
        
        else:
            return jsonify({"error":res.error}), 500
    else:
        return jsonify({"error":"Falta el parametro vdc_id"}), 400
        




@bp.route("/getOriginEdgeInfo", methods=["GET"])
@login_required
@handle_exceptions
def get_edge_info():
    """ Retorna info de un edge. El parametro edge_id indica el id del edge"""

    if "edge_id" in request.args: 
        edge_ser=get_edge_migration(session.get("conf"))
        edge_ser.login_in_origin()
        res=edge_ser.get_origin_edge_info(request.args["edge_id"])
        if res.ok:
            return jsonify(res.data.__dict__)
        else:
            return jsonify({"error":res.error}), 500
    else : 
        return jsonify({"error":"Falta el parametro edge_id"}), 400




@bp.route("/getFwRules", methods=["POST"])
@login_required
@json_required
@handle_exceptions
def get_fw_rules():
    """ Obtener reglas de firewall de un edge de origen. El parametro edge_id indica el id del edge"""
    keys_required=["edge_id", "edge_nsxv_id", "ip_mapping"]
    data=request.get_json()
    if all(key in data for key in keys_required): 
        edge_ser=get_edge_migration(session.get("conf"))
        edge_ser.login_in_origin()
        res=edge_ser.get_origin_edge_firewall_rules(edge_id=data["edge_id"], edge_nsxv_id=data["edge_nsxv_id"], ip_mapping=data["ip_mapping"])
        if res.ok:
            fw_rules=[]
            for rule in res.data:
                new_fw_rule={"name":rule.get_name(),
                             "origin_cidr":rule.get_origin_cidr(),
                             "dest_cidr":rule.get_dest_cidr(),
                             "not_maped_source_cidr":rule.get_not_maped_source(),
                             "not_maped_destination_cidr":rule.get_not_maped_destination(),
                             "action":rule.get_action(),
                             "logging":rule.get_loggin(),
                             "active":rule.get_active()
                             }
                proto_por=rule.get_protoPorts()
                new_proto_port=[]
                for proto in proto_por:
                    new_proto_port.append(proto.__dict__)


                new_fw_rule["protoPorts"]=new_proto_port
               
                fw_rules.append(new_fw_rule)
            

            return jsonify(fw_rules)
        else:
            return jsonify({"error":res.error})
    else : 
        return jsonify({"error":"Faltan campos", "recibido":data, "requeridos":keys_required})




@bp.route("/getStaticRoutes", methods=["GET"])
@login_required
@handle_exceptions
def get_static_routes():
    """ Obtener reglas estaticas de un edge de origen. El parametro edge_id indica el id del edge"""
    
    if "edge_id" in request.args: 
        edge_ser=get_edge_migration(session.get("conf"))
        edge_ser.login_in_origin()
        res=edge_ser.get_static_routes(request.args["edge_id"])
        if res.ok:
            static_routes=[]
            for route in res.data:
                static_routes.append(route.__dict__)
            return jsonify(static_routes)
        else:
            return jsonify({"error":res.error}) 
   
    else : 
        return jsonify({"error":"Falta el parametro edge_id"}), 400



@bp.route("/getNatRules", methods=["POST"])
@login_required
@handle_exceptions
def get_nat_rules():
    """ Obtener reglas de NAT de un edge de origen. El parametro edge_id indica el id del edge"""
    data=request.get_json()
    keys_required=["edge_id", "ip_mapping", "edge_nsxv_id"]
    if all(key in data for key in keys_required): 
        edge_ser=get_edge_migration(session.get("conf"))
        edge_ser.login_in_origin()
        res=edge_ser.get_nat_rules(data["ip_mapping"],data["edge_nsxv_id"])
        if res.ok:
            snat=[]
            dnat=[]

            for s in res.data.get_snat_rules():
                snat.append(s.__dict__)

            for d in res.data.get_dnat_rules():
                dnat.append(d.__dict__)
               
            return jsonify({"snat":snat, "dnat":dnat})
        else:
            return jsonify({"error":res.error}) 
   
    else : 
        return jsonify({"error":"Faltan campos", "recibido":data, "requeridos":keys_required}), 400

@bp.route("/getPrivateNetworks", methods=["GET"])
@login_required
@handle_exceptions
def get_private_networks():
    """ Obtener redes privadas de un edge de origen. El parametro edge_id indica el id del edge"""
    if "edge_id" in request.args:
       migra_ser=get_edge_migration(session.get("conf"))
       migra_ser.login_in_origin()
       res=migra_ser.get_origin_internal_networks(request.args["edge_id"])
       if res.ok:
           private_network_list=[]
           for network in res.data:
               private_network_list.append(network.__dict__)
           return jsonify(private_network_list)
       else:
           return jsonify({"error":res.error}) , 500
    else   : 
        return jsonify({"error":"Falta el parametro edge_id"}), 400




@bp.route("/getOriginEdgeExtIps", methods=["GET"])
@login_required
@handle_exceptions
def get_origin_edge_ext_ips():
    """ Obtener redes privadas de un edge de origen. El parametro edge_id indica el id del edge"""
    if "edge_id" in request.args:
        edge_sev   = get_edge_migration(session.get("conf"))
        edge_sev.login_in_origin()
        res=edge_sev.get_origin_edge_ext_ips(request.args["edge_id"])
        if res.ok:
            return jsonify(res.data)
        else:
            return jsonify({"error":res.error}) , 500
        
    else: 
        return jsonify({"error":"Falta el parametro edge_id"}), 400


###############################Fin de origen ##################################






###############################Destino ########################################
@bp.route("/getDestOrgs", methods=["GET"])
@login_required
@handle_exceptions
def get_dest_orgs():
    """ Obtener lista org de destino. Si el parametro name esta en la consulta, se filtra por nombre."""
    edge_serv=get_edge_migration(session.get("conf"))
    edge_serv.login_in_dest()
    if "name" in request.args :
        res=edge_serv.get_dest_org_by_name(request.args["name"])
        if res.ok :
            org_list=[]
            for org in res.data:
                org_list.append(org.__dict__)
                
            return jsonify(org_list)
        else: 
            return jsonify({"error":res.error}), 500
    else :
        res =edge_serv.get_dest_orgs()
        if res.ok :
            org_list=[]
            for organization in res.data:
                org_list.append(organization.__dict__)

            return jsonify(org_list)
        else: 
            return jsonify({"error":res.error}), 500

          



@bp.route("/getDestVdc", methods=["GET"])
@login_required
@handle_exceptions
def get_vdc():
    """ Obtener lista vdc de una org de destino. El parametro org_id indica el id de la org"""
    if "org_id" in request.args:
        edge_serv=get_edge_migration(session.get("conf"))
        edge_serv.login_in_dest()
        res=edge_serv.get_dest_vdc_by_org_id(request.args["org_id"])
        if res.ok :
            vdc_list=[]
            for vdc in res.data:
                vdc_list.append(vdc.__dict__)
            return jsonify(vdc_list)
        
        
        else :
            return jsonify({"error":res.error}) , 400
    else : 
        return jsonify({"error":"Falta el parametro org_id"}), 400


@bp.route("/getDestEdgeClusters", methods=["GET"])
@login_required
@handle_exceptions
def get_edge_clusters():
    """ Obtener lista de clusters de edge de un VDC de destino."""

    edge_serv=get_edge_migration(session.get("conf"))
    edge_serv.login_in_dest()
    res=edge_serv.get_dest_edge_clusters()
    if res.ok :
        edge_cluster_list=[]
        for cluster in res.data:
            edge_cluster_list.append(cluster.__dict__)
        return jsonify(edge_cluster_list)
    else:
        return jsonify({"error":res.error}) , 500
    

@bp.route("/getDestNetworks", methods=["GET"])
@login_required
@handle_exceptions
def get_networks():
    """ Obtener lista de redes externas. """
    if not ("org_id" in request.args):
        return jsonify({"error":"Falta el parametro org_id"}), 400
        
    edge_serv=get_edge_migration(session.get("conf"))
    edge_serv.login_in_dest()
    res=edge_serv.get_dest_ext_newtworks(org_id=request.args["org_id"])
    if res.ok :
        net_list=[]
        for net in res.data:
            net_list.append(net.__dict__)
        return jsonify(net_list)
    else:
        return jsonify({"error":res.error}) , 500
      
    


@bp.route("/getDestEdgeIps", methods=["GET"])
@login_required
@handle_exceptions
def get_edge_ips():
    """Obtener lista de ips de las interfaces uplink (externas al vdc ) de un edge en destino. El parametro edge_id indica el id del edge"""
    if "edge_id" in request.args:
       edge_serv=get_edge_migration(session.get("conf"))
       edge_serv.login_in_dest()
       res=edge_serv.get_dest_edge_public_ips(request.args["edge_id"])
       if res.ok :
           return jsonify(res.data)
       else:
           return jsonify({"error":res.error}) , 500
    else : 
        return jsonify({"error":"Falta el parametro edge_id"}), 400


            


@bp.route("/createDestEdge", methods=["POST"])
@login_required
#@handle_exceptions
def create_edge():
    """ Crear un edge en el vdc de destino.Parametros necesarios, edge_cluster_id, name, ext_net_id, total_ips.  """
    data = request.get_json()
    required_keys = ["edge_cluster_id", "name", "desc", "ext_net_id", "total_ips", "vdc_id"]

    if all(key in data for key in required_keys):
        edge_ser=get_edge_migration(session.get("conf"))
        edge_ser.login_in_dest()
        res=edge_ser.create_edge_in_dest(data["name"], data["desc"], 
                                          data["vdc_id"], data["edge_cluster_id"], 
                                          data["ext_net_id"], data["total_ips"])
        if res.ok :
            return jsonify(res.data.__dict__)
        else:
            return jsonify({"error":res.error}) , 500
    else: 
        return jsonify({"error":"Faltan parametros", "datos recibidos":data, "required":required_keys}), 400
   


@bp.route("/createDestPrivateNetworks", methods=["POST"])
@login_required
@handle_exceptions
def create_private_networks():
    data=request.get_json()
    required_keys = ["private_networks", "edge_id", "vdc_id"]
    net_required_keys=["name", "gateway", "dns1", "dns2", "prefix_length", "ipRange_start", "ipRange_end", "shared"]
    if all(key in data for key in required_keys):
        private_networks=data["private_networks"]
        edge_id=data["edge_id"]
        vdc_id=data["vdc_id"]
        edge_ser=get_edge_migration(session.get("conf"))
        edge_ser.login_in_dest()
        new_private_networks=[]
        for network in private_networks:
            if all(key in network for key in net_required_keys):
                new_private_networks.append(private_network(name=network["name"], 
                                                        gateway=network["gateway"], 
                                                        network_cidr=network["network_cidr"], 
                                                        dns1=network["dns1"], 
                                                        dns2=network["dns2"], 
                                                        prefix_length=network["prefix_length"], 
                                                        ipRange_start=network["ipRange_start"], 
                                                        ipRange_end=network["ipRange_end"], 
                                                        shared=network["shared"]))
            else : 
                return jsonify({"error":"Faltan parametros en la red", "data_recived":network, "required":net_required_keys}), 400
        
        res=edge_ser.created_dest_int_networks(new_private_networks, vdc_id,edge_id)
        if res.ok : 
            new_private_networks=[]
            for net in res.data:
                new_private_networks.append(net.__dict__)
            return jsonify({"exito":"redes creadas correctamente.", "Redes creadas:":new_private_networks})
        else:
            return jsonify({"error":res.error}), 500
        



@bp.route("/createDestFirewallRules", methods=["POST"])
@login_required
@handle_exceptions
def create_fw_rules():
    data=request.get_json()
    keys_required=["fw_rules", "edge_id"]   
    fw_rule_keys_required=["name", "origin_cidr", "dest_cidr", "action", "active", "logging", "protoPorts"]
    proto_port_keys_required=["protocol", "orgin_ports", "dest_ports"]
    if not all(key in data for key in keys_required)  :
        return jsonify({"error":"Faltan parametros"}), 400
      
    fw_rules=data["fw_rules"]
    edge_id=data["edge_id"]
    try: 
           edge_ser=get_edge_migration(session.get("conf"))

           new_fw_rules=[]
           for rule in fw_rules:
            if not all(key in rule for key in fw_rule_keys_required):
               return jsonify({"error":"Faltan parametros en la regla", "data_recived":rule, "required":fw_rule_keys_required}), 400
            else :
               action=rule["action"]
               active=rule["active"]
               loggin=rule["logging"]
               name=rule["name"]
               origin_cidr=rule["origin_cidr"]
               dest_cidr=rule["dest_cidr"]
               proto_Ports=rule["protoPorts"]
               new_proto_ports=[]
               for proto in proto_Ports:
                if not all(key in proto for key in proto_port_keys_required):
                   return jsonify({"error":"Faltan parametros en los protocolos", "data_recived":proto, "required":proto_port_keys_required}), 400
                else :
                   new_proto_ports.append(protoPorts(protocol=proto["protocol"], orgin_ports=proto["orgin_ports"], dest_ports=proto["dest_ports"]))
               new_fw_rules.append(fwRule(name=name, origin_cidr=origin_cidr, dest_cidr=dest_cidr, action=action, active=active, loggin=loggin, protoPorts=new_proto_ports))
            
           edge_ser.login_in_dest()
           res=edge_ser.create_dest_firewall_rules(new_fw_rules, edge_id)
           if res.ok : 
               return jsonify({"Exito":res.data})
           else:
               return jsonify({"error":res.error}), 500
           
                   
    except Exception as e : 
        return jsonify({"error":str(e)}), 400
   
        

@bp.route("/createDestStaticRoutes", methods=["POST"])
@login_required
@handle_exceptions
def create_static_routes():
    keys_required=["static_routes", "edge_id"]
    static_route_keys_required=["name", "network_cidr", "next_hop_ip"]
    data=request.get_json()

    if all(key in request.get_json() for key in keys_required):
        static_routes=data["static_routes"]
        edge_id=data["edge_id"]
        new_static_routes=[]
        edge_serv=get_edge_migration(session.get("conf"))
        edge_serv.login_in_dest()
   
        for s in static_routes:
            if not all(key in s for key in static_route_keys_required):
                return jsonify({"error":"Faltan parametros en la regla", "data_recived":s, "required":static_route_keys_required}), 400
            else:
                name=s["name"]
                network_cidr=s["network_cidr"]
                next_hop_ip=s["next_hop_ip"]
                new_static_routes.append(staticRoute(name=name, network_cidr=network_cidr, next_hop_ip=next_hop_ip))
        res=edge_serv.create_dest_static_routes(new_static_routes, edge_id)
        if res.ok : 
            return jsonify({"exito":f"se crearon {len(res.data)}"})
        else:
            return jsonify({"error":res.error}), 500


    

@bp.route("/createDestNatRules", methods=["POST"])
@login_required
@handle_exceptions
def create_nat_rules():
    data=request.get_json()
    keys_required=["snat", "dnat", "vdc_id", "org_id", "edge_id"]
    dnat_keys_required=["name", "original_cidr", "translated_cidr", "external_port", "internal_port", "protocol", "prtiority", "active", "loggin"]
    snat_keys_required=["name", "original_cidr", "translated_cidr", "dest_cidr", "priority", "active", "loggin"]

    if all(key in data for key in keys_required):
        snat=data["snat"]
        dnat=data["dnat"]
        vdc_id=data["vdc_id"]
        org_id=data["org_id"]
        edge_id=data["edge_id"]
        
        edge_ser=get_edge_migration(session.get("conf"))
        edge_ser.login_in_dest()
        new_dnat=[]
        new_snat=[]
        for d in dnat : 
          if not all(key in d for key in dnat_keys_required):
              return jsonify({"error":"Faltan parametros en la regla", "data_recived":d, "required":dnat_keys_required}), 400
          else :
            active=d["active"]
            loggin=d["loggin"]
            name=d["name"]
            original_cidr=d["original_cidr"]
            translated_cidr=d["translated_cidr"]
            external_port=d["external_port"]
            internal_port=d["internal_port"]
            protocol=d["protocol"]
            priority=d["prtiority"]
            new_dnat.append(dnatRule(name=name,
                                     original_cidr=original_cidr, 
                                     translated_cidr=translated_cidr,
                                     external_port=external_port, 
                                     internal_port=internal_port,
                                     protocol=protocol,
                                     prtiority=priority, 
                                     active=active, 
                                     loggin=loggin))
            
        for s in snat:
         if not all(key in s for key in snat_keys_required):
            return jsonify({"error":"Faltan parametros en la regla", "data_recived":s, "required":snat_keys_required}), 400
         else :
            active=s["active"]
            loggin=s["loggin"]
            name=s["name"]
            original_cidr=s["original_cidr"]
            translated_cidr=s["translated_cidr"]
            dest_cidr=s["dest_cidr"]
            priority=s["priority"]
            new_snat.append(snatRule(name=name,
                                     original_cidr=original_cidr, 
                                     translated_cidr=translated_cidr,
                                     dest_cidr=dest_cidr, 
                                     priority=priority, 
                                     active=active, 
                                     loggin=loggin))
            
   
        creat_snat_res=edge_ser.create_dest_snat_rules(new_snat, edge_id)
        if creat_snat_res.ok : 
            create_dnat_res=edge_ser.create_dest_dnat_rules(edge_id,new_dnat, vdc_id, org_id)
            if create_dnat_res.ok : 
                return jsonify({"snat rules creadas:":len(new_snat), "dnat rules creadas:":len(new_dnat)})
            else:
                return jsonify({"error":create_dnat_res.error}), 500
        else:
            return jsonify({"error":creat_snat_res.error}), 500
        

    else : 
        return jsonify({"error":"Faltan parametros", "datos recibidos:":data, "required":keys_required}), 400
    
   

#######################FIN DESTINO #############################################################

