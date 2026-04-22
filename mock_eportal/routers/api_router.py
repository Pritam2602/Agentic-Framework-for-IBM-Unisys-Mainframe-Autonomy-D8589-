"""REST API endpoints for Unisys ePortal shopping data."""

from typing import Optional

from fastapi import APIRouter, Query

from mock_eportal.services import ShoppingService

router = APIRouter(prefix="/api/unisys", tags=["unisys-data"])

shopping_service = ShoppingService()


@router.get("/shopping")
async def get_shopping(
    customerId: Optional[int] = Query(None, description="Filter by customer ID"),
    date: Optional[str] = Query(None, description="Filter by shopping date (YYYY-MM-DD)"),
):
    """
    Retrieve Unisys shopping behavior data.

    ePortal is only a data provider. It does not combine IBM and Unisys data;
    federation belongs in the planner/execution/federation layer.
    """
    if customerId is not None and date:
        data = shopping_service.get_by_customer_id_and_date(str(customerId), date)
    elif customerId is not None:
        data = shopping_service.get_by_customer_id(str(customerId))
    elif date:
        data = shopping_service.get_by_date(date)
    else:
        data = shopping_service.get_all()

    return {
        "source": "unisys",
        "entity": "shopping",
        "count": len(data),
        "data": data,
    }


@router.get("/federation-metadata")
async def get_federation_metadata():
    """Return metadata that external federation layers can use."""
    return {
        "system": "unisys_eportal",
        "entities": {
            "shopping": {
                "count": len(shopping_service.get_all()),
                "fields": shopping_service.get_field_names(),
                "maps_to": "IBM transactions",
                "join_key": "customerId",
                "comparable_fields": {
                    "amount": "transactionAmount",
                    "date": "transactionDate",
                },
                "role": "behavioral_enrichment_provider",
            }
        },
    }
