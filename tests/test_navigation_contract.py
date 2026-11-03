"""Keep dashboard navigation links, anchors and expansion targets aligned."""
import re
from pathlib import Path

APP = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_navigation_links_have_unique_target_anchors():
    nav = APP.split('<nav aria-label="Simulator sections" class="sim-nav">', 1)[1].split("</nav>", 1)[0]
    targets = re.findall(r'<a href="#([a-z-]+)"', nav)
    assert len(targets) == 10
    assert len(targets) == len(set(targets))
    for target in targets:
        assert len(re.findall(r'id="' + re.escape(target) + r'"', APP)) >= 1, target


def test_expandable_navigation_targets_precede_section_expanders():
    sections = {
        "critical-loads": "Critical-Load Circuit Planner",
        "battery-bank": "LiFePO4 Battery Bank Designer",
        "outage": "Whole-Home Outage Simulator",
        "hvac": "HVAC & Generator Sizing",
        "generator-fuel": "Generator Fuel & Runtime Calculator",
        "fuel-aware-outage": "Integrated Fuel-Aware Outage",
        "backup-comparison": "Backup System Comparison",
        "optimization": "System Optimization",
        "workspace": "Scenario Workspace & PDF Reports",
    }
    for anchor, title in sections.items():
        anchor_pos = APP.index('id="' + anchor + '"')
        expander_pos = APP.find('st.expander("' + title, anchor_pos)
        assert expander_pos > anchor_pos, anchor
        # Ensure the target is the next section-level expander.
        next_anchor = APP.find('class="sim-section-anchor"', anchor_pos + len(anchor))
        if next_anchor != -1:
            assert expander_pos < next_anchor, anchor


def test_navigation_expansion_targets_match_sections():
    script = APP.split("nav_expansion_script = ", 1)[1].split('"""', 2)[1]
    targets = set(re.findall(r"'([a-z]+(?:-[a-z]+)+)'", script.split("function openSection", 1)[0]))
    assert targets == {
        "critical-loads", "battery-bank", "outage", "hvac",
        "generator-fuel", "fuel-aware-outage", "backup-comparison",
        "optimization", "workspace",
    }
