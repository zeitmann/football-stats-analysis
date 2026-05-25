# Football Stats Analysis — Projektkontext für Claude Code

ZHAW Scientific Programming FS2026 — Timon Wallroth

---

## Projektübersicht

Analyse von Premier-League-Spielerdaten aus der football-data.org API.
Pipeline: Datensammlung → Bereinigung → Analyse & Visualisierung → LLM-Scouting-Reports → Flask-Dashboard.

---

## Dateistruktur

```
football-stats-analysis/
├── .env                        # API-Keys (siehe unten)
├── requirements.txt            # Python-Dependencies (venv unter .venv/)
├── app/
│   └── app.py                  # Flask-Webapp (Port 5001)
├── notebooks/
│   ├── 01_data_collection.ipynb    # API-Abruf + Fake-Marktwerte
│   ├── 02_data_preparation.ipynb   # Bereinigung + Feature Engineering
│   ├── 03_analysis_visualization.ipynb  # EDA, Korrelation, Regression, t-Test
│   ├── 04_llm_analysis.ipynb       # Ollama-Scouting-Reports
│   └── data/
│       └── football.db         # SQLite-Datenbank (Hauptdatenbank)
└── data/
    └── football.db             # Symlink/Kopie — wird von app.py genutzt
```

---

## Datenbank (`notebooks/data/football.db`)

**Tabelle `players`** (351 Zeilen) — Rohdaten aus API:
- `player_id`, `name`, `nationality`, `date_of_birth`, `team_id`, `team_name`
- `position` — mapped: `"Goalkeeper"` / `"Defender"` / `"Midfielder"` / `"Forward"` / `"Unknown"`
- `market_value` — Float in **€M** (fake, positionsbasiert generiert)
- `market_value_numeric` — gleicher Wert nach `clean_market_value()`
- `market_value_tm` — Float in **€M** (Transfermarkt-Wert oder Fallback auf `market_value`)

**Tabelle `players_cleaned`** (351 Zeilen) — nach Notebook 02:
- Alle Spalten von `players` plus:
- `position_group` — standardisiert (4 Kategorien)
- `age` — berechnet aus `date_of_birth`
- `has_market_value` — Boolean

**Tabelle `player_reports`** — nach Notebook 04 (optional):
- Top-5-Spieler + `scouting_report`-Spalte (von llama3.2 generiert)

> ⚠️ **Wichtig:** `market_value_tm` ist in **€M** (z.B. `22.3` = €22,3 Mio.).
> Niemals durch 1.000.000 dividieren — das wurde bereits korrigiert.

---

## Datenbank-Pfade

- **Notebooks** laufen aus `notebooks/` → verwenden relativen Pfad `data/football.db`
- **app.py** verwendet absoluten Pfad:
  ```python
  BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  db_path = os.path.join(BASE_DIR, "notebooks", "data", "football.db")
  ```

---

## Flask-App (`app/app.py`)

**Starten:**
```bash
python app/app.py
# → http://localhost:5001
```

**Routen:**

| Route | Inhalt |
|-------|--------|
| `/` | Startseite mit 4 Metrikkarten |
| `/players` | Alle Spieler als durchsuchbare Tabelle |
| `/analysis` | Top-10, Durchschnittswerte, t-Test (Forwards vs. Defenders) |
| `/charts` | 6 Matplotlib/Seaborn-Charts als Base64-Bilder |
| `/scouting` | LLM-Scouting-Reports (lädt `player_reports`-Tabelle) |

**Technologie:** Bootstrap 5 (CDN), `render_template_string`, `matplotlib.use("Agg")`, seaborn, scipy

---

## Notebooks ausführen

```bash
cd notebooks
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=120 \
  01_data_collection.ipynb
# Dann 02_, 03_, 04_ in dieser Reihenfolge
```

---

## API & LLM-Konfiguration

**`.env`-Datei:**
```
FOOTBALL_API_KEY=<echter Key für football-data.org>
OPENAI_API_KEY=nokeyneeded   # nicht mehr benötigt — Ollama läuft lokal
```

**Ollama (lokal, kein API-Key nötig):**
- Installer: https://ollama.com
- Model einmalig pullen: `ollama pull llama3.2`
- Prüfen: `ollama list`
- Endpoint: `http://localhost:11434/v1`
- Konfiguration in Notebook 04:
  ```python
  client = openai.OpenAI(api_key="nokeyneeded", base_url="http://localhost:11434/v1")
  model = "llama3.2:latest"
  ```

---

## Wichtige Designentscheidungen

| Entscheidung | Detail |
|---|---|
| Marktwerte in €M | `market_value_tm` ist Float in Millionen (z.B. `59.6` = €59,6M). Alle Formatierungen verwenden `f"€{val:.1f}M"` |
| Fake-Marktwerte | Transfermarkt-Scraping ist geblockt → `random.uniform(min, max)` pro Position in `fetch_players()` in Notebook 01, Fallback: `df["market_value_tm"].fillna(df["market_value"])` |
| API-Positionsmapping | football-data.org liefert `"Defence"`, `"Midfield"`, `"Offence"` → wird in `position_map` auf `"Defender"`, `"Midfielder"`, `"Forward"` gemappt |
| Ollama statt OpenAI | Vollständig auf lokale Inferenz umgestellt; `openai`-Library wird weiterverwendet (kompatibles Interface) |
| Notebook-Zellenreihenfolge | Notebook 02 wurde manuell umsortiert (war komplett umgekehrt) |

---

## Positionsbasierte Marktwert-Ranges (€M)

```python
position_values = {
    "Goalkeeper": (2,  15),
    "Defender":   (3,  40),
    "Midfielder": (5,  80),
    "Forward":    (8, 120),
}
```

---

## Python-Umgebung

```bash
source .venv/bin/activate   # venv aktivieren
python --version             # 3.13
```

Wichtige installierte Pakete: `flask`, `pandas`, `numpy`, `matplotlib`, `seaborn`,
`scipy`, `statsmodels`, `openai`, `python-dotenv`, `requests`, `beautifulsoup4`,
`jupyter`, `nbconvert`
