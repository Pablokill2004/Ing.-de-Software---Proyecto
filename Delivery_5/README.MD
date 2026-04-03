# Django-realworld-example | Delivery 5: Quality Polish & Final Handover



## 1. Resumen del Delivery 5

El Delivery 5 cierra el ciclo de optimización iniciado en el Delivery 4 (ADR: migración SQLite → PostgreSQL) con una demostración empírica de mejora de rendimiento sobre el endpoint más crítico del sistema.

| Área | Responsable | Resultado |
|---|---|---|
| Refactorización N+1 (Optimizer) | Estudiante A | 97.5% reducción de queries BD |
| Benchmarking Locust (Analyst) | Estudiante B | −18.3% latencia P95, datos Before/After |
| Documentación & Handover (Quality Lead) | Estudiante C | README, badges, análisis técnico PDF |



## 2. Archivos entregados en este Delivery

```
Delivery_5/
├── README.md                          ← Este archivo
├── Benchmark.md                       ← Comparativa Before/After (Estudiante B)
├── FINOPS_OPTIMIZATION.md             ← Análisis técnico de optimización (Estudiante A)
├── Locust_Settings_Documentation.md   ← Guía de ejecución de pruebas Locust
├── Delivery-5-Quality-Polish.pdf      ← Análisis técnico completo (Estudiante C)
├── Baseline-Locust-Outcomes/          ← Resultados de pruebas ANTES de optimización
│   ├── Locust-Diagrams-Overview-BASELINE.png
│   ├── Locust_BASELINE_requests.csv
│   ├── Locust_Test_Report_BASELINE.html
│   ├── number_of_users_BASELINE.png
│   ├── response_times_(ms)_BASELINE.png
│   └── total_requests_per_second_BASELINE.png
└── Optimized-Locust-Outcomes/         ← Resultados de pruebas DESPUÉS de optimización
    ├── Locust-Diagrams-Overview-Optimized.png
    ├── Locust_OPTIMIZED_requests.csv
    ├── Locust_Test_Report_OPTIMIZED.html
    ├── number_of_users_OPTIMIZED.png
    ├── response_times_(ms)_OPTIMIZED.png
    └── total_requests_per_second_OPTIMIZED.png
```



## 3. Problema Identificado y Solucionado

