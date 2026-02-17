"""
Catalog API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import CommandModel, JobModel, WorkflowModel, DatasetModel, CatalogStatsModel
from app.catalog.catalog_service import CatalogService

router = APIRouter(prefix="/api/catalog", tags=["catalog"])
catalog_service = CatalogService()


@router.get("/commands", response_model=List[CommandModel])
async def get_commands():
    """Get all commands from catalog"""
    try:
        return catalog_service.get_all_commands()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[JobModel])
async def get_jobs():
    """Get all jobs from catalog"""
    try:
        return catalog_service.get_all_jobs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows", response_model=List[WorkflowModel])
async def get_workflows():
    """Get all workflows from catalog"""
    try:
        return catalog_service.get_all_workflows()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets", response_model=List[DatasetModel])
async def get_datasets():
    """Get all datasets from catalog"""
    try:
        return catalog_service.get_all_datasets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=CatalogStatsModel)
async def get_catalog_stats():
    """Get catalog statistics"""
    try:
        return catalog_service.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
