
# Django-realworld-example | Security Hardening (DevSecOps)

## *SBOM Generation*

El archivo SBOM está presente en la raíz de este repositorio. [Ver SBOM file](../sbom.json)


## *Vulnerability Patching*

El archivo SBOM está presente en la raíz de este repositorio. [Ver SBOM file](../sbom.json)

## *Secret Protection*

El archivo SBOM está presente en la raíz de este repositorio. [Ver SBOM file](../sbom.json)


# Django-realworld-example | Delivery 3: DevSecOps — Security Hardening


## *Pre-commit hook that blocks dummy secrets effectively*

Se implementó un pre-commit hook usando **Husky** + un script Node.js (`check-secrets.js`) que escanea los archivos en staging antes de cada commit, bloqueando cualquier secret hardcodeado detectado.

El hook detecta: Django `SECRET_KEY`, passwords en diccionarios de `DATABASES`, API Keys, JWT secrets, tokens de AWS/Google/OpenAI, URIs de base de datos con credenciales embebidas y llaves privadas PEM.

La documentación completa del diseño, patrones detectados y evidencia de funcionamiento se encuentra en:

[Delivery-3-DevSecOps-Pre-commit-Hook](Delivery-3-DevSecOps-Pre-commit-Hook.pdf)


## *SBOM (Software Bill of Materials)*

Se generó un archivo `sbom.json` en formato **CycloneDX 1.5** utilizando `cyclonedx-py`, catalogando las 6 dependencias del proyecto (`Django`, `PyJWT`, `djangorestframework`, `django-cors-middleware`, `django-extensions`, `six`) con sus versiones, PURLs y referencias de distribución.

El archivo se encuentra en la raíz del repositorio:

[django-realworld-example-app](https://github.com/gothinkster/django-realworld-example-app)


## *Evidence of vulnerability remediation (Before/After report)*

Se utilizó **Trivy** para escanear las dependencias del proyecto. El reporte inicial identificó vulnerabilidades críticas en las dependencias. Tras actualizar las versiones afectadas, el reporte final confirma la remediación.

El análisis completo Before/After con los CVEs identificados y las versiones corregidas se documenta en:

[Delivery-3-Vulnerability-Patching](Delivery-3-Vulnerability-Patching.pdf)
