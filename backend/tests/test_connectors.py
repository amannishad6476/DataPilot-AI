import pytest
from app.services.connectors.registry import connector_registry
from app.services.connectors.base import FetchRequest, RawFetchedDocument
from app.services.connectors.public_webpage import PublicWebPageConnector
from app.services.connectors.n8n_connector import N8nWebhookConnector


def test_connector_registry():
    connectors = connector_registry.list_all()
    assert len(connectors) >= 3

    ids = [c.connector_id for c in connectors]
    assert "public_webpage" in ids
    assert "json_feed" in ids
    assert "n8n_webhook" in ids

    # Retrieve individual connector
    web = connector_registry.get("public_webpage")
    assert web is not None
    assert web.name == "Public Web Page & Portal Connector"


def test_public_webpage_domain_security():
    conn = PublicWebPageConnector()
    conn.allowed_domains = ["upciti.gov.in", "nasscom.in", "tcs.com"]

    # Permitted domains
    assert conn.is_domain_permitted("https://upciti.gov.in/portal") is True
    assert conn.is_domain_permitted("https://sub.nasscom.in/members") is True

    # Blocked unpermitted domain
    assert conn.is_domain_permitted("https://malicious-external-site.com") is False

    # Blocked private/internal IPs to prevent SSRF
    assert conn.is_domain_permitted("http://localhost:8000") is False
    assert conn.is_domain_permitted("http://127.0.0.1:8000") is False
    assert conn.is_domain_permitted("http://192.168.1.1/admin") is False
    assert conn.is_domain_permitted("http://10.0.0.1/internal") is False


@pytest.mark.asyncio
async def test_public_webpage_extraction():
    conn = PublicWebPageConnector()

    html_content = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>TechCorp Lucknow - Software Engineering Hub</title>
        <meta name="description" content="Leading IT services and digital transformation provider in Gomti Nagar, Lucknow.">
        <meta property="og:site_name" content="TechCorp India">
      </head>
      <body>
        <h1>Welcome to TechCorp</h1>
        <p>Contact our university partnerships desk at campus.outreach@techcorp.in or call +91 522 456 7890.</p>
        <p>Located at Vibhuti Khand, Lucknow, Uttar Pradesh.</p>
      </body>
    </html>
    """

    doc = RawFetchedDocument(
        source_id="public_webpage",
        source_url="https://techcorp.in/lucknow",
        content=html_content,
        content_type="text/html",
        status_code=200,
        extracted_metadata={
            "title": "TechCorp Lucknow - Software Engineering Hub",
            "description": "Leading IT services and digital transformation provider in Gomti Nagar, Lucknow.",
            "og_site_name": "TechCorp India"
        }
    )

    fields = ["company_name", "website", "public_business_email", "phone", "location", "industry"]
    records = await conn.extract_records(doc, fields)

    assert len(records) == 1
    rec = records[0]
    assert rec["company_name"] == "TechCorp India"
    assert rec["website"] == "https://techcorp.in/lucknow"
    assert rec["public_business_email"] == "campus.outreach@techcorp.in"
    assert "522" in rec["phone"]
    assert "Lucknow" in rec["location"]


def test_n8n_template_generation():
    template = N8nWebhookConnector.generate_n8n_template()
    assert "nodes" in template
    assert len(template["nodes"]) >= 2
    assert template["nodes"][0]["type"] == "n8n-nodes-base.webhook"
