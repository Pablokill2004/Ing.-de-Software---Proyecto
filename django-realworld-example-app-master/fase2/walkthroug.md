## Metodología

los hotspots se identificaron mediante **análisis estático de complejidad**, evaluando:

- **Recuento de líneas y complejidad estructural** — número de clases, métodos y profundidad de anidamiento por archivo.
- **Code smells** — lógica duplicada, código muerto, inconsistencias de interfaz.
- **Violaciones SOLID** — incumplimientos del Principio de Responsabilidad Única (SRP), Principio Abierto/Cerrado (OCP) y Principio de Inversión de Dependencias (DIP).
- **Riesgos de seguridad** — faltas de validaciones de autorización, brechas de consistencia de datos.
- **Bugs de portabilidad y compatibilidad** — código dependiente de plataforma, incompatibilidades por versiones de librerías.

Se eligió el **patrón Strangler Fig** como estrategia de refactor para los tres hotspots. Este patrón, descrito originalmente por Martin Fowler, permite reemplazar código legacy de forma incremental construyendo implementaciones nuevas junto a las existentes, enrutando el tráfico hacia el código nuevo **un endpoint a la vez**, y retirando el código antiguo solo cuando la migración está completa. Este enfoque minimiza el riesgo porque:

1. El código antiguo se mantiene funcional durante toda la migración (cero downtime).
2. Cada paso de migración es testeable de forma independiente y reversible.
3. Evita el anti-patrón de “big bang rewrite”, que históricamente presenta una alta tasa de fallos.

---

## Hotspot #1 — `conduit/apps/articles/views.py`

**232 líneas | 6 clases | 12+ métodos**  
**Riesgo: ALTO | Impacto: ALTO**

### Issues identificados

| # | Issue | Categoría | Líneas afectadas |
|---|-------|----------|------------------|
| 1 | 4 bloques duplicados `try/except Article.DoesNotExist` con mensajes de error casi idénticos | **Violación DRY** | L74-77, L90-93, L132-135, L169-172, L184-187 |
| 2 | `ArticlesFavoriteAPIView.post` y `.delete` son casi idénticos (solo difieren en la llamada a `favorite`/`unfavorite` y el status code) | **Violación DRY** | L165-193 |
| 3 | `ArticleViewSet.update` no hace verificación de ownership — cualquier usuario autenticado puede editar cualquier artículo | **Falla de seguridad (Broken Access Control — OWASP A01)** | L87-106 |
| 4 | `CommentsDestroyAPIView.destroy` no hace verificación de ownership — cualquier usuario autenticado puede borrar cualquier comentario | **Falla de seguridad (Broken Access Control — OWASP A01)** | L149-157 |
| 5 | El atributo de clase `queryset` en `ArticleViewSet` (L20) se sobreescribe en cada método vía `self.queryset.get()` — declaración muerta que confunde a quien lee | **Código muerto** | L20 |
| 6 | 6 clases de views fragmentadas sin una base común o mixin para patrones repetidos (lookup por slug, construcción de contexto del serializer) | **Falta de abstracción** | Archivo completo |
| 7 | `ArticleViewSet` usa `CreateModelMixin`, `ListModelMixin`, `RetrieveModelMixin` pero agrega `update` como método plano — contrato de interfaz inconsistente | **Inconsistencia de interfaz (preocupación LSP)** | L14-17 vs L87 |

### Análisis de ingeniería

**Por qué este es el hotspot de mayor prioridad:**

