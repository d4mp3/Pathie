
**Charakterystyka:**
- Jeden serwer aplikacji (Gunicorn + Nginx jako reverse proxy).
- Komunikacja synchroniczna (brak Celery).
- API tylko tam, gdzie to konieczne (np. `/ai/generate_route/`).

---

## 🧰 **Infrastruktura i DevOps**

| Element | Technologia | Uzasadnienie |
|----------|--------------|--------------|
| **Konteneryzacja** | **Docker + Docker Compose** | Uruchomienie Django + PostgreSQL w dwóch kontenerach. |
| **Hosting** | **VPS (DigitalOcean / Hetzner / OVH)** | Tani i elastyczny hosting dla MVP. |
| **Serwer WWW / Proxy** | **Nginx** | Reverse proxy + serwowanie statycznych plików. |
| **CI/CD** | **GitHub Actions (prosty pipeline)** | Automatyczne testy i deployment po merge. |

---

## 🔐 **Bezpieczeństwo**

- HTTPS wymuszony przez Nginx (Let's Encrypt).
- Django CSRF i XSS Protection – domyślnie aktywne.
- Oddzielny plik `.env` z danymi konfiguracyjnymi (API keys, sekrety).
- OAuth 2.0 (Google) poprzez `django-allauth`.
- Regularne aktualizacje pakietów (dependabot lub `pip-audit`).

---

## 📊 **Korzyści uproszczonego podejścia**

| Obszar | Efekt uproszczenia |
|--------|--------------------|
| **Czas wdrożenia** | Redukcja o ok. 30–50% w porównaniu z React + DRF. |
| **Koszt utrzymania** | 1 kontener z aplikacją + DB – minimalna infrastruktura. |
| **Bezpieczeństwo** | Mniej punktów integracji = mniejsze ryzyko luk. |
| **UX / interaktywność** | Zachowana dzięki HTMX + Leaflet. |
| **Rozszerzalność** | Możliwość płynnego przejścia do SPA w przyszłości (z API). |

---

## 🚀 **Plan ewolucji po MVP**

| Etap | Dodatek | Cel |
|------|----------|-----|
| **Faza 1 (MVP)** | Monolit Django (HTMX, Leaflet) | Walidacja produktu i UX. |
| **Faza 2** | Redis + Celery | Kolejkowanie generacji tras i opisów. |
| **Faza 3** | Oddzielenie frontendu (React / Next.js) | Skalowanie i rozwój funkcji społecznościowych. |
| **Faza 4** | PostGIS + analityka przestrzenna | Optymalizacje i rekomendacje tras. |

---

## 🧭 **Podsumowanie**

Uproszczony stack Django monolitowy pozwala:
- **szybko zbudować i zweryfikować MVP,**
- **zachować wysokie bezpieczeństwo i elastyczność,**
- **uniknąć zbędnej złożoności technicznej,**
- **pozostać kompatybilnym z przyszłym rozwojem.**

To rozwiązanie stanowi **najlepszy balans** między czasem wdrożenia, kosztem i możliwością rozbudowy.

---