**Patrón N+1 en `GET /api/articles/`** — El endpoint de lista de artículos del proyecto original ([`gothinkster/django-realworld-example-app`](https://github.com/gothinkster/django-realworld-example-app)) generaba **~81 consultas SQL** por cada request de 20 artículos.

### Raíz del problema

| Archivo afectado | Línea | Problema |
|---|---|---|
| [`conduit/apps/articles/views.py`](https://github.com/gothinkster/django-realworld-example-app/blob/master/conduit/apps/articles/views.py) | ~35 | Queryset base sin `prefetch_related` ni anotaciones |
| [`conduit/apps/articles/serializers.py`](https://github.com/gothinkster/django-realworld-example-app/blob/master/conduit/apps/articles/serializers.py) | ~71 | `favorited_by.count()` — 1 query por artículo |
| [`conduit/apps/profiles/serializers.py`](https://github.com/gothinkster/django-realworld-example-app/blob/master/conduit/apps/profiles/serializers.py) | ~40 | `is_following()` — 1 query por autor |
| [`conduit/apps/authentication/backends.py`](https://github.com/gothinkster/django-realworld-example-app/blob/master/conduit/apps/authentication/backends.py) | ~30 | `User.objects.get(pk=...)` sin `select_related('profile')` |



## 4. Cambios de Optimización (Estudiante A)

Los cambios se aplicaron en el branch `finops/n-plus-one-query-optimization`. Descripción técnica completa en [`FINOPS_OPTIMIZATION.md`](FINOPS_OPTIMIZATION.md).

### `conduit/apps/articles/views.py`
- **`prefetch_related('tags')`** — elimina 20 queries individuales de tags
- **`annotate(favorites_count=Count('favorited_by'))`** — mueve el COUNT al SQL principal
- **`_build_list_context()`** — pre-computa `favorite_article_ids` y `following_profile_ids` como sets Python (2 queries totales)
- **`select_related` en `get_article_by_slug()`** — optimiza endpoints de detalle

### `conduit/apps/articles/serializers.py`
- `get_favorited()` → lookup `O(1)` en set precalculado, sin query por artículo
- `get_favorites_count()` → lee anotación `instance.favorites_count`, sin `COUNT(*)` por artículo

### `conduit/apps/profiles/serializers.py`
- `get_following()` → lookup `O(1)` en `following_profile_ids`, sin query por autor

### `conduit/apps/authentication/backends.py`
- `select_related('profile')` en el lookup JWT — elimina 1 query extra por request autenticado



## 5. Resultados del Benchmark (Estudiante B)

Pruebas ejecutadas con **Locust** · 50 usuarios concurrentes · 120 segundos · endpoint `/api/articles?limit=20`.

### Resultados de rendimiento de carga (Locust)

| Métrica | Baseline | Optimizado | Mejora |
|---|---|---|---|
| **Requests Per Second** | 50.12 req/s | 50.36 req/s | +0.5% |
| **Latencia Promedio** | 25.45 ms | 20.79 ms | **−18.3%** |
| **P95 Response Time** | 68 ms | 57 ms | **−16.2%** |

### Resultados del benchmark de queries (script `benchmark_queries.py`)

| Métrica | Antes | Después | Mejora |
|---|---|---|---|
| **Consultas BD por request** | 81 | 2 | **−97.5%** |
| **Tiempo de respuesta** | 123 ms | 6 ms | **−95.0%** |

📊 Reportes HTML completos:
- [Locust Test Report — BASELINE](Baseline-Locust-Outcomes/Locust_Test_Report_BASELINE.html)
- [Locust Test Report — OPTIMIZADO](Optimized-Locust-Outcomes/Locust_Test_Report_OPTIMIZED.html)



## 6. Análisis FinOps

La reducción del 97.5% en queries se traduce directamente en menor uso de CPU en la base de datos. En un entorno AWS RDS:

| Escenario | Instancia | Costo mensual estimado |
|---|---|---|
| **Antes** (81 queries/request) | `db.t3.medium` ($0.068/hr) | ~$49/mes |
| **Después** (2 queries/request) | `db.t3.micro` ($0.017/hr) | ~$12/mes |
| **Ahorro teórico** | — | **~75% reducción** |



## 7. Análisis técnico completo (PDF)

El análisis detallado con evidencia, métricas consolidadas y recomendaciones para producción se documenta en:

[Delivery-5-Quality-Polish.pdf](Delivery-5-Quality-Polish.pdf)



## 8. Estado del repositorio — Handover Checklist

| Item | Estado |
|---|---|
|  N+1 corregido en `articles/views.py` | Completado |
| Serializadores optimizados (articles + profiles) | Completado |
| JWT backend con `select_related` | Completado |
| Compatibilidad Django 4.x corregida (`url()` → `re_path()`) | Completado |
| Dockerfile actualizado a Python 3.11 | Completado |
| Benchmark Before/After documentado (Locust) | Completado |
| Benchmark de queries documentado (`benchmark_queries.py`) | Completado |
| README actualizado con badges | Completado |
| PDF de análisis técnico generado | Completado |

---

## 9. Referencia al Repositorio Original

Este proyecto es un fork de análisis académico del repositorio:

> **[gothinkster/django-realworld-example-app](https://github.com/gothinkster/django-realworld-example-app)**

Todos los cambios de optimización se realizaron sobre la rama `finops/n-plus-one-query-optimization`. Los archivos clave modificados son:

- [`conduit/apps/articles/views.py`](https://github.com/gothinkster/django-realworld-example-app/blob/master/conduit/apps/articles/views.py)
- [`conduit/apps/articles/serializers.py`](https://github.com/gothinkster/django-realworld-example-app/blob/master/conduit/apps/articles/serializers.py)
- [`conduit/apps/profiles/serializers.py`](https://github.com/gothinkster/django-realworld-example-app/blob/master/conduit/apps/profiles/serializers.py)
- [`conduit/apps/authentication/backends.py`](https://github.com/gothinkster/django-realworld-example-app/blob/master/conduit/apps/authentication/backends.py)

