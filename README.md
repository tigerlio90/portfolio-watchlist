# Portfolio Watchlist – Investment Cockpit V3

## Enthalten
- aktuelle Kurse
- 1T / 1M / YTD / 1J Performance
- Volatilität
- nächste Earnings
- News je Unternehmen
- Watchlist Score 1–10
- Ampel: Buy / Hold / Watch / Reduce / Sell
- Alerts für starke Tagesverluste, Earnings und niedrige Scores
- Public Mode für teilbare Ansicht
- Performance-Charts und Detailseiten

## Score-Logik
Der Score ist bewusst einfach und transparent:
- Momentum 1M / YTD / 1J
- Volatilität
- kurzfristiger Earnings-Risikohinweis
- Basisscore 5, begrenzt auf 1–10

Er ist keine Anlageempfehlung.

## Lokal starten
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Veröffentlichung
1. GitHub Repository erstellen.
2. `app.py` und `requirements.txt` hochladen.
3. Streamlit Community Cloud öffnen.
4. "Create app" auswählen.
5. Repository, Branch und `app.py` auswählen.
6. Deployen.
7. Den erzeugten `streamlit.app` Link teilen.

## Wichtiger Hinweis
Die Alerts sind In-App-Alerts. Für automatische E-Mail-/Push-Benachrichtigungen muss zusätzlich ein Scheduler oder externer Dienst angebunden werden.
