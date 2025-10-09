import os, requests
from xml.etree import ElementTree as ET

class nsxvAdapter:
    def __init__(self, base_url: str, user: str, password: str):
        self.base = base_url.rstrip("/")
        self.user = user
        self.pw = password
        self.session = requests.Session()
        self.session.verify = False

    def _h(self):
        return {"Accept": "application/xml"}



    def _get_edge_xml(self, edge_id: str):
        url = f"{self.base}/api/4.0/edges/{edge_id}"
        r = self.session.get(url, headers=self._h(),auth=(self.user, self.pw))
        if r.status_code == 200:
            return {"success": ET.fromstring(r.content)}
        else:
            return {"error": f"{r.status_code} {r.reason} {r.text}"}

    def get_vnics(self, edge_id: str) -> list[dict]:
        """Retorna la lista de vnics y la subred a la cual están conectadas.
        Args: edge_id (str) Obligatorio
        Returns: vnics_list ([{"vnic-index":"net_CIDR_FORMAT"}])
        EJEMPLO DE SALIDA: [{"vnic-0":"192.168.0.1/24"}, {"vnic-1":"192.168.0.2/24"}]
        """
        vnics_list = []
    
        # Realizar la petición GET para obtener el XML del edge
    
        edge_xml = self._get_edge_xml(edge_id)
        if "success" in edge_xml : 
            edge_xml=edge_xml["success"]
        else:
            return {"error": edge_xml["error"]}
    
        # Buscar todos los elementos vnic en el XML
        # El namespace para este XML de NSX es diferente o no tiene namespace
        vnics = edge_xml.findall('.//vnic')
    
        for vnic in vnics:
            # Obtener el índice de la vnic
            index_elem = vnic.find('index')
            if index_elem is None or index_elem.text is None:
                continue
            
            vnic_index = index_elem.text.strip()
        
            # Verificar si la vnic está conectada
            is_connected_elem = vnic.find('isConnected')
            if is_connected_elem is not None and is_connected_elem.text == 'false':
                # Si no está conectada, podríamos omitirla o agregar sin IP
                continue
        
        # Buscar addressGroups para obtener las IPs
            address_groups = vnic.find('addressGroups')
            if address_groups is None:
                continue
            
            # Procesar cada addressGroup
            for address_group in address_groups.findall('addressGroup'):
                # Obtener la dirección IP primaria
                primary_address_elem = address_group.find('primaryAddress')
                if primary_address_elem is None or primary_address_elem.text is None:
                   continue
                
                primary_address = primary_address_elem.text.strip()
            
                # Obtener la longitud del prefijo de subred
                prefix_length_elem = address_group.find('subnetPrefixLength')
                if prefix_length_elem is not None and prefix_length_elem.text:
                    prefix_length = prefix_length_elem.text.strip()
                else:
                    # Si no hay prefix length, intentar calcular desde netmask
                    netmask_elem = address_group.find('subnetMask')
                    if netmask_elem is not None and netmask_elem.text:
                        netmask = netmask_elem.text.strip()
                        prefix_length = self._netmask_to_prefix_length(netmask)
                    else:
                    # Si no hay información de subred, usar /32 por defecto
                        prefix_length = '32'
            
                # Construir la notación CIDR
                cidr = f"{primary_address}/{prefix_length}"
            
                # Agregar a la lista como diccionario
                vnic_dict = {f"vnic-{vnic_index}": cidr}
                vnics_list.append(vnic_dict)
            
                # También procesar direcciones secundarias si existen
                secondary_addresses = address_group.find('secondaryAddresses')
                if secondary_addresses is not None:
                   for ip_elem in secondary_addresses.findall('ipAddress'):
                        if ip_elem.text:
                            secondary_ip = ip_elem.text.strip()
                            secondary_cidr = f"{secondary_ip}/{prefix_length}"
                            secondary_dict = {f"vnic-{vnic_index}": secondary_cidr}
                            vnics_list.append(secondary_dict)
    
        return {"success":vnics_list}


    def _netmask_to_prefix_length(self, netmask: str) -> str:
        """Convert netmask to prefix length (e.g., 255.255.255.0 -> 24)"""
        try:
            # Convertir la máscara de red a entero binario y contar los bits en 1
            binary_str = ''
            for octet in netmask.split('.'):
                binary_str += bin(int(octet))[2:].zfill(8)
            return str(binary_str.count('1'))
        except:
            return '32'  # Valor por defecto si hay error
    
    def get_nat_rules(self, edge_id: str)->list[dict]:
        """Recibe la config del edge o T1 ontenida desde la api de VCD y devuelve las reglas de nat: 
        Args: edge_id (str) obligatorio
        Return: nat_list (list[dict])
             por cada regla         
             {"ruleTag":str|None,
             "loggingEnabled":str|None,
             "enabled":str|None,
             "description":str|None, 
             "translatedAddress":str|None
            , "action":str|None,
              "originalAddress":str|None, 
            "snatMatchDestinationAddress":str|None, 
             "protocol":str|None, 
             "originalPort":str|None,
             "translatedPort":str|None , 
            "snatMatchDestinationPort":str|None}"""       
        
        url = f"{self.base}/api/4.0/edges/{edge_id}/nat/config"
        r = self.session.get(url, headers=self._h(),auth=(self.user, self.pw))
        if r.status_code == 200:
            root= ET.fromstring(r.content)
            nat_list=[]
            for rule in root.findall('.//natRule'):
                #Obtener info general 
                ruleTag=rule.find("ruleTag")
                loggingEnabled=rule.find("loggingEnabled")
                enabled=rule.find("enabled")
                description=rule.find("description")
                translatedAddress=rule.find("translatedAddress")
                action=rule.find("action")
                originalAddress=rule.find("originalAddress")
                snatMatchDestinationAddress=rule.find("snatMatchDestinationAddress")
                protocol=rule.find("protocol")
                originalPort=rule.find("originalPort")
                translatedPort=rule.find("translatedPort")
                snatMatchDestinationPort=rule.find("snatMatchDestinationPort")

                
                item={"ruleTag":ruleTag.text if ruleTag is not None else None,
                      "loggingEnabled":loggingEnabled.text if loggingEnabled is not  None else None,
                      "enabled":enabled.text if enabled is not  None else None,
                      "description":description.text if description is not None else None,
                      "translatedAddress":translatedAddress.text if translatedAddress is not None else None,
                      "action":action.text if action is not None else None,
                      "originalAddress":originalAddress.text if originalAddress is not  None else None, 
                      "snatMatchDestinationAddress":snatMatchDestinationAddress.text if snatMatchDestinationAddress is not None else None, 
                      "protocol":protocol.text if protocol is not None else None,
                       "originalPort":originalPort.text if originalPort is not None else None, 
                      "translatedPort":translatedPort.text if translatedPort is not None else None, 
                      "snatMatchDestinationPort":snatMatchDestinationPort.text if snatMatchDestinationPort is not None else None}
                nat_list.append(item)
                    

                    
            return {"success":nat_list}

        else:
            return {"error": f"{r.status_code} {r.reason} {r.text}"}                
                               
    