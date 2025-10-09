from functools import wraps
from flask import session, jsonify, request
from src.edge_migrator.domain.services.edge_migration import edgeMigration
from src.edge_migrator.shared.response import Response

def login_required(f):
    """Ensure that a user is logged in before accessing the route."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "conf" not in session:
            
            return jsonify({"error": "No se encontraron las credenciales o la session caduco"}), 401
        return f(*args, **kwargs)

    return decorated_function

def json_required(f):
    """Ensure that a user is logged in before accessing the route."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({"error": "no json detected"}), 400
        return f(*args, **kwargs)

    return decorated_function




def loginTest(edge:edgeMigration, conf) -> Response:
    """ Test login to edge with provided configuration."""
    log_origin=edge.login_in_origin()
    log_dest=edge.login_in_dest()
    log_nsxv=edge.login_in_nsxv()
    if not log_origin.ok:
        return Response(ok=False, error=f"Login fallido en VCD Origen: {log_origin.error}")
    if not log_dest.ok:
        return Response(ok=False, error=f"Login fallido en VCD Destino: {log_dest.error}")
    if not log_nsxv.ok:
        return Response(ok=False, error=f"Login fallido en NSX-V: {log_nsxv.error}")
    
    #Guardamos todos los datos en la session
    session["conf"]={}
    session["conf"]["VCD_XML_BASE"]=conf["VCD_XML_BASE"] 
    session["conf"]["VCD_XML_USER"]=conf ["VCD_XML_USER"] 
    session["conf"]["VCD_XML_ORG"]=conf["VCD_XML_ORG"] 
    session["conf"]["VCD_XML_PASS"]=conf["VCD_XML_PASS"] 
    session["conf"]["VCD_XML_VERSION"]=conf["VCD_XML_VERSION"] 
    session["conf"]["NSXV_BASE"]=conf["NSXV_BASE"] 
    session["conf"]["NSXV_USER"]=conf["NSXV_USER"] 
    session["conf"]["NSXV_PASS"]=conf["NSXV_PASS"] 
    session["conf"]["VCD_OPEN_BASE"]=conf["VCD_OPEN_BASE"] 
    session["conf"]["VCD_OPEN_USER"] = conf["VCD_OPEN_USER"] 
    session["conf"]["VCD_OPEN_ORG"]=conf["VCD_OPEN_ORG"] 
    session["conf"]["VCD_OPEN_PASS"]=conf["VCD_OPEN_PASS"] 
    session["conf"]["VCD_OPEN_VERSION"]=conf["VCD_OPEN_VERSION"]

    return Response(ok=True, data="Login exitoso en todas las api")

