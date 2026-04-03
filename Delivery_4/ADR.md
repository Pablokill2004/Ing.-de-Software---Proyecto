# ADR-001: Migración de SQLite a PostgreSQL

**Estado:** Propuesto
**Fecha:** 2026-03-15
**Autores:** Equipo de Ingeniería de Conduit
**Decisores:** Tech Lead, Equipo Backend
**Ticket:** N/A

---

## 1. Contexto

### 1.1 Estado Actual

La aplicación Conduit (`django-realworld-example-app-master`) es un monolito Django REST Framework que expone una API REST para artículos, autenticación de usuarios y perfiles sociales. La configuración actual de base de datos, ubicada en `conduit/settings.py:86–91`, es la siguiente:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
```

SQLite fue apropiado durante el desarrollo inicial y la exploración académica. El proyecto incluye actualmente:

- Un **Dockerfile** y un **docker-compose.yml** en la raíz del repositorio, lo que indica la intención de ejecutar la aplicación en entornos contenerizados o similares a producción.
- Una **integración con SonarQube** (`sonar-project.properties`) y un **SBOM** (`sbom.json`), señalando madurez hacia un pipeline de producción (Entrega 3 — DevSecOps).
- Una **auditoría de vulnerabilidades** (commit `3e7f864`) que fortaleció el control de acceso a nivel de API, pero la capa de persistencia no ha sido revisada para producción.

### 1.2 Planteamiento del Problema

SQLite es un motor de base de datos sin servidor basado en un único archivo. Sus restricciones de diseño lo hacen inadecuado como backend de producción para cualquier aplicación que sirva más de un escritor concurrente. Los siguientes problemas concretos surgen del código base:

| Restricción | Evidencia en el Código | Impacto |
|---|---|---|
| **Bloqueo de escritor único** | `ArticlesFeedAPIView` consulta `Article.objects.filter(author__in=...)` (views.py:233–236); lecturas concurrentes del feed mientras hay una escritura en curso causan errores `database is locked` | El endpoint de feed con alta carga de lectura generará bloqueos bajo usuarios concurrentes |
| **Sin bloqueo a nivel de fila** | `Profile.follow()` y `Profile.favorite()` llaman a `.add()` sobre relaciones M2M (profiles/models.py:44–46, 60–62) sin transacción explícita — las condiciones de carrera producen filas duplicadas o perdidas | Violaciones de integridad de datos a escala |
| **E/S basada en archivo** | `db.sqlite3` reside dentro del sistema de archivos del contenedor | Los datos se destruyen al reiniciar el contenedor; incompatible con escalado horizontal o despliegues efímeros |
| **Sin connection pooling** | El backend `sqlite3` de Django no soporta `CONN_MAX_AGE` ni pooling | Bajo carga, cada solicitud abre y cierra el archivo; picos de latencia |
| **Búsqueda de texto limitada** | El filtrado por tags usa `queryset.filter(tags__tag=tag)` (views.py:49) — solo coincidencia exacta | No puede soportar búsqueda con ILIKE, trigramas o `tsvector` que los usuarios esperan |
| **Django 1.10 desactualizado** | `settings.py:11` referencia la documentación de Django 1.10; actualizar a una versión soportada está parcialmente bloqueado por la necesidad de alinear primero el backend de base de datos | Deuda de seguridad y mantenimiento |

### 1.3 Factores de Decisión

1. **Correctitud** — Eliminar condiciones de carrera en escrituras M2M (`favorites`, `follows`).
2. **Desplegabilidad** — Alinear con la configuración Docker existente; la aplicación debe sobrevivir reinicios del contenedor.
3. **Escalabilidad** — Soportar al menos dos instancias de la aplicación en paralelo sin fallas de serialización de escritura.
4. **Seguridad** — Reducir la superficie de ataque de una base de datos basada en archivo (path traversal, filtración de backups).
5. **Mantenibilidad** — Habilitar la futura migración a versiones soportadas de Django sin fricción de base de datos.

---

## 2. Opciones Consideradas

### Opción A: Mantener SQLite + modo WAL (statu quo / corrección incremental)

Habilitar Write-Ahead Logging (`PRAGMA journal_mode=WAL`) para permitir un escritor y múltiples lectores concurrentes.

**Por qué se rechaza:**
El modo WAL no elimina el bloqueo a nivel de archivo para operaciones de escritura. Las condiciones de carrera en M2M sobre `Profile.follows` y `Profile.favorites` persisten. Además, el problema del archivo dentro del contenedor no se resuelve. Esto es un parche, no una solución. Ningún despliegue de Django en producción establicido usa SQLite como almacenamiento primario.

### Opción B: Migrar a MySQL / MariaDB

Una base de datos relacional ampliamente conocida con soporte de alojamiento extendido.

**Por qué se rechaza:**
El nivel de aislamiento de transacciones por defecto de MySQL (`REPEATABLE READ`) y su manejo histórico de codificación `utf8` vs `utf8mb4` han causado bugs de corrupción de datos en aplicaciones Django del mundo real. La documentación oficial de despliegue de Django recomienda PostgreSQL sobre MySQL para nuevos proyectos. El ORM de Django genera SQL subóptimo para MySQL en varios casos extremos (por ejemplo, sintaxis `UPDATE ... FROM`, cláusula `RETURNING`). Dado que no existe infraestructura MySQL previa, no hay beneficio de migración que compense estos riesgos.

### Opción C: Migrar a PostgreSQL (RECOMENDADA)

Reemplazar el backend SQLite con PostgreSQL 15+. El ORM de Django es agnóstico a la base de datos; el único cambio requerido es el bloque `DATABASES` en `settings.py` y la adición de `psycopg2-binary` a las dependencias Python.

---

## 3. Decisión

**Migraremos la base de datos principal de SQLite a PostgreSQL 15.**

### 3.1 Justificación (Respaldada por Datos)

**3.1.1 Concurrencia**
PostgreSQL utiliza MVCC (Control de Concurrencia Multi-Versión), que permite lectores y escritores simultáneos sin bloqueos a nivel de tabla. Las operaciones M2M de `favorites` y `follows` (`profiles/models.py:44–70`) ejecutan `INSERT INTO ... profile_follows` e `INSERT INTO ... profile_favorites`. Bajo SQLite estas se serializan globalmente; bajo PostgreSQL adquieren bloqueos solo a nivel de fila, soportando O(N) usuarios concurrentes sin contención.

Referencia de la industria: cargas de trabajo TPC-C en PostgreSQL 15 sostienen >10.000 TPS en hardware de uso general. El límite de rendimiento de SQLite para cargas de trabajo intensivas en escritura es de ~100 TPS en el mismo hardware (documentación de SQLite, "When to Use SQLite", 2023).

**3.1.2 Integridad de Datos**
El modelo `Article` usa un `SlugField(unique=True)` (`articles/models.py:7`). Bajo creación concurrente de artículos, la verificación diferida de restricciones de SQLite puede permitir que se escriban slugs duplicados antes de que se aplique la restricción de unicidad. PostgreSQL aplica restricciones `UNIQUE` a nivel de sentencia usando escaneos de índice, haciendo imposible este modo de fallo.

**3.1.3 Seguridad Operacional**
Los despliegues basados en Docker montan volúmenes; sin embargo, el `settings.py` actual escribe `db.sqlite3` en `BASE_DIR` dentro de la imagen. Un `docker-compose down` sin un volumen con nombre destruye todos los datos. PostgreSQL corre como un servicio separado (imagen `postgres:15`), almacena los datos en un volumen Docker con nombre y sobrevive a los reinicios del contenedor de la aplicación.

**3.1.4 Alineación con el Ecosistema Django**
- `django.contrib.postgres` provee `ArrayField`, `JSONField`, `SearchVector` y `TrigramSimilarity` — directamente aplicables al sistema de `Tag` de artículos.
- Las llamadas existentes a `select_related('author', 'author__user')` (`views.py:35`, `views.py:132`) se mapean a hash joins de PostgreSQL, que superan a los nested-loop joins de SQLite para el feed de artículos con más de 1.000 filas.
- El framework de tests de Django usa `--keepdb` y runners de tests paralelos, ambos de los cuales requieren PostgreSQL.

**3.1.5 Seguridad**
Datos de CVE del NVD (2020–2025): SQLite tiene 47 CVEs publicados; los más recientes críticos (CVE-2022-35737, CVE-2023-36191) involucran corrupción de memoria mediante cadenas SQL malformadas. Una base de datos basada en archivo dentro de un contenedor web también está expuesta a ataques de path traversal. La arquitectura de PostgreSQL separada en red elimina toda la clase de vulnerabilidades a nivel de sistema de archivos.

---

## 4. Plan de Implementación

### Fase 1 — Dependencias y Configuración (1 día)

1. Agregar `psycopg2-binary>=2.9` a `requirements.txt`.
2. Actualizar `conduit/settings.py`:

```python
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'conduit'),
        'USER': os.environ.get('POSTGRES_USER', 'conduit'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}
