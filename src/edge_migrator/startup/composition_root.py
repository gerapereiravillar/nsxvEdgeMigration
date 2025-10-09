# startup/composition_root.py
from src.edge_migrator.infrastructure.vcloud_api.vcd_client_adapter_new import VcdApiAdapter
from src.edge_migrator.infrastructure.nsxV_api.nsxV_adapter_new import nsxvAdapter
from src.edge_migrator.infrastructure.vcloud_open_api.vcd_open_api_adapter_new import vCloudOpenApiAdap
from src.edge_migrator.domain.services.edge_migration import edgeMigration

def build_edge_service(cfg) -> edgeMigration:
    vcd_xml = VcdApiAdapter(
        base_url=cfg["VCD_XML_BASE"],
        user=cfg["VCD_XML_USER"],
        org=cfg["VCD_XML_ORG"],
        password=cfg["VCD_XML_PASS"],
        api_version=cfg.get("VCD_XML_VERSION", "36.2"),
    )

    nsxv = nsxvAdapter(
        base_url=cfg["NSXV_BASE"],
        user=cfg["NSXV_USER"],
        password=cfg["NSXV_PASS"],
    )

    vcd_open = vCloudOpenApiAdap(
        base_url=cfg["VCD_OPEN_BASE"],
        user=cfg["VCD_OPEN_USER"],
        org=cfg["VCD_OPEN_ORG"],
        password=cfg["VCD_OPEN_PASS"],
        api_version=cfg.get("VCD_OPEN_VERSION", "39.1"),
    )


    return edgeMigration (xml_api=vcd_xml, nsxv_api=nsxv, api_open=vcd_open)
