"""
Catalog Service - Business logic layer
"""

from app.repository.catalog_repository import CatalogRepository


class CatalogService:

    def __init__(self):
        self.repository = CatalogRepository()

    # =========================================================
    # COMMANDS
    # =========================================================

    def get_all_commands(self):
        return self.repository.get_all_commands()

    # =========================================================
    # JOBS
    # =========================================================

    def get_all_jobs(self):
        return self.repository.get_all_jobs()

    # =========================================================
    # WORKFLOWS
    # =========================================================

    def get_all_workflows(self):
        return self.repository.get_all_workflows()

    # =========================================================
    # DATASETS
    # =========================================================

    def get_all_datasets(self):
        return self.repository.get_all_datasets()

    # =========================================================
    # STATS
    # =========================================================

    def get_statistics(self):
        return self.repository.get_catalog_stats()
