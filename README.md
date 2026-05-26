# football-stats-analysis

# Setup-Anleitung
Schritt-für-Schritt Anleitung zur lokalen Installation und Ausführung des Projekts --> für Mac und Windows
## Mac

### Voraussetzungen
- [ ] [Homebrew](https://brew.sh) installiert
- [ ] [VS Code](https://code.visualstudio.com) installiert
- [ ] [Git](https://git-scm.com) installiert

### Schritte

**1. Repository klonen**
```bash
git clone https://github.com/zeitmann/football-stats-analysis
cd football-stats-analysis
```

**2. Python installieren**
```bash
brew install python
```

**3. Virtuelle Umgebung erstellen & aktivieren**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**4. Pakete installieren**
```bash
pip3 install -r requirements.txt
```

**5. .env Datei erstellen**
```bash
echo "FOOTBALL_API_KEY=dein_key_hier" > .env
echo "OPENAI_API_KEY=dein_key_hier" >> .env
```
> API Keys: [football-data.org](https://www.football-data.org) (kostenlos) und [OpenAI](https://platform.openai.com/api-keys)

**6. Notebooks ausführen** *(in dieser Reihenfolge!)*
- [ ] `notebooks/01_data_collection.ipynb` → Run All
- [ ] `notebooks/02_data_preparation.ipynb` → Run All
- [ ] `notebooks/03_analysis_visualization.ipynb` → Run All
- [ ] `notebooks/04_llm_analysis.ipynb` → Run All

**7. Web-App starten**
```bash
python3 app/app.py
```

**8. Im Browser öffnen**
```
http://localhost:5001
```

---

## Windows

### Voraussetzungen
- [ ] [Python](https://python.org/downloads) installiert *(beim Installieren "Add Python to PATH" ankreuzen!)*
- [ ] [VS Code](https://code.visualstudio.com) installiert
- [ ] [Git](https://git-scm.com) installiert

### Schritte

**1. Repository klonen**
```powershell
git clone https://github.com/zeitmann/football-stats-analysis
cd football-stats-analysis
```

**2. Pakete installieren**
```powershell
python -m pip install -r requirements.txt
```

**3. .env Datei erstellen**

Erstelle im Root-Ordner eine neue Datei namens `.env` mit folgendem Inhalt:
```
FOOTBALL_API_KEY=dein_key_hier
OPENAI_API_KEY=dein_key_hier
```
> API Keys: [football-data.org](https://www.football-data.org) (kostenlos) und [OpenAI](https://platform.openai.com/api-keys)

**4. Notebooks ausführen** *(in dieser Reihenfolge!)*
- [ ] `notebooks/01_data_collection.ipynb` → Run All
- [ ] `notebooks/02_data_preparation.ipynb` → Run All
- [ ] `notebooks/03_analysis_visualization.ipynb` → Run All
- [ ] `notebooks/04_llm_analysis.ipynb` → Run All

**5. Web-App starten**
```powershell
python app/app.py
```

**6. Im Browser öffnen**
```
http://localhost:5001
```

---

## Wichtige Hinweise

- Die `.env` Datei **niemals** auf GitHub pushen — sie ist in `.gitignore` eingetragen
- Notebooks **immer in der richtigen Reihenfolge** ausführen — jedes Notebook baut auf dem vorherigen auf
- Falls `pip` nicht erkannt wird (Windows): `python -m pip` statt `pip` verwenden
- Falls Port 5001 besetzt ist (Mac): AirPlay Receiver unter *Systemeinstellungen → Allgemein → AirDrop & Handoff* deaktivieren