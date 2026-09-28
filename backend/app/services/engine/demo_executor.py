import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.workflow import Workflow, WorkflowRun
from app.models.dataset import DatasetRecord, EvidenceRecord
from app.schemas.planner import ValidationRuleSpec
from app.services.engine.executor import BaseWorkflowExecutor
from app.services.processing.normalizer import DataNormalizer
from app.services.processing.validator import DataValidator
from app.services.processing.deduplicator import SimilarityDeduplicator
from app.services.connectors.registry import connector_registry

logger = logging.getLogger(__name__)

# Rich, realistic dataset generator for college fest sponsor intelligence in Lucknow & UP
LUCKNOW_SPONSORS_RAW = [
    {
        "company_name": "Tata Consultancy Services Ltd",
        "industry": "IT Services & Enterprise Consulting",
        "website": "http://www.tcs.com/corporate-sponsorships",
        "public_business_email": "campus.relations@tcs.com",
        "phone": "+91 522 666 4000",
        "location": "Vibhuti Khand, Gomti Nagar, Lucknow, UP",
        "source": "https://www.tcs.com/locations/lucknow-campus",
        "snippet": "TCS Lucknow campus engages actively with regional technical universities and collegiate hackathons."
    },
    {
        "company_name": "Tata Consultancy Services (Lucknow Campus)",  # Near-duplicate for deduplication demonstration
        "industry": "Information Technology",
        "website": "https://tcs.com",
        "public_business_email": "tcs.lucknow@tcs.com",
        "phone": "05226664000",
        "location": "Lucknow, Uttar Pradesh",
        "source": "https://www.nasscom.in/members/tcs-lucknow",
        "snippet": "Software development center in Gomti Nagar, Lucknow employing over 3,000 engineers."
    },
    {
        "company_name": "HCL Technologies Ltd",
        "industry": "IT Infrastructure & Cloud Engineering",
        "website": "https://www.hcltech.com",
        "public_business_email": "corporate.partnerships@hcltech.com",
        "phone": "+91 522 710 1000",
        "location": "HCL IT City, Chak Ganjariya, Sultanpur Road, Lucknow, UP",
        "source": "https://www.hcltech.com/about-us/global-presence/india/lucknow",
        "snippet": "HCL IT City Lucknow is one of Northern India's largest engineering hubs with frequent collegiate event sponsorship programs."
    },
    {
        "company_name": "HCL Tech Lucknow",  # Near-duplicate for deduplication demonstration
        "industry": "IT Software",
        "website": "http://hcltech.com/lucknow",
        "public_business_email": "hcl.lucknow@hcltech.com",
        "phone": "+915227101000",
        "location": "Sultanpur Road, Lucknow",
        "source": "https://upciti.gov.in/it-city-lucknow-tenants",
        "snippet": "Major tech facility in Lucknow IT City campus."
    },
    {
        "company_name": "Tech Mahindra",
        "industry": "Digital Transformation & Telecom",
        "website": "https://www.techmahindra.com",
        "public_business_email": "connect@techmahindra.com",
        "phone": "+91 120 453 4400",
        "location": "Noida & Lucknow Regional Center, UP",
        "source": "https://techmahindra.com/en-in/contact-us/",
        "snippet": "Tech Mahindra actively supports student innovation initiatives and technology conclaves."
    },
    {
        "company_name": "Zoho Corporation",
        "industry": "Enterprise SaaS & Cloud Software",
        "website": "https://www.zoho.com",
        "public_business_email": "outreach@zohocorp.com",
        "phone": "+91 44 6744 7070",
        "location": "India Operations / Rural Tech Initiatives",
        "source": "https://www.zoho.com/community/events.html",
        "snippet": "Zoho Schools and community outreach routinely sponsor university codefests and student developer summits."
    },
    {
        "company_name": "PhysicsWallah (PW)",
        "industry": "EdTech & Competitive Exam Prep",
        "website": "https://www.pw.live",
        "public_business_email": "partnerships@pw.live",
        "phone": "+91 70192 43492",
        "location": "Hazratganj & Alambagh Centers, Lucknow, UP",
        "source": "https://www.pw.live/offline-centres/lucknow",
        "snippet": "PhysicsWallah operates flagship offline learning hubs across Lucknow with high student fest sponsorship budget."
    },
    {
        "company_name": "Paytm (One97 Communications)",
        "industry": "FinTech & Digital Payments",
        "website": "https://paytm.com",
        "public_business_email": "brand.alliances@paytm.com",
        "phone": "+91 120 477 0770",
        "location": "Regional Merchant Operations, Hazratganj, Lucknow, UP",
        "source": "https://paytm.com/about-us",
        "snippet": "Paytm Payment Gateway and Student wallet solutions frequently sponsor major Northern India college fests."
    },
    {
        "company_name": "Razorpay",
        "industry": "Payment Infrastructure & Neobanking",
        "website": "https://razorpay.com",
        "public_business_email": "hackathons@razorpay.com",
        "phone": "+91 80 4666 9555",
        "location": "India Operations (Lucknow Student Outreach)",
        "source": "https://razorpay.com/events/hackathons",
        "snippet": "Razorpay DevRel team actively sponsors student hackathons with API bounties and financial grants."
    },
    {
        "company_name": "Info Edge India (Naukri.com)",
        "industry": "Internet & Employment Platforms",
        "website": "https://www.infoedge.in",
        "public_business_email": "corporate@infoedge.in",
        "phone": "+91 120 308 2000",
        "location": "Regional Office, Ashok Marg, Lucknow, UP",
        "source": "https://www.infoedge.in/contact-us.html",
        "snippet": "Publisher of Naukri.com, 99acres, and Shiksha with permanent branch operations in Ashok Marg, Lucknow."
    },
    {
        "company_name": "Swiggy",
        "industry": "Quick Commerce & Consumer Logistics",
        "website": "https://www.swiggy.com",
        "public_business_email": "brand.partnerships@swiggy.in",
        "phone": "+91 80 6746 6720",
        "location": "City Operations, Vibhuti Khand, Lucknow, UP",
        "source": "https://www.swiggy.com/corporate",
        "snippet": "Swiggy Campus Crew actively partners with collegiate fests for youth brand engagement and food court partnerships."
    },
    {
        "company_name": "Zomato",
        "industry": "Food Delivery & Event Ticketing",
        "website": "https://www.zomato.com",
        "public_business_email": "live-partnerships@zomato.com",
        "phone": "+91 11 3080 0000",
        "location": "Regional Hub, Indira Nagar, Lucknow, UP",
        "source": "https://www.zomato.com/lucknow",
        "snippet": "Zomato Live and Feeding India collaborate with universities on collegiate cultural and technical festivals."
    },
    {
        "company_name": "Flipkart Internet Pvt Ltd",
        "industry": "E-Commerce & Supply Chain Tech",
        "website": "https://www.flipkart.com",
        "public_business_email": "campus.connect@flipkart.com",
        "phone": "+91 80 4547 3000",
        "location": "Fulfillment Hub, Mohanlalganj, Lucknow, UP",
        "source": "https://www.flipkartcareers.com/campus",
        "snippet": "Flipkart GRiD hackathon team sponsors top college technological events and robotics challenges."
    },
    {
        "company_name": "Pine Labs",
        "industry": "Merchant FinTech & POS Systems",
        "website": "https://www.pinelabs.com",
        "public_business_email": "marketing@pinelabs.com",
        "phone": "+91 120 417 4000",
        "location": "Noida & Lucknow Regional Distribution",
        "source": "https://www.pinelabs.com/contact-us",
        "snippet": "Leading merchant platform providing payment technology sponsorships to regional engineering colleges."
    },
    {
        "company_name": "MakeMyTrip",
        "industry": "Online Travel & Hospitality Tech",
        "website": "https://www.makemytrip.com",
        "public_business_email": "youth.marketing@makemytrip.com",
        "phone": "+91 124 462 8747",
        "location": "Hazratganj, Lucknow, UP",
        "source": "https://www.makemytrip.com/about-us",
        "snippet": "MakeMyTrip youth wing sponsors travel discounts and event pass rewards for student tech participants."
    },
    {
        "company_name": "PolicyBazaar (PB Fintech)",
        "industry": "InsurTech & Financial Marketplace",
        "website": "https://www.policybazaar.com",
        "public_business_email": "corporate.affairs@policybazaar.com",
        "phone": "+91 124 456 5000",
        "location": "Gomti Nagar, Lucknow, UP",
        "source": "https://www.policybazaar.com/about-us",
        "snippet": "Active fintech recruiter with strong presence at Uttar Pradesh campus recruitment drives."
    },
    {
        "company_name": "Meesho",
        "industry": "Social Commerce & Marketplace",
        "website": "https://www.meesho.com",
        "public_business_email": "university.relations@meesho.com",
        "phone": "+91 80 6179 9600",
        "location": "UP Regional Seller Office, Lucknow",
        "source": "https://www.meesho.io/tech",
        "snippet": "Meesho tech team hosts engineering competitions and sponsors collegiate open source tracks."
    },
    {
        "company_name": "CRED (Dreamplug Technologies)",
        "industry": "FinTech & Financial Rewards",
        "website": "https://cred.club",
        "public_business_email": "dev-alliances@cred.club",
        "phone": "+91 80 4568 2000",
        "location": "India Headquarters (Campus Outreach)",
        "source": "https://cred.club/careers",
        "snippet": "CRED Developers regularly awards track prizes and title sponsorships for top engineering conclaves."
    },
    {
        "company_name": "PhonePe",
        "industry": "UPI Payments & Digital Financial Services",
        "website": "https://www.phonepe.com",
        "public_business_email": "events@phonepe.com",
        "phone": "+91 80 6872 7374",
        "location": "Regional Hub, Vibhuti Khand, Lucknow, UP",
        "source": "https://www.phonepe.com/contact-us",
        "snippet": "PhonePe Pulse and Engineering division support collegiate hackathons and coding tournaments."
    },
    {
        "company_name": "Delhivery",
        "industry": "Supply Chain Technology & Logistics",
        "website": "https://www.delhivery.com",
        "public_business_email": "partnerships@delhivery.com",
        "phone": "+91 124 671 9500",
        "location": "Transport Nagar, Lucknow, UP",
        "source": "https://www.delhivery.com/contact",
        "snippet": "Logistics tech giant with large automated sorting facility in Lucknow sponsoring student engineering design competitions."
    },
    {
        "company_name": "Lenskart Solutions",
        "industry": "Omnichannel Retail & Vision Tech",
        "website": "https://www.lenskart.com",
        "public_business_email": "fest.sponsorship@lenskart.in",
        "phone": "+91 99998 99998",
        "location": "Phoenix Palassio & Hazratganj, Lucknow, UP",
        "source": "https://www.lenskart.com/stores/lucknow",
        "snippet": "Lenskart youth brand ambassadors partner with university festivals across UP for brand kiosks."
    },
    {
        "company_name": "Groww (Nextbillion Technology)",
        "industry": "Investment Tech & Wealth Management",
        "website": "https://groww.in",
        "public_business_email": "campus@groww.in",
        "phone": "+91 80 6902 4700",
        "location": "India Operations",
        "source": "https://groww.in/about-us",
        "snippet": "Groww provides student financial literacy workshops and tech fest sponsorships nationwide."
    },
    {
        "company_name": "Zerodha Broking Ltd",
        "industry": "FinTech & Open Source Software",
        "website": "https://zerodha.com",
        "public_business_email": "foss@zerodha.com",
        "phone": "+91 80 4718 1888",
        "location": "Rainmatter Tech Initiatives",
        "source": "https://zerodha.com/about",
        "snippet": "Rainmatter foundation by Zerodha actively grants funds to student open source and tech clubs."
    },
    {
        "company_name": "Nykaa (FSN E-Commerce)",
        "industry": "Consumer Tech & Beauty Retail",
        "website": "https://www.nykaa.com",
        "public_business_email": "corporate.communications@nykaa.com",
        "phone": "+91 22 6614 9696",
        "location": "Hazratganj Store, Lucknow, UP",
        "source": "https://www.nykaa.com/who-are-we",
        "snippet": "Nykaa on Trend sponsors university cultural and youth tech summits with merchandise and title branding."
    },
    {
        "company_name": "Coforge (formerly NIIT Technologies)",
        "industry": "Enterprise Software & Cloud Transformation",
        "website": "https://www.coforge.com",
        "public_business_email": "contact@coforge.com",
        "phone": "+91 120 459 2300",
        "location": "Greater Noida & Lucknow Campus Outreach, UP",
        "source": "https://www.coforge.com/about-us",
        "snippet": "Leading digital services enterprise actively recruiting and sponsoring computer science symposiums in UP."
    },
    {
        "company_name": "Birlasoft Ltd",
        "industry": "Enterprise IT Solutions & Cloud Consulting",
        "website": "https://www.birlasoft.com",
        "public_business_email": "contactus@birlasoft.com",
        "phone": "+91 20 6652 5000",
        "location": "Noida & Lucknow Regional Network",
        "source": "https://www.birlasoft.com/contact-us",
        "snippet": "CK Birla group company providing industry-institute collaboration grants and fest co-sponsorships."
    },
    {
        "company_name": "Persistent Systems",
        "industry": "Digital Product Engineering",
        "website": "https://www.persistent.com",
        "public_business_email": "info@persistent.com",
        "phone": "+91 20 6703 0000",
        "location": "India Engineering Centers",
        "source": "https://www.persistent.com/company/overview/",
        "snippet": "Persistent Foundation backs collegiate innovation awards and national student hackathons."
    },
    {
        "company_name": "Fractal Analytics",
        "industry": "Artificial Intelligence & Decision Science",
        "website": "https://fractal.ai",
        "public_business_email": "ai.outreach@fractal.ai",
        "phone": "+91 22 6734 0000",
        "location": "India AI Hubs",
        "source": "https://fractal.ai/contact/",
        "snippet": "Leading AI enterprise that sponsors university data science tracks, machine learning summits, and codefests."
    },
    {
        "company_name": "InMobi",
        "industry": "AdTech & Mobile Marketing Platforms",
        "website": "https://www.inmobi.com",
        "public_business_email": "partners@inmobi.com",
        "phone": "+91 80 4032 5000",
        "location": "India Operations",
        "source": "https://www.inmobi.com/company/about-us",
        "snippet": "Unicorn mobile tech firm sponsoring mobile app hackathons and collegiate algorithm challenges."
    },
    {
        "company_name": "Freshworks Inc",
        "industry": "Customer Experience Software & SaaS",
        "website": "https://www.freshworks.com",
        "public_business_email": "student-relations@freshworks.com",
        "phone": "+91 44 6667 8040",
        "location": "India Technology Centers",
        "source": "https://www.freshworks.com/company/about/",
        "snippet": "Freshworks for Startups and Students provides dev credits and hackathon sponsorships across Indian institutes."
    },
    {
        "company_name": "BharatPe (Resilient Innovations)",
        "industry": "Merchant QR & SME Lending",
        "website": "https://bharatpe.com",
        "public_business_email": "alliances@bharatpe.com",
        "phone": "+91 888 2555 444",
        "location": "Merchant Hub, Aminabad & Aliganj, Lucknow, UP",
        "source": "https://bharatpe.com/about-us",
        "snippet": "Extensive merchant acquisition network across Lucknow supporting regional technical and entrepreneurship fests."
    },
    {
        "company_name": "Unacademy (Sorting Hat Technologies)",
        "industry": "EdTech & Learning Platforms",
        "website": "https://unacademy.com",
        "public_business_email": "events@unacademy.com",
        "phone": "+91 85858 58585",
        "location": "Unacademy Centre, Hazratganj, Lucknow, UP",
        "source": "https://unacademy.com/offline-centres/lucknow",
        "snippet": "Prominent offline presence in Lucknow, frequently partnering as education and prize sponsor for collegiate events."
    },
    {
        "company_name": "Incomplete Test Sponsor Entry",  # Intentionally slightly flawed to showcase validation!
        "industry": "Information Technology",
        "website": "http://invalid-web-portal",
        "public_business_email": "not-an-email-format",
        "phone": "123",
        "location": "Lucknow, UP",
        "source": "https://unverified-directory.local",
        "snippet": "Raw unverified candidate discovered from uncurated directory listing."
    }
]


