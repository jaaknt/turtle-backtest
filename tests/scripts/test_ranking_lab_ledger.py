"""The hypothesis ledger is the ranking lab's multiple-testing counter, not just a record.

`required_margin(n_tested)` reads the number of recorded hypotheses, so every duplicate row
raises the bar for every later candidate. `--eval` is re-run routinely — a `--no-portfolio`
preview before the real run, a re-measurement after a harness fix (rows 8 and 9 of the
committed ledger were exactly that) — so the writer has to be keyed on the candidate id rather
than appending blindly.

The script is loaded by path because `scripts/` holds hyphenated files that are not importable
as modules.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "qullamaggie-ranking-lab.py"

LEDGER_TEMPLATE = """# Ledger

Hand-written preamble that must survive every write.

<!-- lab:ledger:start -->

| # | Candidate | Hypothesis | Verdict |
| --- | --- | --- | --- |
| 1 | `c001-first` | First one. | **REJECT** |
| 2 | `c002-second` | Second one. | **REJECT** |
<!-- lab:ledger:end -->

## Findings

Hand-written analysis that must survive every write.
"""


@pytest.fixture
def lab(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """The script module, writing to a throwaway ledger."""
    spec = importlib.util.spec_from_file_location("qullamaggie_ranking_lab", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    ledger = tmp_path / "ledger.md"
    ledger.write_text(LEDGER_TEMPLATE, encoding="utf-8")
    monkeypatch.setattr(module, "LEDGER_PATH", ledger)
    return module


def test_tested_spec_ids_reads_the_candidate_column(lab: ModuleType) -> None:
    assert lab.tested_spec_ids() == ["c001-first", "c002-second"]


def test_a_new_candidate_is_appended_with_the_next_number(lab: ModuleType) -> None:
    replaced = lab.upsert_ledger("c003-third", "`c003-third` | Third one. | **ACCEPT** |")

    assert replaced is False
    assert lab.tested_spec_ids() == ["c001-first", "c002-second", "c003-third"]
    assert lab.ledger_rows()[-1].startswith("| 3 | `c003-third` |")


def test_re_running_a_candidate_replaces_its_row_and_not_the_count(lab: ModuleType) -> None:
    """The whole point: a second `--eval` of one hypothesis must not charge the next one a
    wider multiple-testing margin, and must not leave two contradictory verdicts on record."""
    lab.upsert_ledger("c001-first", "`c001-first` | First one. | **REJECT** | re-measured |")
    replaced = lab.upsert_ledger("c001-first", "`c001-first` | First one. | **ACCEPT** | re-measured again |")

    assert replaced is True
    assert lab.tested_spec_ids() == ["c001-first", "c002-second"]
    rows = lab.ledger_rows()
    assert rows[0].startswith("| 1 | `c001-first` |"), "a replaced row keeps its original number"
    assert "re-measured again" in rows[0]
    assert "**REJECT**" not in rows[0]


def test_writes_never_touch_anything_outside_the_markers(lab: ModuleType) -> None:
    lab.upsert_ledger("c003-third", "`c003-third` | Third one. | **REJECT** |")
    lab.upsert_ledger("c001-first", "`c001-first` | First one. | **REJECT** |")

    text = lab.LEDGER_PATH.read_text(encoding="utf-8")
    assert text.startswith("# Ledger\n\nHand-written preamble that must survive every write.")
    assert text.endswith("## Findings\n\nHand-written analysis that must survive every write.\n")


def test_a_ledger_with_duplicated_markers_is_refused(lab: ModuleType) -> None:
    """Refuse before writing: the verdict has already been printed, so a bad write loses it."""
    lab.LEDGER_PATH.write_text(LEDGER_TEMPLATE + "\n<!-- lab:ledger:end -->\n", encoding="utf-8")

    with pytest.raises(ValueError, match="expected exactly one"):
        lab.upsert_ledger("c003-third", "`c003-third` | Third one. | **REJECT** |")
