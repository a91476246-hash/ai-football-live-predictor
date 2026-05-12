"""Tests for the Parik24 HTML → LiveMatch parser."""

from __future__ import annotations

from app.parsers.parik_parser import parse_parik_live_page
from app.schemas.match import MatchStatus

# Minimal HTML fixture that mirrors the real page structure.
FIXTURE_LIVE_PAGE = """
<!DOCTYPE html>
<html lang="uk">
<body data-brand="PRJ4">
<div id="root">
  <div>
    <div class="EC_AA EC_AC">Футбол</div>

    <div class="EC_Eq">
      <div class="EC_Ey">Бразилія. Ліга Пауліста A1</div>
      <div class="EC_CZ">
        <div>
          <a class="styles_wrapper__0hdzw" href="/uk/go">
            <div class="styles_wrapper__tfMk3">
              <div class="styles_time-status__Y2C9z">1Т 22:15</div>
              <span class="styles_wrapper__YmxdR">+184</span>
            </div>
            <div class="styles_wrapper__RRMjt styles_wrapper-list__X4zX5">
              <div class="styles_wrapper__1HTcK styles_content__XyPHU">
                <div class="styles_content__m0PN2">
                  <div class="styles_competitors__UgcxV">
                    <div class="styles_wrapper__-AU-O">Авеніда</div>
                    <div class="styles_wrapper__-AU-O">Греміо</div>
                  </div>
                  <div class="styles_wrapper__XF5l8">
                    <div class="styles_scores__CMREw">
                      <div class="styles_column__w4d1U">
                        <span>0</span>
                        <span>0</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </a>
        </div>
      </div>
    </div>

    <div class="EC_Eq">
      <div class="EC_Ey">Аргентина. Регіональний кубок</div>
      <div class="EC_CZ">
        <div>
          <a class="styles_wrapper__0hdzw" href="/uk/go">
            <div class="styles_wrapper__tfMk3">
              <div class="styles_time-status__Y2C9z">Перерва</div>
              <span class="styles_wrapper__YmxdR">+43</span>
            </div>
            <div class="styles_wrapper__RRMjt styles_wrapper-list__X4zX5">
              <div class="styles_wrapper__1HTcK styles_content__XyPHU">
                <div class="styles_content__m0PN2">
                  <div class="styles_competitors__UgcxV">
                    <div class="styles_wrapper__-AU-O">Уніон Креспо</div>
                    <div class="styles_wrapper__-AU-O">Пеньяроль Парана</div>
                  </div>
                  <div class="styles_wrapper__XF5l8">
                    <div class="styles_scores__CMREw">
                      <div class="styles_column__w4d1U">
                        <span>1</span>
                        <span>0</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </a>
        </div>
      </div>
    </div>

    <div class="EC_Eq">
      <div class="EC_Ey">Бразилія. Ліга Катаріненсе</div>
      <div class="EC_CZ">
        <div>
          <a class="styles_wrapper__0hdzw" href="/uk/go">
            <div class="styles_wrapper__tfMk3">
              <div class="styles_time-status__Y2C9z">2Т 92:10</div>
              <span class="styles_wrapper__YmxdR">+3</span>
            </div>
            <div class="styles_wrapper__RRMjt styles_wrapper-list__X4zX5">
              <div class="styles_wrapper__1HTcK styles_content__XyPHU">
                <div class="styles_content__m0PN2">
                  <div class="styles_competitors__UgcxV">
                    <div class="styles_wrapper__-AU-O">Барра</div>
                    <div class="styles_wrapper__-AU-O">Жоїнвіль</div>
                  </div>
                  <div class="styles_wrapper__XF5l8">
                    <div class="styles_scores__CMREw">
                      <div class="styles_column__w4d1U">
                        <span>1</span>
                        <span>0</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </a>
        </div>
      </div>
    </div>

  </div>

  <!-- Non-football section — should be ignored -->
  <div>
    <div class="EC_AA EC_AC">Теніс</div>
    <div class="EC_Eq">
      <div class="EC_Ey">ATP. Аделаїда</div>
    </div>
  </div>
</div>
</body>
</html>
"""

FIXTURE_EMPTY = "<html><body></body></html>"


def test_parses_all_football_matches() -> None:
    matches = parse_parik_live_page(FIXTURE_LIVE_PAGE)
    assert len(matches) == 3


def test_first_half_match() -> None:
    matches = parse_parik_live_page(FIXTURE_LIVE_PAGE)
    m = matches[0]
    assert m.home_team == "Авеніда"
    assert m.away_team == "Греміо"
    assert m.score_home == 0
    assert m.score_away == 0
    assert m.minute == 22
    assert m.status == MatchStatus.FIRST_HALF
    assert m.league == "Бразилія. Ліга Пауліста A1"
    assert m.is_scoreless


def test_half_time_match() -> None:
    matches = parse_parik_live_page(FIXTURE_LIVE_PAGE)
    m = matches[1]
    assert m.home_team == "Уніон Креспо"
    assert m.away_team == "Пеньяроль Парана"
    assert m.score_home == 1
    assert m.score_away == 0
    assert m.status == MatchStatus.HALF_TIME
    assert m.minute == 45
    assert m.league == "Аргентина. Регіональний кубок"


def test_second_half_match() -> None:
    matches = parse_parik_live_page(FIXTURE_LIVE_PAGE)
    m = matches[2]
    assert m.home_team == "Барра"
    assert m.away_team == "Жоїнвіль"
    assert m.score_home == 1
    assert m.score_away == 0
    assert m.minute == 92
    assert m.status == MatchStatus.SECOND_HALF
    assert m.is_second_half


def test_external_id_format() -> None:
    matches = parse_parik_live_page(FIXTURE_LIVE_PAGE)
    assert matches[0].external_id == "parik-Авеніда-Греміо"


def test_empty_page_returns_empty_list() -> None:
    assert parse_parik_live_page(FIXTURE_EMPTY) == []


def test_ignores_non_football_sections() -> None:
    matches = parse_parik_live_page(FIXTURE_LIVE_PAGE)
    leagues = {m.league for m in matches}
    assert "ATP. Аделаїда" not in leagues
