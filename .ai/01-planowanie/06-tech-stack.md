# Stack Technologiczny - Pathie (MVP)

### **Frontend**

* **Framework:** **React 19**
    * **Opis:** Aplikacja kliencka w architekturze SPA (Single Page Application).

* **Język:** **TypeScript 5**
    * **Opis:** Statyczne typowanie dla całego kodu frontendowego.

* **Narzędzie budowania:** **Vite**
    * **Opis:** Nowoczesny bundler i serwer deweloperski.

* **Styling:** **Tailwind CSS 4**
    * **Opis:** Framework CSS typu utility-first.

* **Biblioteki dodatkowe:**
    * **Routing:** **React Router** - standard do nawigacji po stronie klienta.
    * **Mapy:** **React Leaflet** - integracja popularnej biblioteki map Leaflet.js z Reactem.
    * **Komponenty UI:** **Shadcn/ui** (lub podobne) - baza gotowych, dostępnych komponentów UI.

### **Backend**

* **Framework:** **Django 5**
    * **Opis:** Główna logika aplikacji, API i zarządzanie użytkownikami.

* **API:** **Django REST Framework (DRF)**
    * **Opis:** Warstwa do budowy REST API dla komunikacji z frontendem.

* **Baza Danych:** **PostgreSQL 16**
    * **Opis:** Relacyjna baza danych.

* **Optymalizacja tras:** **OpenRouteService API**
    * **Opis:** Zewnętrzne API do obliczania i optymalizacji kolejności punktów na trasie.

### **Sztuczna Inteligencja (AI)**

* **Dostawca Modeli:** **OpenRouter.ai**
    * **Opis:** Brama (gateway) do różnych modeli językowych (LLM).

### **Zadania Asynchroniczne**

* **Framework:** **Celery**
    * **Opis:** Biblioteka do uruchamiania zadań w tle.

* **Broker wiadomości:** **Redis**
    * **Opis:** Wewnątrz-pamięciowa baza danych używana jako pośrednik wiadomości dla Celery.

### **Infrastruktura i DevOps**

* **Hosting:** **Prywatny serwer VPS (np. DigitalOcean, Hetzner, OVH)**
    * **Opis:** Dedykowana maszyna wirtualna do hostowania aplikacji.

* **Konteneryzacja:** **Docker & Docker Compose**
    * **Opis:** Uruchomienie wszystkich części aplikacji (frontend, backend, baza danych, Redis) w osobnych kontenerach.

* **CI/CD:** **GitHub Actions**
    * **Opis:** Zautomatyzowane procesy testowania i wdrażania.

* **Serwer Web/Proxy:** **Nginx**
    * **Opis:** Używany jako reverse proxy dla aplikacji Django oraz do serwowania statycznych plików frontendu.
    * **Uzasadnienie:** Wysoka wydajność, standard branżowy.