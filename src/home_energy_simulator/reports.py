"""Create a standalone, in-memory PDF report from a simulated outage."""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from .scenarios import Scenario
from .outage import OutageResult


def outage_pdf(scenario: Scenario, result: OutageResult) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(612, 792), rightMargin=48,
                            leftMargin=48, topMargin=44, bottomMargin=44)
    styles = getSampleStyleSheet()
    styles["Title"].alignment = TA_CENTER
    story = [Paragraph("Home Energy Simulator", styles["Title"]),
             Paragraph("Outage Analysis Report | v1.0", styles["Heading2"]),
             Paragraph("Scenario: " + _escape(scenario.name), styles["Normal"]),
             Spacer(1, 16)]
    fields = [
        ("Duration", f"{result.hours_simulated} hours"),
        ("Demand served", f"{result.fraction_demand_served:.1%}"),
        ("Hours fully supplied", f"{result.hours_fully_served} / {result.hours_simulated}"),
        ("Unserved energy", f"{result.total_unserved_kwh:.2f} kWh"),
        ("Solar array", f"{scenario.config.solar_kw:g} kW"),
        ("Battery storage", f"{scenario.config.battery_kwh:g} kWh"),
        ("Generator rating", f"{scenario.config.generator_kw:g} kW"),
        ("Generator runtime", f"{result.generator_hours} hours"),
        ("Fuel consumed", f"{result.generator_fuel_used:.2f} {result.generator_fuel_unit}"),
        ("Fuel cost", f"${result.generator_fuel_cost:,.2f}"),
        ("First unmet hour", "None" if result.first_unserved_hour is None else str(result.first_unserved_hour + 1)),
    ]
    t = Table([[Paragraph(k, styles["Normal"]), Paragraph(v, styles["Normal"])] for k, v in fields],
              colWidths=[225, 270], hAlign="LEFT")
    t.setStyle(TableStyle([("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.whitesmoke, colors.white]),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 8)]))
    story.extend([t, Spacer(1, 18), Paragraph("Model assumptions", styles["Heading2"]),
                  Paragraph("Hourly average loads and a repeated 24-hour solar profile. "
                            "Generator fuel consumption is an estimate. The model does not "
                            "simulate starting surges, installation constraints, weather "
                            "uncertainty or code-compliant interconnection. "
                            "Results are illustrative, not an electrical design.", styles["Normal"])])
    doc.build(story)
    return buffer.getvalue()


def _escape(value: str) -> str:
    from xml.sax.saxutils import escape
    return escape(value)
