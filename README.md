# 🚦 GateFlow

### A Developer-Focused API Gateway Built with Python, FastAPI, Redis & PostgreSQL

GateFlow is a backend-focused API Gateway project designed to simplify communication between multiple microservices through a centralized gateway.

It provides request routing, API key authentication, Redis-powered rate limiting, usage analytics, persistent route management, and role-based admin access.

The project is being developed milestone by milestone, with an emphasis on practical backend engineering, scalable architecture, security, and observability.

---

## 🧭 Project Progress

**Current progress: Milestones 1.1 – 3.4 completed**

### 🟢 Milestone 1 — Gateway Foundation

<details>
<summary><strong>1.1 — Project Setup & Architecture</strong></summary>

- Created the GateFlow project structure.
- Set up the Python development environment.
- Organized the gateway and independent backend services.
- Configured Docker-based development.

</details>

<details>
<summary><strong>1.2 — FastAPI Gateway</strong></summary>

- Built the central FastAPI application.
- Added a health-check endpoint.
- Configured application startup and shutdown using lifespan events.
- Set up CORS for frontend integration.

</details>

<details>
<summary><strong>1.3 — Reverse Proxy</strong></summary>

- Implemented asynchronous HTTP forwarding using HTTPX.
- Forwarded incoming requests to their destination services.
- Preserved query parameters and relevant headers.
- Filtered hop-by-hop HTTP headers.
- Added gateway response metadata.

</details>

<details>
<summary><strong>1.4 — Microservices Integration</strong></summary>

- Created an independent User Service.
- Created an independent Product Service.
- Connected both services through the gateway.
- Tested service endpoints and request forwarding.

</details>

<details>
<summary><strong>1.5 — Request Metadata & Error Handling</strong></summary>

- Added gateway latency tracking.
- Added `X-GateFlow-Latency` and `X-GateFlow-Status` response headers.
- Implemented route-not-found and method-validation handling.
- Verified gateway health and service responses.

</details>

### 🟢 Milestone 2 — Dynamic Route Management & Persistence

<details>
<summary><strong>2.1 — Dynamic Route Registry</strong></summary>

- Implemented a centralized route registry.
- Added path-prefix matching.
- Supported HTTP method validation.
- Implemented longest-prefix route matching.

</details>

<details>
<summary><strong>2.2 — Route Administration</strong></summary>

Implemented administrative endpoints for managing gateway routes:

- `GET /gateway/admin/routes`
- `POST /gateway/admin/routes`
- `PUT /gateway/admin/routes/{name}`
- `DELETE /gateway/admin/routes/{name}`

</details>

<details>
<summary><strong>2.3 — PostgreSQL Integration</strong></summary>

- Integrated PostgreSQL using SQLAlchemy.
- Created persistent API route storage.
- Added database initialization and route persistence.

</details>

<details>
<summary><strong>2.4 — Persistent Route Loading</strong></summary>

- Loaded routes from PostgreSQL during gateway startup.
- Saved dynamically registered routes.
- Verified that registered routes survived gateway restarts.

</details>

### 🟢 Milestone 3 — Security, Traffic Control & Analytics

<details>
<summary><strong>3.1 — API Key Authentication</strong></summary>

- Implemented API key generation.
- Added API key hashing using SHA-256.
- Stored API key hashes rather than raw keys.
- Added request authentication through `X-API-Key`.
- Implemented API key creation, listing, and revocation.

</details>

<details>
<summary><strong>3.2 — Redis Rate Limiting</strong></summary>

- Integrated Redis into the gateway.
- Implemented atomic rate limiting using a Redis Lua script.
- Configured a limit of 100 requests per API key per 60-second window.
- Added rate-limit response headers.
- Implemented HTTP 429 responses when limits are exceeded.
- Added fail-closed behavior when Redis is unavailable.

**Verified:** A 101-request test resulted in 100 successful requests followed by a rate-limit response.

</details>

<details>
<summary><strong>3.3 — Usage Analytics</strong></summary>

- Created persistent API request logs.
- Recorded API key ID, HTTP method, path, status code, latency, and timestamp.
- Added analytics endpoints for:
  - Traffic overview
  - Request traffic over time
  - Endpoint usage
  - API key usage
  - HTTP status-code distribution

</details>

<details>
<summary><strong>3.4 — Admin Authentication & Role-Based Access Control</strong></summary>

- Implemented administrator accounts.
- Added password hashing with Argon2.
- Implemented JWT-based authentication.
- Added login, registration, and current-admin endpoints.
- Implemented three roles:
  - `super_admin`
  - `admin`
  - `viewer`
- Added role-based authorization for route management, API keys, and analytics.
- Protected administrative endpoints against unauthenticated access.

</details>

---

## 🏗️ Architecture

