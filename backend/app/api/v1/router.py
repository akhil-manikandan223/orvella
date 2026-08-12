from fastapi import APIRouter

from app.api.v1.routes import (
    audit_logs,
    auth,
    cities,
    countries,
    districts,
    features,
    organization_categories,
    organization_types,
    states,
    tenants,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(audit_logs.router)
api_router.include_router(cities.router)
api_router.include_router(countries.router)
api_router.include_router(districts.router)
api_router.include_router(features.router)
api_router.include_router(organization_categories.router)
api_router.include_router(organization_types.router)
api_router.include_router(states.router)
api_router.include_router(tenants.router)
