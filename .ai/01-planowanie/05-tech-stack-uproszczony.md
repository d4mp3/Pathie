# 🧩 Stack Technologiczny – Pathie (MVP, uproszczony monolit Django)

## 🎯 Cel uproszczenia
Celem tego wariantu jest **maksymalne skrócenie czasu dostarczenia MVP**, przy zachowaniu:
- pełnej funkcjonalności wymaganej przez PRD,
- spójności architektonicznej,
- bezpieczeństwa i stabilności wdrożenia.

Architektura monolityczna pozwoli skupić się na **walidacji hipotezy produktu**

---

## 🖥️ **Frontend + Backend (monolit)**

### **Framework:** `Django 5`
**Rola:** Jednolity serwer aplikacji (frontend + backend).
**Uzasadnienie:**
- Wbudowany ORM, system autoryzacji i routing.
- Brak konieczności utrzymywania osobnego serwera API.
- Szybkie iteracje dzięki Django Templates i HTMX.

---

### **Warstwa prezentacji (frontend)**

| Technologia | Opis | Uzasadnienie |
|--------------|------|--------------|
| **Django Templates** | System renderowania HTML po stronie serwera. | Pozwala na prosty, szybki rozwój bez build stepu. |
| **HTMX** | Dodaje asynchroniczne interakcje (AJAX, partial reloads) bez SPA. | Zapewnia nowoczesne UX bez złożoności Reacta. |
| **Alpine.js** *(opcjonalnie)* | Lekka warstwa logiki po stronie klienta (np. modale, przełączniki). | Brak konieczności stosowania frameworka JS. |
| **Tailwind CSS 4** | Framework CSS typu utility-first. | Umożliwia szybkie stylowanie i Mobile-First design. |
| **Django Leaflet** | Biblioteka mapowa JS. | Interaktywne mapy z minimalną konfiguracją i bez kosztów licencji. |

---

## ⚙️ **Warstwa logiki i danych**

| Komponent | Technologia | Uzasadnienie |
|------------|--------------|--------------|
| **Baza danych** | **PostgreSQL 16** | Stabilna, open-source’owa baza relacyjna z obsługą danych przestrzennych (PostGIS w przyszłości). |
| **ORM i modele** | **Django ORM** | Umożliwia szybkie definiowanie modeli tras, punktów, użytkowników i opisów. |
| **Uwierzytelnianie** | **Django Auth + django-allauth (OAuth Google)** | Obsługuje zarówno logowanie lokalne, jak i przez Google, zgodnie z PRD. |
| **Buforowanie danych** | **Django cache (local memory lub file-based)** | Wystarczające do cache’owania tras i opisów w MVP (bez Redis). |

---

## 🧠 **Integracje AI i zewnętrzne**

| Komponent | Technologia | Uzasadnienie |
|------------|--------------|--------------|
| **Generowanie tras i opisów** | **OpenRouter.ai API** | Dostarcza modele LLM do generowania tras i narracji. |
| **Optymalizacja tras** | **OpenRouteService API** | Zewnętrzne API do obliczania kolejności punktów i dystansu. |
| **Źródła danych** | **Wikipedia API, OpenStreetMap** | Zasoby do wzbogacania opisów punktów. |

---
