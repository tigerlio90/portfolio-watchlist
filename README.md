# Investment Cockpit V9 Mobile

Mobile-first version designed specifically around a 375px-wide iPhone 7 viewport.

Design:
- Erste-inspired navy/blue/white palette matching the approved mobile mockup
- large touch targets
- horizontal swipeable market cards
- bottom tab navigation
- no desktop sidebar
- compact news and watchlist cards
- add/delete securities from mobile
- Flask/HTML/CSS/JS, no Streamlit WebSocket

Render start command:
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
