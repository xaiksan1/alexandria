# cloud/cloud_catalog.py
"""Static cloud-services catalog — organic data source for CloudMCP.

No external API required. Keyword search against provider/name/tags.
Raise CloudCatalogError on any internal fault.
"""
from __future__ import annotations

_CATALOG: list[dict] = [
    {
        "id": "aws-ec2", "provider": "AWS", "name": "EC2 — Elastic Compute Cloud",
        "category": "compute", "price_from": "0.0116 USD/hr",
        "url": "https://aws.amazon.com/ec2/",
        "tags": ["ec2", "aws", "compute", "server", "vm", "instance"],
    },
    {
        "id": "aws-s3", "provider": "AWS", "name": "S3 — Simple Storage Service",
        "category": "storage", "price_from": "0.023 USD/GB/mo",
        "url": "https://aws.amazon.com/s3/",
        "tags": ["s3", "aws", "storage", "bucket", "object"],
    },
    {
        "id": "aws-lambda", "provider": "AWS", "name": "AWS Lambda",
        "category": "serverless", "price_from": "0.20 USD/1M reqs",
        "url": "https://aws.amazon.com/lambda/",
        "tags": ["lambda", "aws", "serverless", "function", "faas"],
    },
    {
        "id": "aws-rds", "provider": "AWS", "name": "RDS — Relational Database Service",
        "category": "database", "price_from": "0.017 USD/hr",
        "url": "https://aws.amazon.com/rds/",
        "tags": ["rds", "aws", "database", "postgres", "mysql", "sql"],
    },
    {
        "id": "gcp-gce", "provider": "GCP", "name": "Compute Engine",
        "category": "compute", "price_from": "0.010 USD/hr",
        "url": "https://cloud.google.com/compute",
        "tags": ["gce", "gcp", "google", "compute", "vm", "server", "instance"],
    },
    {
        "id": "gcp-gcs", "provider": "GCP", "name": "Cloud Storage",
        "category": "storage", "price_from": "0.020 USD/GB/mo",
        "url": "https://cloud.google.com/storage",
        "tags": ["gcs", "gcp", "google", "storage", "bucket", "object"],
    },
    {
        "id": "gcp-bigquery", "provider": "GCP", "name": "BigQuery",
        "category": "analytics", "price_from": "5.00 USD/TB",
        "url": "https://cloud.google.com/bigquery",
        "tags": ["bigquery", "bq", "gcp", "google", "analytics", "data", "warehouse", "sql"],
    },
    {
        "id": "gcp-run", "provider": "GCP", "name": "Cloud Run",
        "category": "serverless", "price_from": "0.00002400 USD/vCPU-s",
        "url": "https://cloud.google.com/run",
        "tags": ["cloud run", "gcp", "google", "serverless", "container", "faas"],
    },
    {
        "id": "azure-vm", "provider": "Azure", "name": "Virtual Machines",
        "category": "compute", "price_from": "0.013 USD/hr",
        "url": "https://azure.microsoft.com/products/virtual-machines",
        "tags": ["azure", "vm", "microsoft", "compute", "server", "instance"],
    },
    {
        "id": "azure-blob", "provider": "Azure", "name": "Blob Storage",
        "category": "storage", "price_from": "0.018 USD/GB/mo",
        "url": "https://azure.microsoft.com/products/storage/blobs",
        "tags": ["azure", "blob", "microsoft", "storage", "object"],
    },
    {
        "id": "azure-functions", "provider": "Azure", "name": "Azure Functions",
        "category": "serverless", "price_from": "0.20 USD/1M reqs",
        "url": "https://azure.microsoft.com/products/functions",
        "tags": ["azure", "functions", "microsoft", "serverless", "faas"],
    },
    {
        "id": "do-droplets", "provider": "DigitalOcean", "name": "Droplets",
        "category": "compute", "price_from": "4.00 USD/mo",
        "url": "https://www.digitalocean.com/products/droplets",
        "tags": ["digitalocean", "do", "droplet", "compute", "vps", "server"],
    },
    {
        "id": "hetzner-cx", "provider": "Hetzner", "name": "Cloud Servers (CX line)",
        "category": "compute", "price_from": "3.29 EUR/mo",
        "url": "https://www.hetzner.com/cloud",
        "tags": ["hetzner", "cloud", "compute", "vps", "server", "cheap"],
    },
    {
        "id": "cf-workers", "provider": "Cloudflare", "name": "Workers",
        "category": "serverless", "price_from": "0.00 USD (100k req/day free)",
        "url": "https://workers.cloudflare.com/",
        "tags": ["cloudflare", "workers", "serverless", "edge", "faas", "cdn"],
    },
    {
        "id": "fly-machines", "provider": "Fly.io", "name": "Fly Machines",
        "category": "compute", "price_from": "0.0000019 USD/vCPU-s",
        "url": "https://fly.io/",
        "tags": ["fly", "fly.io", "compute", "container", "deploy", "edge"],
    },
]


class CloudCatalogError(Exception):
    """Raised on any catalog fault (should not occur with static data)."""


class CloudCatalogClient:
    """In-memory cloud services catalog — no HTTP, no rate limits.

    search() does case-insensitive substring matching against name, provider, and tags.
    aclose() is a no-op (no HTTP client to release).
    """

    async def search(self, query: str) -> list[dict]:
        """Return catalog items whose name, provider, or tags contain any query token."""
        tokens = query.lower().split()
        results = []
        for item in _CATALOG:
            haystack = (
                item["name"].lower()
                + " " + item["provider"].lower()
                + " " + " ".join(item["tags"])
            )
            if any(tok in haystack for tok in tokens):
                results.append(item)
        return results

    async def aclose(self) -> None:
        pass
