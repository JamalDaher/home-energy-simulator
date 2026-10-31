from io import BytesIO
from reportlab.pdfgen import canvas
from home_energy_simulator.model import SystemConfig
from home_energy_simulator.outage import simulate_outage
from home_energy_simulator.scenarios import Scenario
from home_energy_simulator.reports import outage_pdf


def test_report_is_valid_pdf_bytes():
    scenario = Scenario("Test & <Safety>", SystemConfig(solar_kw=0, battery_kwh=0),
                        [1] * 24, [0] * 24, days=1)
    result = simulate_outage(scenario.config, scenario.loads_kw,
                             scenario.sun_factors, days=scenario.days)
    pdf = outage_pdf(scenario, result)
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1000
