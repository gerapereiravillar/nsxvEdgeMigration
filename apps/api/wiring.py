from src.edge_migrator.domain.services.edge_migration import edgeMigration
from src.edge_migrator.startup.composition_root import build_edge_service


def get_edge_migration(config)->edgeMigration:
  edge_ser=build_edge_service(config)
  return edge_ser
  