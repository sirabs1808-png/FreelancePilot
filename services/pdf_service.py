"""
PDF Document Generation Service for FreelancePilot.
Generates commercial-quality vector PDF invoices and proposals using ReportLab.
"""

import os
from pathlib import Path
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

from utils.config import EXPORTS_DIR
from utils.helpers import format_currency, format_date


class PDFService:
    """
    Renders styled, professional PDF invoices and proposals.
    """

    @staticmethod
    def generate_invoice_pdf(invoice, output_path: str = None) -> str:
        """
        Generates a PDF invoice for the given Invoice ORM model.
        Returns the absolute path to the generated PDF.
        """
        if not output_path:
            filename = f"{invoice.invoice_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = str(EXPORTS_DIR / filename)

        from database.db import SessionLocal
        from database.models import Setting

        db = SessionLocal()
        settings = {s.key: s.value for s in db.query(Setting).all()}
        db.close()

        biz_name = settings.get("business_name", "FreelancePilot Studio")
        biz_email = settings.get("business_email", "billing@freelancestudio.com")
        biz_phone = settings.get("business_phone", "+1 (555) 019-2834")
        biz_address = settings.get("business_address", "100 Innovation Way\nSan Francisco, CA 94107")

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        normal_style = ParagraphStyle(
            "InvoiceBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#475569")
        )

        bold_style = ParagraphStyle(
            "InvoiceBodyBold",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#0F172A"),
            fontName="Helvetica-Bold"
        )

        meta_right = ParagraphStyle(
            "MetaRight",
            parent=normal_style,
            alignment=2
        )

        meta_right_bold = ParagraphStyle(
            "MetaRightBold",
            parent=bold_style,
            alignment=2
        )

        elements = []

        # 1. Header Row
        biz_info_p = Paragraph(
            f"<b>{biz_name}</b><br/>"
            f"{biz_email}<br/>"
            f"{biz_phone}<br/>"
            f"{biz_address.replace(chr(10), '<br/>')}",
            normal_style
        )

        status_color = "#10B981" if invoice.status == "Paid" else ("#2563EB" if invoice.status == "Sent" else "#F59E0B")

        meta_info_p = Paragraph(
            f"<font size=20 color='#0F172A'><b>INVOICE</b></font><br/>"
            f"<b>Invoice #:</b> {invoice.invoice_number}<br/>"
            f"<b>Date:</b> {format_date(invoice.issue_date)}<br/>"
            f"<b>Due Date:</b> {format_date(invoice.due_date)}<br/>"
            f"<b>Status:</b> <font color='{status_color}'><b>{invoice.status.upper()}</b></font>",
            meta_right
        )

        header_table = Table([[biz_info_p, meta_info_p]], colWidths=[3.5 * inch, 3.5 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 24))

        # 2. Bill To Section
        client = invoice.client
        client_name = client.name if client else "Valued Client"
        client_company = f"{client.company}<br/>" if client and client.company else ""
        client_email = f"{client.email}<br/>" if client and client.email else ""
        client_addr = client.address.replace("\n", "<br/>") if client and client.address else ""

        bill_to_p = Paragraph(
            f"<font color='#64748B' size=8><b>BILLED TO:</b></font><br/>"
            f"<b>{client_name}</b><br/>"
            f"{client_company}"
            f"{client_email}"
            f"{client_addr}",
            normal_style
        )
        elements.append(bill_to_p)
        elements.append(Spacer(1, 20))

        # 3. Line Items Table
        table_data = [
            [
                Paragraph("<b>DESCRIPTION</b>", bold_style),
                Paragraph("<b>QTY</b>", meta_right_bold),
                Paragraph("<b>UNIT PRICE</b>", meta_right_bold),
                Paragraph("<b>TOTAL</b>", meta_right_bold)
            ]
        ]

        currency_sym = "$" if invoice.currency == "USD" else ("€" if invoice.currency == "EUR" else "£")

        for item in invoice.items:
            table_data.append([
                Paragraph(item.description, normal_style),
                Paragraph(f"{item.quantity:g}", meta_right),
                Paragraph(format_currency(item.unit_price, symbol=currency_sym), meta_right),
                Paragraph(format_currency(item.total, symbol=currency_sym), meta_right_bold),
            ])

        items_table = Table(
            table_data,
            colWidths=[4.0 * inch, 0.8 * inch, 1.2 * inch, 1.2 * inch]
        )
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor("#CBD5E1")),
            ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 15))

        # 4. Totals Block
        totals_data = [
            [Paragraph("Subtotal:", normal_style), Paragraph(format_currency(invoice.subtotal, symbol=currency_sym), meta_right)],
        ]

        if invoice.discount and invoice.discount > 0:
            totals_data.append([
                Paragraph("Discount:", normal_style),
                Paragraph(f"-{format_currency(invoice.discount, symbol=currency_sym)}", meta_right)
            ])

        if invoice.tax and invoice.tax > 0:
            totals_data.append([
                Paragraph("Tax / VAT:", normal_style),
                Paragraph(f"+{format_currency(invoice.tax, symbol=currency_sym)}", meta_right)
            ])

        total_style = ParagraphStyle(
            "TotalBig",
            parent=meta_right_bold,
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#2563EB")
        )

        totals_data.append([
            Paragraph("<b>Total Due:</b>", bold_style),
            Paragraph(f"<b>{format_currency(invoice.total, symbol=currency_sym)}</b>", total_style)
        ])

        totals_table = Table(totals_data, colWidths=[5.6 * inch, 1.6 * inch])
        totals_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor("#0F172A")),
        ]))
        elements.append(totals_table)
        elements.append(Spacer(1, 25))

        # 5. Notes & Payment Instructions
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=15))

        if invoice.notes:
            notes_p = Paragraph(f"<b>Notes & Terms:</b><br/>{invoice.notes.replace(chr(10), '<br/>')}", normal_style)
            elements.append(notes_p)
            elements.append(Spacer(1, 10))

        payment_terms = Paragraph(
            "<b>Payment Instructions:</b><br/>"
            "Please transfer funds to the bank details listed on your agreement, or via Stripe / Bank Wire.<br/>"
            "Thank you for your business!",
            normal_style
        )
        elements.append(payment_terms)

        doc.build(elements)
        return output_path

    @staticmethod
    def generate_financial_report_pdf(
        report_title: str,
        summary: dict,
        monthly_breakdown: list,
        client_breakdown: list,
        output_path: str = None
    ) -> str:
        """
        Generates a comprehensive executive financial report in PDF.
        """
        if not output_path:
            filename = f"Financial_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = str(EXPORTS_DIR / filename)

        from database.db import SessionLocal
        from database.models import Setting

        db = SessionLocal()
        settings = {s.key: s.value for s in db.query(Setting).all()}
        db.close()

        biz_name = settings.get("business_name", "FreelancePilot Studio")

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0F172A"),
            fontName="Helvetica-Bold"
        )

        section_style = ParagraphStyle(
            "ReportSection",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#2563EB"),
            fontName="Helvetica-Bold",
            spaceBefore=14,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155")
        )

        bold_style = ParagraphStyle(
            "ReportBold",
            parent=body_style,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#0F172A")
        )

        elements = []

        # 1. Header
        elements.append(Paragraph(f"<font color='#2563EB'><b>{biz_name.upper()}</b></font> • EXECUTIVE FINANCIAL AUDIT", body_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563EB"), spaceAfter=14))
        elements.append(Paragraph(report_title, title_style))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", body_style))
        elements.append(Spacer(1, 14))

        # 2. Key Metrics Summary Grid
        summary_table_data = [
            [
                Paragraph("<b>GROSS BILLED</b>", bold_style),
                Paragraph("<b>COLLECTED REVENUE</b>", bold_style),
                Paragraph("<b>TOTAL EXPENSES</b>", bold_style),
                Paragraph("<b>NET PROFIT</b>", bold_style)
            ],
            [
                Paragraph(f"<font size=12 color='#0F172A'><b>{summary.get('gross', '$0.00')}</b></font>", body_style),
                Paragraph(f"<font size=12 color='#10B981'><b>{summary.get('collected', '$0.00')}</b></font>", body_style),
                Paragraph(f"<font size=12 color='#EF4444'><b>{summary.get('expenses', '$0.00')}</b></font>", body_style),
                Paragraph(f"<font size=12 color='#2563EB'><b>{summary.get('net_profit', '$0.00')}</b></font>", body_style)
            ]
        ]
        sum_table = Table(summary_table_data, colWidths=[1.8 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch])
        sum_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(sum_table)
        elements.append(Spacer(1, 14))

        # 3. Monthly Breakdown Table
        elements.append(Paragraph("Monthly Cashflow Performance", section_style))
        m_data = [
            [
                Paragraph("<b>MONTH</b>", bold_style),
                Paragraph("<b>GROSS BILLED</b>", bold_style),
                Paragraph("<b>EXPENSES</b>", bold_style),
                Paragraph("<b>NET PROFIT</b>", bold_style)
            ]
        ]
        for row in monthly_breakdown:
            m_data.append([
                Paragraph(row["month"], body_style),
                Paragraph(row["income"], body_style),
                Paragraph(row["expense"], body_style),
                Paragraph(row["profit"], bold_style),
            ])

        m_table = Table(m_data, colWidths=[2.2 * inch, 1.7 * inch, 1.7 * inch, 1.6 * inch])
        m_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        elements.append(m_table)
        elements.append(Spacer(1, 14))

        # 4. Client Lifetime Value (LTV) Table
        elements.append(Paragraph("Client Lifetime Value (LTV) & Account Status", section_style))
        c_data = [
            [
                Paragraph("<b>CLIENT</b>", bold_style),
                Paragraph("<b>PROJECTS</b>", bold_style),
                Paragraph("<b>COLLECTED (PAID)</b>", bold_style),
                Paragraph("<b>OUTSTANDING</b>", bold_style)
            ]
        ]
        for c in client_breakdown:
            c_data.append([
                Paragraph(c["name"], body_style),
                Paragraph(str(c["projects"]), body_style),
                Paragraph(c["paid"], bold_style),
                Paragraph(c["outstanding"], body_style),
            ])

        c_table = Table(c_data, colWidths=[2.8 * inch, 1.2 * inch, 1.6 * inch, 1.6 * inch])
        c_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        elements.append(c_table)

        doc.build(elements)
        return output_path


    @staticmethod
    def generate_proposal_pdf(
        proposal_title: str,
        client_name: str,
        content: str,
        output_path: str = None
    ) -> str:
        """
        Generates a clean, professional PDF client proposal.
        """
        if not output_path:
            clean_title = "".join(c for c in proposal_title if c.isalnum() or c in ("-", "_")).rstrip()
            filename = f"Proposal_{clean_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = str(EXPORTS_DIR / filename)

        from database.db import SessionLocal
        from database.models import Setting

        db = SessionLocal()
        settings = {s.key: s.value for s in db.query(Setting).all()}
        db.close()

        biz_name = settings.get("business_name", "FreelancePilot Studio")
        biz_email = settings.get("business_email", "contact@freelancestudio.com")

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=44,
            rightMargin=44,
            topMargin=44,
            bottomMargin=44
        )

        styles = getSampleStyleSheet()

        h1_style = ParagraphStyle(
            "ProposalH1",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0F172A"),
            fontName="Helvetica-Bold"
        )

        h2_style = ParagraphStyle(
            "ProposalH2",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#2563EB"),
            fontName="Helvetica-Bold",
            spaceBefore=14,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            "ProposalBody",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceAfter=8
        )

        elements = []

        # Header Banner
        header_p = Paragraph(
            f"<font color='#2563EB'><b>{biz_name.upper()}</b></font> • {biz_email}<br/>"
            f"<font size=8 color='#64748B'>PREPARED FOR: {client_name.upper()} • {datetime.now().strftime('%B %d, %Y')}</font>",
            body_style
        )
        elements.append(header_p)
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563EB"), spaceAfter=18))

        # Title
        elements.append(Paragraph(proposal_title, h1_style))
        elements.append(Spacer(1, 14))

        # Content lines
        for line in content.split("\n"):
            line = line.strip()
            if not line:
                elements.append(Spacer(1, 6))
                continue

            if line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
                clean_heading = line.lstrip("#").strip()
                elements.append(Paragraph(clean_heading, h2_style))
            elif line.startswith("- ") or line.startswith("* "):
                bullet_text = line[2:].strip()
                elements.append(Paragraph(f"• {bullet_text}", body_style))
            else:
                elements.append(Paragraph(line, body_style))

        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=14))
        elements.append(Paragraph(
            f"<i>Proposal prepared by {biz_name}. Valid for 30 days from issuance.</i>",
            ParagraphStyle("FooterNote", parent=body_style, fontSize=8, textColor=colors.HexColor("#94A3B8"))
        ))

        doc.build(elements)
        return output_path

    @staticmethod
    def generate_financial_report_pdf(
        report_title: str,
        summary: dict,
        monthly_breakdown: list,
        client_breakdown: list,
        output_path: str = None
    ) -> str:
        """
        Generates a comprehensive executive financial report in PDF.
        """
        if not output_path:
            filename = f"Financial_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = str(EXPORTS_DIR / filename)

        from database.db import SessionLocal
        from database.models import Setting

        db = SessionLocal()
        settings = {s.key: s.value for s in db.query(Setting).all()}
        db.close()

        biz_name = settings.get("business_name", "FreelancePilot Studio")

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0F172A"),
            fontName="Helvetica-Bold"
        )

        section_style = ParagraphStyle(
            "ReportSection",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#2563EB"),
            fontName="Helvetica-Bold",
            spaceBefore=14,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155")
        )

        bold_style = ParagraphStyle(
            "ReportBold",
            parent=body_style,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#0F172A")
        )

        elements = []

        # 1. Header
        elements.append(Paragraph(f"<font color='#2563EB'><b>{biz_name.upper()}</b></font> • EXECUTIVE FINANCIAL AUDIT", body_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563EB"), spaceAfter=14))
        elements.append(Paragraph(report_title, title_style))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", body_style))
        elements.append(Spacer(1, 14))

        # 2. Key Metrics Summary Grid
        summary_table_data = [
            [
                Paragraph("<b>GROSS BILLED</b>", bold_style),
                Paragraph("<b>COLLECTED REVENUE</b>", bold_style),
                Paragraph("<b>TOTAL EXPENSES</b>", bold_style),
                Paragraph("<b>NET PROFIT</b>", bold_style)
            ],
            [
                Paragraph(f"<font size=12 color='#0F172A'><b>{summary.get('gross', '$0.00')}</b></font>", body_style),
                Paragraph(f"<font size=12 color='#10B981'><b>{summary.get('collected', '$0.00')}</b></font>", body_style),
                Paragraph(f"<font size=12 color='#EF4444'><b>{summary.get('expenses', '$0.00')}</b></font>", body_style),
                Paragraph(f"<font size=12 color='#2563EB'><b>{summary.get('net_profit', '$0.00')}</b></font>", body_style)
            ]
        ]
        sum_table = Table(summary_table_data, colWidths=[1.8 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch])
        sum_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(sum_table)
        elements.append(Spacer(1, 14))

        # 3. Monthly Breakdown Table
        elements.append(Paragraph("Monthly Cashflow Performance", section_style))
        m_data = [
            [
                Paragraph("<b>MONTH</b>", bold_style),
                Paragraph("<b>GROSS BILLED</b>", bold_style),
                Paragraph("<b>EXPENSES</b>", bold_style),
                Paragraph("<b>NET PROFIT</b>", bold_style)
            ]
        ]
        for row in monthly_breakdown:
            m_data.append([
                Paragraph(row["month"], body_style),
                Paragraph(row["income"], body_style),
                Paragraph(row["expense"], body_style),
                Paragraph(row["profit"], bold_style),
            ])

        m_table = Table(m_data, colWidths=[2.2 * inch, 1.7 * inch, 1.7 * inch, 1.6 * inch])
        m_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        elements.append(m_table)
        elements.append(Spacer(1, 14))

        # 4. Client Lifetime Value (LTV) Table
        elements.append(Paragraph("Client Lifetime Value (LTV) & Account Status", section_style))
        c_data = [
            [
                Paragraph("<b>CLIENT</b>", bold_style),
                Paragraph("<b>PROJECTS</b>", bold_style),
                Paragraph("<b>COLLECTED (PAID)</b>", bold_style),
                Paragraph("<b>OUTSTANDING</b>", bold_style)
            ]
        ]
        for c in client_breakdown:
            c_data.append([
                Paragraph(c["name"], body_style),
                Paragraph(str(c["projects"]), body_style),
                Paragraph(c["paid"], bold_style),
                Paragraph(c["outstanding"], body_style),
            ])

        c_table = Table(c_data, colWidths=[2.8 * inch, 1.2 * inch, 1.6 * inch, 1.6 * inch])
        c_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        elements.append(c_table)

        doc.build(elements)
        return output_path