```text
                    ┌──────────────────────┐
                    │    Client / Frontend │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    GateFlow Gateway  │
                    │       FastAPI        │
                    ├──────────────────────┤
                    │ Reverse Proxy        │
                    │ API Key Auth         │
                    │ Rate Limiting        │
                    │ Route Registry       │
                    │ Request Logging      │
                    └───┬────────┬─────────┘
                        │        │
               ┌────────▼───┐ ┌──▼────────────┐
               │ User       │ │ Product       │
               │ Service    │ │ Service       │
               │ :8002      │ │ :8003         │
               └────────────┘ └───────────────┘

                    ┌──────────────────────┐
                    │      PostgreSQL      │
                    │ Routes, Admins, Logs │
                    └──────────────────────┘

                    ┌──────────────────────┐
                    │        Redis         │
                    │    Rate Limiting     │
                    └──────────────────────┘
```

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend development |
| FastAPI | API Gateway and services |
| HTTPX | Asynchronous HTTP forwarding |
| PostgreSQL | Persistent storage |
| SQLAlchemy | Database ORM |
| Redis | Rate limiting |
| PyJWT | JWT authentication |
| Argon2 | Password hashing |
| Docker | Containerization |
| Docker Compose | Multi-service orchestration |
| React + Vite | Dashboard foundation |

## 📁 Project Structure

```text
GateFlow/
│
├── backend-services/
│   ├── user-service/
│   └── product-service/
│
├── dashboard/
│   ├── public/
│   └── src/
│
├── gateway/
│   ├── admin/
│   ├── analytics/
│   ├── core/
│   ├── middleware/
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── rate_limiter.py
│   └── security.py
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## 🚀 Getting Started

### Prerequisites

Make sure you have:

- Python 3.11+
- Docker Desktop
- Docker Compose
- Node.js and npm (for dashboard development)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/iamSunnyrohit/GateFlow.git
cd GateFlow
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Update `.env` with the required configuration for your local environment.

**Security:** Never commit `.env` or publish real API keys, database passwords, or JWT secrets.

### 3. Start the backend services

```bash
docker compose up --build -d
```

### 4. Check running containers

```bash
docker compose ps
```

### 5. Check gateway health

```bash
curl http://localhost:8000/health
```

### 6. Explore API documentation

Open the FastAPI Swagger documentation:

http://localhost:8000/docs

## 🔌 API Endpoints

### Gateway

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Gateway health check |
| GET | `/api/users` | Forward to User Service |
| GET | `/api/products` | Forward to Product Service |

### Administration

| Method | Endpoint | Description |
|---|---|---|
| GET | `/gateway/admin/routes` | List routes |
| POST | `/gateway/admin/routes` | Register route |
| PUT | `/gateway/admin/routes/{name}` | Update route |
| DELETE | `/gateway/admin/routes/{name}` | Delete route |
| POST | `/gateway/admin/api-keys` | Create API key |
| GET | `/gateway/admin/api-keys` | List API keys |
| DELETE | `/gateway/admin/api-keys/{key_id}` | Revoke API key |

### Admin Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/gateway/admin/auth/register` | Register administrator |
| POST | `/gateway/admin/auth/login` | Admin login |
| GET | `/gateway/admin/auth/me` | Current admin profile |

### Analytics

| Method | Endpoint | Description |
|---|---|---|
| GET | `/gateway/admin/analytics/overview` | Traffic overview |
| GET | `/gateway/admin/analytics/traffic` | Traffic over time |
| GET | `/gateway/admin/analytics/endpoints` | Endpoint analytics |
| GET | `/gateway/admin/analytics/api-keys` | API key analytics |
| GET | `/gateway/admin/analytics/status-codes` | Status-code analytics |

**Authentication notes:**

- Protected service endpoints require an API key through `X-API-Key`.
- Administrative endpoints require a valid administrator JWT.
- Administrative permissions depend on the assigned role.

## 🗺️ Roadmap

| Milestone | Description | Status |
|---|---|---|
| 1 | Gateway Foundation | ✅ Complete |
| 2 | Dynamic Routing & Persistence | ✅ Complete |
| 3 | Security, Rate Limiting & Analytics | ✅ Complete |
| 4 | Advanced Gateway Features | 🔜 Planned |
| 5 | Monitoring & Observability | 🔜 Planned |
| 6 | React Admin Dashboard | 🔜 Planned |
| 7 | Testing & Production Hardening | 🔜 Planned |
| 8 | Deployment & Documentation | 🔜 Planned |

### What's next?

The next development phase will focus on advanced gateway capabilities, beginning with a **Circuit Breaker Pattern** to improve resilience when downstream microservices become unavailable.

## 🎯 Project Goals

GateFlow is being developed to explore practical concepts in backend engineering:

- Microservices architecture
- API gateway design
- Asynchronous request forwarding
- Authentication and authorization
- Distributed rate limiting
- Database persistence
- Traffic analytics
- Fault tolerance
- Containerized deployment

## 👨‍💻 Development

Built incrementally as a hands-on backend engineering project.

**Developer:** [@iamSunnyrohit](https://github.com/iamSunnyrohit)

**Repository:** [GateFlow](https://github.com/iamSunnyrohit/GateFlow)

---

⭐ If you find this project interesting, consider giving it a star!

*GateFlow — One Gateway. Multiple Services. Centralized Control.*