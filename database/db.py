"""
Database initialization and session management for FreelancePilot.
Uses SQLite for local storage and SQLAlchemy for ORM.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Default database directory and file path
DB_DIR = Path.home() / ".freelancepilot"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "freelancepilot.db"

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Context manager or helper to obtain a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes the database schema and seeds initial data if empty."""
    from database import models
    Base.metadata.create_all(bind=engine)
    seed_initial_data()


def seed_initial_data():
    """Seeds sample data on first launch so the dashboard looks great immediately."""
    from database.models import Client, Project, Task, Invoice, InvoiceItem, Expense, Activity, Setting
    from datetime import datetime, timedelta

    db = SessionLocal()
    try:
        # Check if settings already exist
        if db.query(Setting).count() == 0:
            default_settings = [
                Setting(key="theme", value="dark"),
                Setting(key="currency", value="USD"),
                Setting(key="currency_symbol", value="$"),
                Setting(key="business_name", value="My Freelance Studio"),
                Setting(key="business_email", value="alex@freelancestudio.com"),
                Setting(key="business_phone", value="+1 (555) 019-2834"),
                Setting(key="business_address", value="100 Innovation Way, Suite 400\nSan Francisco, CA 94107"),
                Setting(key="default_ai_provider", value="gemini"),
            ]
            db.add_all(default_settings)

        # Check if clients exist
        if db.query(Client).count() == 0:
            c1 = Client(
                name="Sophia Vance",
                company="Nexus Tech",
                email="sophia@nexustech.io",
                phone="+1 (555) 234-5678",
                address="742 Evergreen Terrace, Seattle, WA",
                notes="Prefers weekly async updates on Slack."
            )
            c2 = Client(
                name="Marcus Thorne",
                company="Aura Brand Studio",
                email="marcus@aurastudio.co",
                phone="+1 (555) 876-5432",
                address="120 West 42nd St, New York, NY",
                notes="Rebranding contract, fast turnaround needed."
            )
            c3 = Client(
                name="Elena Rostova",
                company="Solaria Health",
                email="elena@solariahealth.org",
                phone="+1 (555) 345-6789",
                address="450 Mission St, San Francisco, CA",
                notes="HIPAA-conscious web app design."
            )
            db.add_all([c1, c2, c3])
            db.commit()

            # Seed projects
            now = datetime.now()
            p1 = Project(
                client_id=c1.id,
                title="Nexus Mobile App Redesign",
                description="End-to-end redesign of iOS and Android SaaS applications with new design system.",
                budget=8500.0,
                deadline=now + timedelta(days=12),
                status="In Progress",
                progress=65
            )
            p2 = Project(
                client_id=c2.id,
                title="Aura Brand Identity & Web",
                description="Complete visual identity, logo package, typography guidelines, and responsive Webflow site.",
                budget=5200.0,
                deadline=now + timedelta(days=5),
                status="In Progress",
                progress=85
            )
            p3 = Project(
                client_id=c3.id,
                title="Patient Portal UI System",
                description="Design audit and WCAG AAA compliant component library for telehealth portal.",
                budget=6400.0,
                deadline=now + timedelta(days=24),
                status="Not Started",
                progress=15
            )
            db.add_all([p1, p2, p3])
            db.commit()

            # Seed tasks
            t1 = Task(project_id=p1.id, title="Finalize Figma component tokens", priority="High", deadline=now + timedelta(days=2), completed=False)
            t2 = Task(project_id=p1.id, title="Prototype user onboarding flow", priority="Medium", deadline=now + timedelta(days=4), completed=False)
            t3 = Task(project_id=p2.id, title="Deliver vector logo asset pack", priority="Urgent", deadline=now + timedelta(days=1), completed=False)
            t4 = Task(project_id=p2.id, title="QA testing on mobile viewport", priority="Medium", deadline=now + timedelta(days=3), completed=True)
            t5 = Task(project_id=p3.id, title="Initial client kickoff & research brief", priority="Low", deadline=now + timedelta(days=6), completed=False)
            db.add_all([t1, t2, t3, t4, t5])

            # Seed invoices
            inv1 = Invoice(
                invoice_number="INV-2026-001",
                client_id=c1.id,
                issue_date=now - timedelta(days=15),
                due_date=now - timedelta(days=1),
                status="Paid",
                currency="USD",
                subtotal=4250.0,
                discount=0.0,
                tax=0.0,
                total=4250.0,
                notes="Milestone 1: Wireframes and Design System Tokens."
            )
            inv2 = Invoice(
                invoice_number="INV-2026-002",
                client_id=c2.id,
                issue_date=now - timedelta(days=7),
                due_date=now + timedelta(days=7),
                status="Sent",
                currency="USD",
                subtotal=2600.0,
                discount=0.0,
                tax=0.0,
                total=2600.0,
                notes="Milestone 1: Brand Guidelines and Typography."
            )
            inv3 = Invoice(
                invoice_number="INV-2026-003",
                client_id=c3.id,
                issue_date=now - timedelta(days=2),
                due_date=now + timedelta(days=14),
                status="Draft",
                currency="USD",
                subtotal=3200.0,
                discount=0.0,
                tax=0.0,
                total=3200.0,
                notes="Upfront deposit (50%) for Patient Portal UI."
            )
            db.add_all([inv1, inv2, inv3])
            db.commit()

            # Seed invoice items
            db.add(InvoiceItem(invoice_id=inv1.id, description="Design System Architecture & Tokens", quantity=1.0, unit_price=2500.0, total=2500.0))
            db.add(InvoiceItem(invoice_id=inv1.id, description="Mobile Flow Wireframes (30 screens)", quantity=1.0, unit_price=1750.0, total=1750.0))
            db.add(InvoiceItem(invoice_id=inv2.id, description="Brand Identity Guidelines & Assets", quantity=1.0, unit_price=2600.0, total=2600.0))
            db.add(InvoiceItem(invoice_id=inv3.id, description="Patient Portal UI System Deposit (50%)", quantity=1.0, unit_price=3200.0, total=3200.0))

            # Seed expenses
            e1 = Expense(project_id=p1.id, category="Software", description="Figma Organization Seat", amount=75.0, date=now - timedelta(days=10))
            e2 = Expense(project_id=p2.id, category="Assets", description="Commercial Typeface License (Aeonik)", amount=240.0, date=now - timedelta(days=6))
            e3 = Expense(project_id=None, category="Hosting", description="Cloud server & staging environments", amount=45.0, date=now - timedelta(days=3))
            db.add_all([e1, e2, e3])

            # Seed activities
            db.add(Activity(title="Invoice Paid", description="Nexus Tech paid $4,250.00 for INV-2026-001", icon="fa5s.check-circle", category="invoice"))
            db.add(Activity(title="Invoice Sent", description="Sent INV-2026-002 ($2,600.00) to Marcus Thorne", icon="fa5s.paper-plane", category="invoice"))
            db.add(Activity(title="Milestone Completed", description="Aura Brand Identity reached 85% completion", icon="fa5s.flag-checkered", category="project"))
            db.add(Activity(title="New Client Added", description="Elena Rostova (Solaria Health) was added", icon="fa5s.user-plus", category="client"))

            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()
