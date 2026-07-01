# Mini-clúster auto-reparable con balanceo de carga en Kubernetes

Proyecto de Kubernetes que despliega una app Flask con múltiples réplicas, balanceo de carga automático, auto-reparación de pods y autoescalado por CPU.

```
         Usuario (navegador / terminal)
                    │
                    ▼
          [Service LoadBalancer]       ← distribuye el tráfico
         /          │          \
      Pod 1       Pod 2       Pod 3   ← app Flask (Python)
         \          │          /
                [MongoDB]             ← contador global compartido

              [HPA - Autoscaler]      ← vigila CPU, escala de 2 a 6 pods
```

---

## Orden de lectura

| Paso | Archivo | Contenido |
|---|---|---|
| 1 | [TEORIA.md](TEORIA.md) | Conceptos de Kubernetes: pods, deployments, services, HPA, probes |
| 2 | [EJECUCION.md](EJECUCION.md) | Requisitos e instrucciones para desplegar el proyecto |
| 3 | [ACTIVIDAD.md](ACTIVIDAD.md) | Trabajo práctico con preguntas y entregables |

---

## Archivos del proyecto

```
balanceo-carga-k8/
├── app.py                 ← aplicación Flask
├── Dockerfile             ← receta para construir la imagen Docker
├── requirements.txt       ← dependencias de Python
├── app-deployment.yaml    ← Deployment de la app + Service LoadBalancer
├── mongo-deployment.yaml  ← Deployment de MongoDB + Service interno
└── hpa.yaml               ← HorizontalPodAutoscaler (escala por CPU)
```
