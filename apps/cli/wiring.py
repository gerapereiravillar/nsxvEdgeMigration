from edge_migrator.infrastructure.vcloud_api.vcd_client_adapter import VcdApiAdapter
from edge_migrator.domain.services.edge_migration import export_edge_xml as export_uc

def export_edge_xml_usecase():
    vcd = VcdApiAdapter.from_env()
    return lambda org, edge: export_uc(vcd, org, edge)
