"""Keep dashboard navigation links, anchors and expansion targets aligned."""
import re
from pathlib import Path

APP = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_navigation_links_have_unique_target_anchors():
    nav = APP.split('<nav aria-label="Simulator sections" class="sim-nav">', 1)[1].split("</nav>", 1)[0]
    targets = re.findall(r'<a[^>]* href="#([a-z-]+)"', nav)
    assert len(targets) == 10
    assert len(targets) == len(set(targets))
    for target in targets:
        assert (f'id="{target}"' in APP or f'anchor="{target}"' in APP), target


def test_expandable_navigation_targets_precede_section_expanders():
    sections = {
        "critical-loads": "Essential circuits",
        "battery-bank": "Battery bank designer",
        "outage": "Outage simulation",
        "hvac": "Heating, cooling & generator sizing",
        "generator-fuel": "Generator fuel & runtime",
        "fuel-aware-outage": "Multi-day outage with fuel limits",
        "backup-comparison": "Compare backup systems",
        "optimization": "Find a better system configuration",
        "workspace": "Saved scenarios & reports",
    }
    for anchor, title in sections.items():
        anchor_pos = APP.index('id="' + anchor + '"')
        expander_pos = APP.find('st.expander("' + title, anchor_pos)
        assert expander_pos > anchor_pos, anchor
        # Ensure the target is the next section-level expander.
        assert expander_pos < APP.find("st.expander(", anchor_pos + 1) + 200, anchor


def test_navigation_expansion_targets_match_sections():
    script = APP.split("nav_expansion_script = ", 1)[1].split('"""', 2)[1]
    targets = set(re.findall(r"'([a-z]+(?:-[a-z]+)*)'", script.split("]);", 1)[0]))
    assert targets == {
        "critical-loads", "battery-bank", "outage", "hvac",
        "generator-fuel", "fuel-aware-outage", "backup-comparison",
        "optimization", "workspace",
    }