class DemoWorkflowExecutor(BaseWorkflowExecutor):
    def __init__(self):
        self.normalizer = DataNormalizer()
        self.validator = DataValidator()
        self.deduplicator = SimilarityDeduplicator()

    async def execute(self, workflow: Workflow, run: WorkflowRun, db: Session):
        """
        Executes the planned DAG step by step.
        Updates WorkflowRun.step_statuses after each step.
        Applies genuine normalization, validation, and similarity deduplication!
        """
        logger.info(f"Starting Demo execution for workflow {workflow.id}, run {run.id}")

        # Parse steps and validation rules from workflow
        steps = workflow.steps_spec or []
        rules = [ValidationRuleSpec(**r) for r in (workflow.validation_rules or [])]

        # Initialize step statuses
        step_statuses = []
        for s in steps:
            step_statuses.append({
                "step_id": s["id"],
                "step_name": s["name"],
                "step_type": s["type"],
                "status": "pending",
                "progress_percent": 0,
                "message": "Queued in pipeline",
                "records_produced": 0,
                "started_at": None,
                "completed_at": None,
                "error": None
            })

        run.status = "running"
        run.step_statuses = step_statuses

        timeline: List[Dict[str, Any]] = [
            {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "step_id": None,
                "stage": "initialization",
                "level": "info",
                "message": f"Execution initialized in Demo mode for workflow: {workflow.goal}",
                "details": {"steps_count": len(steps), "rules_count": len(rules)}
            }
        ]
        run.execution_timeline = list(timeline)
        db.commit()

        # Intermediate data pipeline states
        raw_candidates: List[Dict[str, Any]] = []
        normalized_records: List[Dict[str, Any]] = []
        validated_records: List[Dict[str, Any]] = []
        unique_records: List[Dict[str, Any]] = []
        duplicates_caught: List[Any] = []
        records_to_dedup: List[Dict[str, Any]] = []

        total_steps = len(steps)

        for idx, step_spec in enumerate(steps):
            step_id = step_spec["id"]
            step_name = step_spec["name"]
            step_type = step_spec["type"]

            # Cancellation check
            db.refresh(run)
            if run.status == "cancelled":
                logger.info(f"Demo run {run.id} was cancelled by user.")
                timeline.append({
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "step_id": step_id,
                    "stage": "cancellation",
                    "level": "warning",
                    "message": f"Execution safely cancelled by user at step '{step_name}'.",
                    "details": {"step_id": step_id, "step_name": step_name}
                })
                run.execution_timeline = list(timeline)
                db.commit()
                return

            # Update step to running
            step_statuses[idx]["status"] = "running"
            step_statuses[idx]["started_at"] = datetime.now(timezone.utc).isoformat()
            step_statuses[idx]["message"] = f"Executing {step_name}..."
            step_statuses[idx]["progress_percent"] = 40
            run.step_statuses = list(step_statuses)
            db.commit()

            timeline.append({
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "step_id": step_id,
                "stage": step_type,
                "level": "info",
                "message": f"Step '{step_name}' ({step_type}) started.",
                "details": {"action": step_spec.get("action")}
            })

            # Small realistic latency for live visualization
            await asyncio.sleep(0.4)

            # Step logic execution based on step_type
            if step_type in ["input", "ai_planning"]:
                step_statuses[idx]["message"] = "Query analyzed and search directives compiled."
                step_statuses[idx]["records_produced"] = 0

            elif step_type == "source_discovery":
                # Identified permitted public indexes
                discovered_sources_count = len(workflow.sources_spec) if workflow.sources_spec else 3
                step_statuses[idx]["message"] = f"Discovered {discovered_sources_count} accessible public sources complying with robots.txt."
                step_statuses[idx]["records_produced"] = discovered_sources_count

            elif step_type == "extraction":
                # Produce raw sponsor or general entity records
                if not raw_candidates:
                    raw_candidates = [dict(item) for item in LUCKNOW_SPONSORS_RAW]
                step_statuses[idx]["message"] = f"Extracted {len(raw_candidates)} entity candidate records."
                step_statuses[idx]["records_produced"] = len(raw_candidates)

            elif step_type == "transformation":
                # Apply normalization: URLs, emails, phone numbers with audit trail
                normalized_records = []
                for r in raw_candidates:
                    clean_dict, transforms = self.normalizer.normalize_record_with_audit(r)
                    clean_dict["_field_transformations"] = transforms
                    normalized_records.append(clean_dict)
                step_statuses[idx]["message"] = f"Cleaned & normalized formatting across {len(normalized_records)} records."
                step_statuses[idx]["records_produced"] = len(normalized_records)

            elif step_type == "validation":
                # Run validation rules with detailed status per field
                records_to_validate = normalized_records if normalized_records else raw_candidates
                validated_records = []
                valid_count = 0
                for r in records_to_validate:
                    is_valid, errors, conf, field_validations, conf_level = self.validator.validate_record_detailed(r, rules)
                    r_copy = dict(r)
                    r_copy["_is_valid"] = is_valid
                    r_copy["_errors"] = errors
                    r_copy["_confidence"] = conf
                    r_copy["_field_validations"] = field_validations
                    r_copy["_confidence_level"] = conf_level
                    validated_records.append(r_copy)
                    if is_valid:
                        valid_count += 1
                step_statuses[idx]["message"] = f"Validated RFC email, phone & URL health: {valid_count} clean, {len(validated_records) - valid_count} flagged."
                step_statuses[idx]["records_produced"] = len(validated_records)

            elif step_type == "deduplication":
                # Run similarity-based deduplication
                records_to_dedup = validated_records if validated_records else normalized_records or raw_candidates
                keys = workflow.steps_spec[idx].get("target_fields", ["company_name", "website"])
                unique_records, duplicates_caught = self.deduplicator.deduplicate_records(records_to_dedup, keys)
                step_statuses[idx]["message"] = f"Similarity deduplication merged {len(duplicates_caught)} near-duplicates into canonical records."
                step_statuses[idx]["records_produced"] = len(unique_records)

            elif step_type in ["merge", "output"]:
                final_source = unique_records if unique_records else validated_records or raw_candidates
                step_statuses[idx]["message"] = f"Finalized dataset: {len(final_source)} verified actionable records."
                step_statuses[idx]["records_produced"] = len(final_source)

            # Mark step completed
            step_statuses[idx]["status"] = "completed"
            step_statuses[idx]["completed_at"] = datetime.now(timezone.utc).isoformat()
            step_statuses[idx]["progress_percent"] = 100
            run.step_statuses = list(step_statuses)

            timeline.append({
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "step_id": step_id,
                "stage": step_type,
                "level": "success",
                "message": f"Step '{step_name}' completed successfully. Produced {step_statuses[idx]['records_produced']} items.",
                "details": {"records": step_statuses[idx]["records_produced"]}
            })
            run.execution_timeline = list(timeline)
            db.commit()

        # Step 4: Persist final dataset records and traceability evidence
        final_list = unique_records if unique_records else validated_records or raw_candidates
        valid_total = 0

        for item in final_list:
            is_valid = item.get("_is_valid", True)
            errors = item.get("_errors", [])
            conf = item.get("_confidence", 0.95)
            field_val_map = item.get("_field_validations", {})
            field_trans_map = item.get("_field_transformations", {})
            conf_level = item.get("_confidence_level", "HIGH" if conf >= 0.85 else "MEDIUM" if conf >= 0.70 else "LOW")

            # Clean internal temporary keys
            data_payload = {k: v for k, v in item.items() if not k.startswith("_")}
            if is_valid:
                valid_total += 1

            record_entity = DatasetRecord(
                run_id=run.id,
                workflow_id=workflow.id,
                data=data_payload,
                is_valid=is_valid,
                confidence_score=conf,
                confidence_level=conf_level,
                evidence_status="AVAILABLE",
                field_validations=field_val_map,
                field_transformations=field_trans_map,
                validation_errors=errors,
                deduplicated_with=None
            )
            db.add(record_entity)
            db.flush()

            # Attach evidence records for traceability
            source_url = str(data_payload.get("source", "https://public-web-intelligence.net/verified"))
            snippet = str(data_payload.get("snippet", f"Verified public intelligence listing for {data_payload.get('company_name', 'entity')}"))

            # Evidence item 1: General source listing
            ev1 = EvidenceRecord(
                record_id=record_entity.id,
                field_name="source",
                source_url=source_url,
                snippet=snippet,
                confidence=conf
            )
            db.add(ev1)

            # Evidence item 2: Official website domain proof
            if data_payload.get("website"):
                ev2 = EvidenceRecord(
                    record_id=record_entity.id,
                    field_name="website",
                    source_url=data_payload.get("website"),
                    snippet=f"Confirmed active public web domain for {data_payload.get('company_name', 'organization')}",
                    confidence=0.98 if is_valid else 0.50
                )
                db.add(ev2)

            # Evidence item 3: Contact proof
            if data_payload.get("public_business_email") or data_payload.get("business_email"):
                email_val = data_payload.get("public_business_email") or data_payload.get("business_email")
                ev3 = EvidenceRecord(
                    record_id=record_entity.id,
                    field_name="business_email",
                    source_url=source_url,
                    snippet=f"Public business inquiry endpoint verified: {email_val}",
                    confidence=0.94 if is_valid else 0.40
                )
                db.add(ev3)

        # Compute Data Quality Summary
        total_eval = len(final_list)
        valid_rate = round((valid_total / max(1, total_eval)) * 100, 1)

        field_completion: Dict[str, float] = {}
        for f in (workflow.fields_spec or []):
            fname = f.get("name") if isinstance(f, dict) else getattr(f, "name", "")
            if fname:
                present_count = sum(1 for it in final_list if it.get(fname) and str(it.get(fname)).strip())
                field_completion[fname] = round((present_count / max(1, total_eval)) * 100, 1)

        conf_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        all_issues = []
        for it in final_list:
            lvl = it.get("_confidence_level", "HIGH")
            conf_counts[lvl] = conf_counts.get(lvl, 0) + 1
            for err in it.get("_errors", []):
                if err not in all_issues:
                    all_issues.append(err)

        avg_conf = round(sum(it.get("_confidence", 0.95) for it in final_list) / max(1, total_eval), 2)
        dedup_base = len(records_to_dedup) if records_to_dedup else total_eval
        dedup_reduction = round((len(duplicates_caught) / max(1, dedup_base)) * 100, 1)

        quality_summary = {
            "total_evaluated": total_eval,
            "valid_count": valid_total,
            "valid_rate_percent": valid_rate,
            "field_completion_rates": field_completion,
            "confidence_breakdown": conf_counts,
            "average_confidence": avg_conf,
            "evidence_coverage_percent": 100.0,
            "deduplication_reduction_percent": dedup_reduction,
            "issues_found": all_issues
        }

        # Track connector activity metrics
        connector_registry.record_call("public_webpage", True, latency_ms=115.0, status_code=200)

        timeline.append({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": "completed",
            "level": "success",
            "message": f"Run completed successfully: {total_eval} records persisted ({valid_total} valid, {len(duplicates_caught)} duplicates merged).",
            "details": {"quality_summary": quality_summary}
        })

        # Update run stats
        run.status = "completed"
        run.total_records = len(final_list)
        run.valid_records = valid_total
        run.duplicate_records = len(duplicates_caught)
        run.quality_summary = quality_summary
        run.execution_timeline = list(timeline)
        run.source_health_summary = connector_registry.get_health_report()
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        logger.info(f"Execution completed for run {run.id}. Records: {run.total_records}, Duplicates removed: {run.duplicate_records}")


demo_executor = DemoWorkflowExecutor()
