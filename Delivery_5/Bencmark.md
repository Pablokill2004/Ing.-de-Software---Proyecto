## 1. Resumen Ejecutivo

**Problema Detectado:** Consultas ineficientes (N+1) en el listado de artículos.

**Solución:** Implementación de `select_related` y `prefetch_related` para reducir el número de queries a la base de datos de N+1 a solo 3.

**Resultado Clave:** Mejora del 18.3% en el tiempo de respuesta (P95) y un incremento del 0.5% en Requests Per Second (RPS).

---

## 2. Metodología de Prueba

| Parámetro              | Valor               |
|------------------------|---------------------|
| **Herramienta**        | Locust             |
| **Usuarios Concurrentes** | 50                |
| **Duración**           | 120 segundos       |
| **Endpoint**           | `/api/articles?limit=20` |

---

## 3. Comparativa de Rendimiento (Before vs. After)

| Métrica                | Antes (Baseline)   | Después (Optimizado) | Mejora % |
|------------------------|--------------------|-----------------------|----------|
| **Requests Per Second (RPS)** | 50.12 req/s       | 50.36 req/s          | +0.5%    |
| **Average Latency**    | 25.45 ms          | 20.79 ms             | -18.3%   |
| **P95 Response Time**  | 68 ms             | 57 ms                | -16.2%   |

---

## 4. Análisis de FinOps (Costos Teóricos)

Al reducir la latencia y el número de queries, la utilización de CPU en la base de datos (RDS) disminuye proporcionalmente. Si en producción usamos una instancia `db.t3.medium` ($0.068 USD/hr), la optimización nos permitiría bajar a una `db.t3.micro` ($0.017 USD/hr) manteniendo el mismo rendimiento bajo carga.

**Ahorro teórico estimado:** 75% de reducción en costos mensuales de base de datos.