Las fallas de seguridad (issues #3 y #4) corresponden a **Broken Access Control**, que es el riesgo #1 del OWASP Top 10 (2021). Cualquier usuario autenticado puede modificar o borrar contenido que no le pertenece. En un entorno de producción, esto sería una vulnerabilidad crítica.

Más allá de seguridad, los cinco bloques duplicados `try/except` violan el principio **DRY (Don't Repeat Yourself)**. Cada bloque sigue el mismo patrón:

```python
try:
    article = Article.objects.get(slug=slug)
except Article.DoesNotExist:
    raise NotFound('An article with this slug does not exist.')
```

Esta duplicación incrementa la carga de mantenimiento: si cambia el formato del mensaje de error, o si se necesita agregar logging cuando falla el lookup, hay que actualizar 5 ubicaciones.

El `ArticlesFavoriteAPIView` también viola DRY: sus métodos `post` y `delete` (L165-193) comparten ~80% del código. Las únicas diferencias son:
- `profile.favorite(article)` vs `profile.unfavorite(article)`
- `HTTP_201_CREATED` vs `HTTP_200_OK`

### Plan de refactor con Strangler Fig

**Fase 1 — Crear módulo en paralelo (Bajo riesgo)**
1. Crear `conduit/apps/articles/views_v2.py` junto al `views.py` existente.
2. Extraer un helper `get_article_by_slug(slug)` para eliminar los bloques duplicados `try/except`. Esto sigue el patrón de refactor **Extract Method**:

```python
# views_v2.py
from rest_framework.exceptions import NotFound
from .models import Article

def get_article_by_slug(slug):
    """Lookup centralizado de artículos — elimina 5 bloques try/except duplicados."""
    try:
        return Article.objects.get(slug=slug)
    except Article.DoesNotExist:
        raise NotFound('An article with this slug does not exist.')
```

**Fase 2 — Agregar autorización (Alto impacto, corrige la falla de seguridad)**
3. Crear una clase de permisos `IsAuthorOrReadOnly` en `conduit/apps/articles/permissions.py`. Esto aplica el **Strategy Pattern**: el sistema de permisos de DRF permite cambiar estrategias de autorización de forma declarativa:

```python
# permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthorOrReadOnly(BasePermission):
    """Permite operaciones de escritura solo si el usuario que hace la request es el autor."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user.profile
```

4. Aplicar `IsAuthorOrReadOnly` a `ArticleViewSet` (para `update`) y `CommentsDestroyAPIView` (para `destroy`).

**Fase 3 — Consolidar favoritos (Impacto medio)**
5. Refactorizar `ArticlesFavoriteAPIView` extrayendo un helper `_toggle_favorite`:

```python
def _toggle_favorite(self, request, article_slug, action, success_status):
    profile = request.user.profile
    article = get_article_by_slug(article_slug)
    getattr(profile, action)(article)
    serializer = self.serializer_class(article, context={'request': request})
    return Response(serializer.data, status=success_status)
```

**Fase 4 — Migración por rutas (Incremental)**
6. Actualizar `conduit/apps/articles/urls.py` para enrutar endpoints a `views_v2.py` uno a la vez. Empezar por los endpoints críticos de seguridad (`update`, `destroy`).
7. Mantener `views.py` como fallback hasta que todas las rutas estén migradas.

**Fase 5 — Limpieza**
8. Eliminar `views.py` una vez que todas las rutas apunten a `views_v2.py`.
9. Renombrar `views_v2.py` a `views.py`.

## Hotspot #2 — `conduit/apps/authentication/models.py`

**139 líneas | 2 clases | 8 métodos**  
**Riesgo: MEDIO-ALTO | Impacto: ALTO**

### Issues identificados

| # | Issue | Categoría | Líneas afectadas |
|---|-------|----------|------------------|
| 1 | La lógica de generación de JWT (`_generate_jwt_token`) vive dentro del modelo `User` | **Violación SRP** | L127-139 |
| 2 | `int(dt.strftime('%s'))` — el especificador de formato `%s` no forma parte del estándar C y **no funciona en Windows** | **Bug latente (portabilidad)** | L136 |
| 3 | `token.decode('utf-8')` — PyJWT >= 2.0 retorna `str` en lugar de `bytes`, causando `AttributeError` | **Bug de compatibilidad** | L139 |
| 4 | La propiedad `token` re-genera el JWT en cada acceso — sin caching | **Smell de performance** | L100-109 |
| 5 | En `conduit/apps/authentication/signals.py`, se usa el operador `is` para comparar enteros (`instance.pk is None` después de `.save()` puede no comportarse como se espera para enteros no cacheados) | **Preocupación de corrección** | signals.py |

### Análisis de ingeniería

**Violación SRP (Single Responsibility Principle):**  
El modelo `User` tiene dos responsabilidades: (1) representar la identidad del usuario y gestionar el estado de autenticación, y (2) generar tokens JWT. Según SRP, una clase debería tener una sola razón para cambiar. Actualmente, el modelo `User` debe cambiar si cambia el esquema del usuario *o* si cambia la estrategia de generación del token (por ejemplo, cambiar de HS256 a RS256, agregar claims, cambiar expiración).

**Bug de portabilidad:**  
La llamada `strftime('%s')` (L136) depende de una extensión específica de plataforma. En Windows, esto lanza `ValueError` porque `%s` no es una directiva reconocida. La alternativa portable es `datetime.timestamp()` (Python 3.3+) o `calendar.timegm()`.

**Compatibilidad con PyJWT:**  
A partir de PyJWT 2.0 (lanzado en enero de 2021), `jwt.encode()` retorna `str` en lugar de `bytes`. Llamar `.decode('utf-8')` sobre un `str` lanza `AttributeError: 'str' object has no attribute 'decode'`. Este breaking change se manifestaría inmediatamente al actualizar PyJWT.

### Plan de refactor con Strangler Fig

**Fase 1 — Crear TokenService (Bajo riesgo)**
1. Crear `conduit/apps/authentication/services.py` con una clase `TokenService`. Esto aplica el refactor **Extract Class** y sigue el **Service Layer Pattern**: la lógica de dominio (generación JWT) se mueve fuera del modelo de datos hacia un servicio dedicado:

```python
# services.py
import jwt
from datetime import datetime, timedelta
from django.conf import settings

class TokenService:
    """Encapsula la generación de tokens JWT — extraído del modelo User (SRP)."""

    TOKEN_EXPIRY_DAYS = 60
    ALGORITHM = 'HS256'

    @classmethod
    def generate_token(cls, user):
        dt = datetime.now() + timedelta(days=cls.TOKEN_EXPIRY_DAYS)

        payload = {
            'id': user.pk,
            'exp': int(dt.timestamp())  # Portable — funciona en todas las plataformas
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=cls.ALGORITHM)

        # PyJWT >= 2.0 retorna str; PyJWT < 2.0 retorna bytes
        if isinstance(token, bytes):
            return token.decode('utf-8')
        return token
```

**Fase 2 — Bridge por delegación (cero ruptura)**
2. Actualizar la propiedad `User.token` para delegar a `TokenService`:

```python
@property
def token(self):
    from .services import TokenService
    return TokenService.generate_token(self)
```

Esto es el “strangler bridge”: los consumidores externos siguen accediendo a `user.token` sin cambios, pero la implementación ahora vive en `TokenService`.

**Fase 3 — Migrar callers (Incremental)**
3. Actualizar serializers (`RegistrationSerializer`, `LoginSerializer`, `UserSerializer`) para llamar `TokenService.generate_token(user)` directamente en lugar de `user.token`.

**Fase 4 — Limpieza**
4. Cuando todos los callers usen `TokenService`, eliminar la propiedad `token` y el método `_generate_jwt_token` del modelo `User`.

---
## Hotspot #3 — `conduit/apps/authentication/serializers.py`

**177 líneas | 3 clases | 4 métodos**  
**Riesgo: MEDIO | Impacto: MEDIO-ALTO**

### Issues identificados

| # | Issue | Categoría | Líneas afectadas |
|---|-------|----------|------------------|
| 1 | `LoginSerializer.validate` realiza autenticación + autorización + construcción de respuesta en un solo método | **Violación SRP** | L42-96 |
| 2 | `UserSerializer.update` llama `instance.save()` (L166) y `instance.profile.save()` (L174) sin `@transaction.atomic` — si el guardado del profile falla, los datos del usuario quedan parcialmente comprometidos | **Riesgo de consistencia de datos** | L139-176 |
| 3 | `from conduit.apps.profiles.serializers import ProfileSerializer` — import entre apps genera acoplamiento fuerte entre `authentication` y `profiles` | **Smell de acoplamiento (violación DIP)** | L5 |
| 4 | El campo `profile` se declara `write_only=True` (L115) mientras `bio` e `image` son `read_only=True` (L119-120) — representación bidireccional de lectura/escritura del mismo dato a través de rutas de campos distintas | **Diseño de API confuso** | L115-120 |

### Análisis de ingeniería

**Violación SRP en `LoginSerializer.validate`:**  
Este método de 55 líneas (L42-96) maneja tres responsabilidades distintas:
1. **Validación de entrada** — verificar que email y password estén presentes.
2. **Autenticación** — llamar a `django.contrib.auth.authenticate()`.
3. **Construcción de respuesta** — construir el diccionario de retorno con email, username y token.

Según SRP, cada una debería ser una preocupación separada. El método `validate` debería limitarse a validar entrada; la autenticación debería delegarse a un servicio; y la construcción de la respuesta es una preocupación de representación (`to_representation`) del serializer.

**Riesgo de consistencia de datos:**  
En `UserSerializer.update` (L139-176), primero se guarda el usuario (L166) y luego se guarda el profile (L174). Si el guardado del profile lanza una excepción (por ejemplo, una violación de constraint en base de datos), los cambios del usuario ya quedaron commitados. Esto viola la propiedad de **Atomicidad**: o se guardan ambos cambios, o no se guarda ninguno. La corrección es directa: envolver el método en `@transaction.atomic`.

**Acoplamiento entre apps:**  
El import de `ProfileSerializer` desde `conduit.apps.profiles` (L5) crea una dependencia directa del app `authentication` hacia el app `profiles`. Esto viola el **Principio de Inversión de Dependencias (DIP)**: los módulos de alto nivel (authentication) no deberían depender de módulos de bajo nivel (profiles). En un proyecto Django bien organizado por capas, las apps deberían comunicarse por interfaces bien definidas o señales de Django, no por imports directos de serializers de otras apps.

### Plan de refactor con Strangler Fig

**Fase 1 — Crear AuthenticationService (Bajo riesgo)**
1. Agregar un método `authenticate(email, password)` a `services.py` (creado en el Hotspot #2):

```python
# En services.py
from django.contrib.auth import authenticate as django_authenticate

class AuthenticationService:
    """Encapsula la lógica de autenticación — extraída de LoginSerializer (SRP)."""

    @staticmethod
    def authenticate(email, password):
        if not email:
            raise ValueError('Se requiere un correo electrónico para iniciar sesión.')
        if not password:
            raise ValueError('Se requiere una contraseña para iniciar sesión.')

        user = django_authenticate(username=email, password=password)

        if user is None:
            raise ValueError('No se encontró un usuario con este email y contraseña.')
        if not user.is_active:
            raise ValueError('Este usuario ha sido desactivado.')

        return user
```

**Fase 2 — Crear serializers v2 (Bajo riesgo)**
2. Crear `conduit/apps/authentication/serializers_v2.py`.
3. Implementar `LoginSerializerV2.validate`: solo valida formato de entrada y delega a `AuthenticationService.authenticate()`:

```python
class LoginSerializerV2(serializers.Serializer):
    email = serializers.CharField(max_length=255)
    username = serializers.CharField(max_length=255, read_only=True)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data):
        user = AuthenticationService.authenticate(
            data.get('email'), data.get('password')
        )
        return {
            'email': user.email,
            'username': user.username,
            'token': TokenService.generate_token(user)
        }
```

4. Implementar `UserSerializerV2.update` envuelto en `@transaction.atomic`:

```python
from django.db import transaction

class UserSerializerV2(serializers.ModelSerializer):
    # ... mismas declaraciones de campos ...

    @transaction.atomic
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        profile_data = validated_data.pop('profile', {})

        for key, value in validated_data.items():
            setattr(instance, key, value)

        if password is not None:
            instance.set_password(password)

        instance.save()

        for key, value in profile_data.items():
            setattr(instance.profile, key, value)

        instance.profile.save()
        return instance
```

**Fase 3 — Migración por rutas (Incremental)**
5. Actualizar `LoginAPIView` para usar `LoginSerializerV2` y `UserRetrieveUpdateAPIView` para usar `UserSerializerV2`.

**Fase 4 — Limpieza**
6. Eliminar las clases antiguas de serializers una vez que todas las views usen los serializers v2.
7. Renombrar `serializers_v2.py` a `serializers.py`.

---

## Matriz de prioridad

Los hotspots se priorizan usando una matriz **Riesgo × Impacto**, donde:
- **Riesgo** mide la severidad de los problemas existentes (fallas de seguridad > bugs de compatibilidad > code smells).
- **Impacto** mide cuántas features/endpoints se ven afectados y el radio de explosión de una falla.

| Prioridad | Hotspot | Riesgo | Impacto | Justificación |
|----------|---------|------|--------|---------------|
| **P0 — Crítico** | `articles/views.py` | ALTO | ALTO | Contiene **vulnerabilidades de seguridad activas** (faltan ownership checks en update y delete). Mayor complejidad estructural (6 clases, 12+ métodos). Mayor duplicación (5 bloques `try/except` repetidos). Afecta la mayor cantidad de endpoints (8 de 14 endpoints totales). |
| **P1 — Alto** | `authentication/models.py` | MEDIO-ALTO | ALTO | Contiene **bugs de compatibilidad** que fallan en Windows (`strftime('%s')`) y en PyJWT >= 2.0 (`.decode('utf-8')`). La violación SRP en el modelo core `User` hace que cualquier cambio de tokens requiera modificar el modelo. Alto impacto porque la generación de JWT afecta todas las requests autenticadas. |
| **P2 — Medio** | `authentication/serializers.py` | MEDIO | MEDIO-ALTO | **Riesgo de consistencia de datos** (doble save no atómico) y violaciones SRP. Menor radio de explosión que P0/P1 porque las fallas se concentran en login y user-update. El acoplamiento entre apps es un problema de mantenibilidad, pero no un riesgo inmediato de runtime.


## Quality Gates

Los quality gates definen los **criterios mínimos de calidad** que el código nuevo debe cumplir antes de poder fusionarse (merge) a la rama principal. Estos gates se hacen cumplir mediante SonarQube como parte del **pipeline de CI/CD**.

### Definición de gates

| Gate | Métrica | Umbral | Justificación |
|------|--------|--------|---------------|
| **Confiabilidad (Reliability)** | Bugs nuevos en el código modificado | **0** | No se permiten bugs nuevos en ningún PR. Es el umbral más estricto posible: tolerancia cero a regresiones. |
| **Seguridad (Security)** | Vulnerabilidades nuevas en el código modificado | **0** | No se permiten nuevos issues de seguridad. Esto atiende directamente los hallazgos de Broken Access Control en el Hotspot #1. |
| **Mantenibilidad (Maintainability)** | Ratio de deuda técnica en el código nuevo | **≤ 5%** | Permite enfocarse en “estrangular” la deuda del legado sin quedar bloqueados por ella, asegurando que todo el código *nuevo* sea limpio. El 5% significa que por cada 100 líneas nuevas, como máximo 5 líneas pueden acumular code smells sin resolver. |
| **Duplicación (Duplication)** | Líneas duplicadas en el código nuevo | **≤ 3%** | Hace cumplir DRY en contribuciones nuevas. Este umbral es más estricto que el default de SonarQube (que a menudo ni está configurado) porque la duplicación es el problema más prevalente encontrado en esta auditoría. |
| **Cobertura (Coverage)** | Cobertura de líneas en el código nuevo | **≥ 80%** | Dado que el proyecto actualmente tiene **cobertura de pruebas cero**, este gate obliga a que todo código nuevo venga testeado. 80% es un estándar de industria que balancea rigurosidad con practicidad (algunas líneas como handlers de excepciones son difíciles de cubrir). |
| **Complejidad (Complexity)** | Complejidad cognitiva por método | **≤ 15** | Evita la creación de nuevos hotspots. La complejidad cognitiva de SonarQube mide qué tan difícil es entender un método (considera anidamiento, rupturas del flujo lineal y recursión). Un umbral de 15 es la recomendación por defecto de SonarQube. |

### Cómo interactúan los Quality Gates con la estrategia Strangler Fig

Los quality gates se configuran para evaluar **solo el código nuevo** (no toda la base de código). Esto es crítico porque:

1. El código legado (que estamos estrangulando) fallaría múltiples gates (por ejemplo, `LoginSerializer.validate` tiene complejidad cognitiva > 15 y hay 0% de cobertura de pruebas).
2. Al acotar los gates al código nuevo, el equipo puede fusionar refactors tipo Strangler Fig de forma incremental sin que el legado bloquee el pipeline.
3. A medida que el código legado se reemplaza, las métricas globales de la base de código mejoran de manera orgánica.

### Mecanismo de enforcement

Los quality gates se hacen cumplir en dos niveles:

1. **Servidor SonarQube** — El quality gate se configura en la UI de SonarQube bajo *Quality Gates > Create*. El gate se aplica al proyecto `conduit-realworld-django`.
2. **Pipeline de CI** — `sonar-scanner` se ejecuta como un paso dentro del pipeline (por ejemplo, GitHub Actions). Si el quality gate falla, el pipeline falla y el PR no puede ser mergeado.

---

## Configuración de SonarQube

El proyecto se configura mediante `sonar-project.properties` en la raíz del repositorio. Decisiones clave de configuración:

| Propiedad | Valor | Justificación |
|----------|-------|---------------|
| `sonar.projectKey` | `conduit-realworld-django` | Identificador único del proyecto en SonarQube. |
| `sonar.sources` | `conduit` | Todo el código de la aplicación vive bajo el directorio `conduit/`. |
| `sonar.language` | `py` | El proyecto es una aplicación Python (Django). |
| `sonar.exclusions` | `**/migrations/**,**/tests/**,manage.py` | Las migrations de Django son auto-generadas y no deberían analizarse. Los tests tienen estándares de calidad distintos. `manage.py` es boilerplate. |

### Pasos de setup de SonarQube

1. **Instalar SonarQube** (Community Edition es gratis y suficiente para este proyecto).
2. **Crear el proyecto** en la UI de SonarQube con key `conduit-realworld-django`.
3. **Configurar el quality gate** usando los umbrales definidos arriba.
4. **Generar un token de autenticación** para el pipeline de CI.
5. **Agregar `sonar-project.properties`** a la raíz del repositorio (ya hecho — ver archivo en la raíz del repo).
6. **Integrar con CI** — agregar un paso `sonar-scanner` al workflow de GitHub Actions (entregable separado).

---

## Apéndice: Patrones de diseño referenciados

| Patrón | Dónde se aplica | Descripción |
|---------|------------------|-------------|
| **Strangler Fig** | Todos los hotspots | Reemplazo incremental del legado construyendo implementaciones nuevas junto a las antiguas, migrando tráfico y retirando el código viejo. Evita los big-bang rewrites. |
| **Strategy Pattern** | Permiso `IsAuthorOrReadOnly` | El sistema de permisos de DRF usa Strategy: las clases de permisos son estrategias intercambiables para decisiones de autorización. |
| **Service Layer Pattern** | `TokenService`, `AuthenticationService` | Extrae lógica de dominio desde modelos/serializers hacia servicios dedicados, siguiendo SRP. |
| **Extract Method** | `get_article_by_slug()` | Consolida código duplicado en un método único y reutilizable. |
| **Extract Class** | `TokenService` desde `User` | Mueve un conjunto cohesivo de responsabilidades desde una clase hacia una clase nueva y dedicada. |

## Apéndice: Principios SOLID referenciados

| Principio | Violaciones encontradas | Hotspot |
|-----------|--------------------------|---------|
| **SRP** (Single Responsibility) | Generación de JWT en el modelo User; auth + validación + respuesta en `LoginSerializer.validate` | #2, #3 |
| **OCP** (Open/Closed) | Agregar nuevas acciones de artículos requiere modificar clases de views existentes | #1 |
| **LSP** (Liskov Substitution) | `ArticleViewSet` declara mixins pero agrega `update` fuera del contrato de mixins | #1 |
| **DIP** (Dependency Inversion) | Import directo entre apps de `ProfileSerializer` en serializers de authentication | #3 |

