# Django-realworld-example | Delivery 4: Architecture Decision Record (ADR)


## *Argumentos Basados en Datos & Validación QA (Persona C)*

Los benchmarks de rendimiento (SQLite vs PostgreSQL), análisis de CVEs (NVD 2020–2025), comparativa de costos en nube (AWS/Azure/GCP) y la validación del setup desde cero se documentan en:

[Delivery-4-ADR-DataArguments-QA-Validation](Delivery-4-ADR-DataArguments-QA-Validation.pdf)


---


# Django-realworld-example | Delivery 3: DevSecOps — Security Hardening


## *Pre-commit Hook: Block hardcoded secrets before they reach the repository*

Se implementó un pre-commit hook usando Husky que escanea los archivos en staging antes de cada commit, bloqueando cualquier secret hardcodeado detectado (Django SECRET_KEY, passwords, JWT secrets, API keys, entre otros).

La documentación completa del diseño, patrones de detección y evidencia de funcionamiento se encuentra en:

[Delivery-3-DevSecOps-Pre-commit-Hook](Delivery-3-DevSecOps-Pre-commit-Hook.pdf)


## *SBOM Generation*

El archivo SBOM está presente en la raíz de este repositorio, generado con cyclonedx-py en formato CycloneDX 1.5.

[Ver sbom.json](sbom.json)


## *Vulnerability Patching*

El análisis de vulnerabilidades Before/After con los CVEs identificados y las versiones corregidas se documenta en:

[Delivery-3-DevSecOps-Pre-commit-Hook](Delivery-3-DevSecOps-Pre-commit-Hook.pdf)


---


# Django-realworld-example | Delivery 2: Governance & Technical Debt Audit


## *Governance Pipeline: Configure a CI workflow (GitHub Actions) that measures Cyclomatic Complexity and Code Coverage. It must fail/warn if metrics degrade.*

Revisar en Github actions los worklows hechos. Actualmente se encontrarán varias pruebas de workflows fallidos y un par bien ejecutados, si bien es cierto en los últimos se muestran fallidos, se deben a los problemas de coverage en el proyecto analizado:

[django-realworld-example-app-master](/django-realworld-example-app-master)

También, proveemos una pequeña [documentación](ISA-Delivery2-GithubActioins-InitialSettings.pdf) de la configuración del github actions.


## *Tech Debt Audit: Identify the top 3 "Hotspots" (files with high churn/complexity) and propose a refactoring plan using the Strangler Fig pattern.*

Los Hostpots, plan de refactoring y el uso del Strangler Fig pattern, se encuentran documentados en 
[Delivery-2-Governance-&-Technical-Debt-Audit](Delivery-2-Governance-&-Technical-Debt-Audit.pdf)

Véase el índice que especifica los puntos considerados.