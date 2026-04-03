# Django-realworld-example | Delivery 4: Data Arguments & QA Validation

## *Argumentos Basados en Datos para ADR-001*

Para esta parte puede ver el siguiente archivo [Ver ADR-001-DataArguments-QA](ADR-001-DataArguments-QA.md)

### 1. Benchmarks de Rendimiento
¿Por qué?: Se necesitaba justificar con datos cuantitativos por qué PostgreSQL supera a SQLite en el contexto del proyecto.

Por lo que se recopilaron benchmarks de la industria que muestran una diferencia de 100x en TPS (SQLite ~100 TPS vs PostgreSQL >10,000 TPS), directamente relevante para los endpoints de `favorites` y `follows` del proyecto que ejecutan escrituras M2M concurrentes en `profiles/models.py:44–70`.

### 2. Análisis de CVEs (NVD 2020–2025)
¿Por qué?: La decisión arquitectónica tiene implicaciones de seguridad que deben respaldarse con datos reales, no solo con opiniones.

Se consultó la National Vulnerability Database para comparar la superficie de ataque de ambos motores: SQLite acumula 47 CVEs publicados vs 12 de PostgreSQL 15, con los CVEs críticos de SQLite (CVE-2022-35737, CVE-2023-36191) involucrando corrupción de memoria mediante SQL malformado — especialmente riesgoso cuando la BD reside como archivo dentro del contenedor web.

### 3. Comparativa de Costos en Nube (AWS/Azure/GCP)
¿Por qué?: Se necesitaba responder concretamente cuánto costaría migrar, para que la decisión tenga sustento financiero además de técnico.

Se levantaron precios actuales de AWS RDS, Azure Database for PostgreSQL y Google Cloud SQL, con rangos desde $0 (Docker local / Supabase free) hasta ~$50 USD/mes (producción), concluyendo que la migración recupera su costo de 2 días-desarrollador en el primer despliegue al eliminar el riesgo de pérdida de datos.

## *Validación QA — Setup de la Persona A*

Para esta parte puede ver el siguiente archivo [Ver ADR-001-DataArguments-QA](ADR-001-DataArguments-QA.md)

### Verificación del One-Command Setup
¿Por qué?: Como rol de QA, se necesita confirmar independientemente que el entorno de la Persona A funciona desde cero antes de que el equipo lo adopte.

Se validaron 6 pasos críticos (build limpio, migraciones automáticas, disponibilidad del servidor, persistencia de datos, compatibilidad Windows y cache de Docker) en una máquina sin dependencias previas más allá de Docker Desktop. Todos los pasos pasaron. La decisión de usar `python:3.6-slim` es correcta y necesaria para la compatibilidad con Django 1.10.5.