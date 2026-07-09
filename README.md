# zeichen-luessum

Tier-Icons und Ausmalbilder für Kinder.

## Ordner

- `tiere/` – farbige Tier-Illustrationen (2048×2048 px, transparenter Hintergrund)
- `ausmalbilder/` – A4-Ausmalbilder (2480×3508 px, 300 DPI) mit deutschem Tiernamen

## Ausmalbilder neu generieren

```bash
pip install -r scripts/requirements.txt
python3 scripts/create_all_coloring_pages.py
```

Ergebnis: je ein PNG pro Tier in `ausmalbilder/` sowie `ausmalbilder/alle-ausmalbilder.pdf` mit allen 46 Seiten.

Einzelnes Tier:

```bash
python3 scripts/create_coloring_pages.py tiere/hase.png ausmalbilder/hase.png --name "Hase"
```