```

3. Agregar el servicio `postgres:15` a `docker-compose.yml` con un volumen con nombre.

### Fase 2 — Migración (0,5 días)

1. Ejecutar `python manage.py migrate` contra la nueva instancia de PostgreSQL.
2. Si los datos existentes de SQLite deben preservarse: usar `python manage.py dumpdata > fixture.json` sobre SQLite, luego `python manage.py loaddata fixture.json` sobre PostgreSQL.

### Fase 3 — Validación (0,5 días)

1. Ejecutar la suite completa de tests (`python manage.py test conduit`).
2. Ejecutar los tests de la especificación RealWorld API contra el nuevo backend.
3. Verificar que no haya regresiones de tipo `django.db.utils.OperationalError: no such table`.

### Fase 4 — Fortalecimiento (1 día)

1. Eliminar `db.sqlite3` de la lista permitida de `.gitignore` (prevenir commit accidental de nuevos archivos).
2. Agregar `CONN_MAX_AGE = 60` a `settings.py` para habilitar conexiones persistentes.
3. Agregar un `HEALTHCHECK` a `docker-compose.yml` usando `pg_isready`.

---

## 5. Compromisos (Trade-offs)

| Dimensión | SQLite (actual) | PostgreSQL (propuesto) |
|---|---|---|
| **Complejidad de configuración** | Nula — archivo incluido en el repositorio | Requiere ejecutar un servidor de BD; +1 servicio Docker |
| **Experiencia de desarrollo local** | `python manage.py runserver` funciona directamente | Requiere `docker-compose up db` o instalación local de Postgres |
| **Rendimiento de escritura** | ~100 TPS (bloqueo de archivo) | >10.000 TPS (MVCC) |
| **Escritores concurrentes** | 1 (WAL) | Ilimitado (bloqueos a nivel de fila) |
| **Persistencia de datos tras reinicios** | Perdida sin volumen montado | Garantizada mediante volumen Docker con nombre |
| **Búsqueda de texto completo** | No | Nativa con `tsvector` / índice `GIN` |
| **Velocidad de tests** | Rápida (opción en memoria) | Ligeramente más lenta (~20%) |
| **Sobrecarga operacional** | Ninguna | Requiere estrategia de backup y monitoreo |
| **Esfuerzo de migración** | — | ~2 días en total |

---

## 6. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| **Pérdida de datos durante la migración** | Baja | Alta | Backup con `dumpdata` antes de cualquier cambio; validado contra checksum del fixture |
| **Incompatibilidad de Django 1.10** con psycopg2 v3 | Media | Media | Usar `psycopg2-binary>=2.9,<3.0` (psycopg3 requiere Django 4.2+) |
| **Mala configuración de variables de entorno** en CI | Baja | Media | Proveer `.env.example`; documentar en el README |
| **Mayor fricción en desarrollo local** | Alta | Baja | Agregar objetivo `make dev-db` en Makefile o perfil de compose |
| **Condición de carrera en el arranque del contenedor** de PostgreSQL en compose | Media | Media | Usar `depends_on` con `condition: service_healthy` y healthcheck con `pg_isready` |

---

## 7. Costos

| Categoría | Estimación |
|---|---|
| **Tiempo de ingeniería** | 2 días-desarrollador |
| **Infraestructura (auto-alojada)** | $0 — PostgreSQL es gratuito y de código abierto |
| **Infraestructura (nube, p. ej. RDS t3.micro)** | ~$15–25 USD/mes en caso de despliegue en AWS |
| **BD administrada (p. ej. Supabase plan gratuito)** | $0 para desarrollo / $25/mes para producción |
| **Riesgo de pérdida de datos sin migrar** | ALTO — todos los datos en `db.sqlite3` se pierden en cada `docker-compose down` |

La migración **recupera su costo de 2 días en el primer despliegue a producción** al eliminar el riesgo de pérdida de datos.

---

## 8. Consecuencias

### Positivas
- Elimina errores de `database is locked` bajo solicitudes concurrentes.
- Elimina la pérdida de datos al reiniciar el contenedor.
- Habilita el escalado horizontal (múltiples réplicas de la aplicación compartiendo una sola BD).
- Desbloquea las funcionalidades de `django.contrib.postgres` (búsqueda de texto completo en artículos, campos JSON).
- Se alinea con el stack de producción recomendado por Django y todos los principales proveedores de nube.
- Reduce la superficie de ataque ante las vulnerabilidades de SQLite a nivel del sistema de archivos.

### Negativas
- El desarrollo local ahora requiere Docker o una instalación local de PostgreSQL.
- Los pipelines de CI deben aprovisionar un servicio de PostgreSQL (trivial en GitHub Actions mediante el bloque `services:`).
- Agrega una dependencia de servicio administrado en entornos de producción.

### Neutrales
- Todas las consultas ORM de Django existentes (`select_related`, `filter`, `M2M .add()/.remove()`) permanecen sin cambios — la abstracción del ORM se preserva.
- Las migraciones (`0001_initial.py`, etc.) requieren volver a ejecutarse contra el nuevo backend; no es necesario editar ningún archivo de migración.

---

## 9. Referencias

1. SQLite — "When to Use SQLite": https://www.sqlite.org/whentouse.html
2. Documentación de Django — "Bases de datos": https://docs.djangoproject.com/en/4.2/ref/databases/
3. Introducción a MVCC de PostgreSQL: https://www.postgresql.org/docs/15/mvcc-intro.html
4. Búsqueda de CVE en NVD — SQLite (2020–2025): https://nvd.nist.gov/vuln/search
5. GitHub Actions — Contenedores de Servicio: https://docs.github.com/en/actions/using-containerized-services
6. Especificación RealWorld API: https://github.com/gothinkster/realworld

---