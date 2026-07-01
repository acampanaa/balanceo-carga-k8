# Teoría — Kubernetes: balanceo de carga, auto-reparación y autoescalado

← Volver al [índice](README.md)

---

## ¿Qué es Kubernetes?

Kubernetes (también llamado K8s) es un sistema de orquestación de contenedores. Su función es gestionar automáticamente la ejecución, disponibilidad y escalado de aplicaciones empaquetadas en contenedores Docker.

En lugar de ejecutar un contenedor manualmente con `docker run`, le describes a Kubernetes el estado deseado ("quiero 3 copias de esta app corriendo") y él se encarga de mantenerlo: si una copia falla, la reinicia; si hay mucha carga, crea más.

---

## Arquitectura del proyecto

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

## Conceptos clave

### Pod

El **pod** es la unidad mínima de Kubernetes. Representa uno o más contenedores que se ejecutan juntos en el mismo nodo. En este proyecto, cada pod contiene una instancia de la app Flask.

Los pods son **efímeros**: pueden morir y ser reemplazados en cualquier momento. Por eso no guardan estado interno — el estado (el contador de peticiones) vive en MongoDB, no en los pods.

Cada pod tiene:
- Un nombre único generado automáticamente (`balanceo-app-5c5958b74-2dhqd`)
- Su propia IP interna dentro del clúster
- Acceso a las variables de entorno que le inyecta Kubernetes

### Deployment

Un **Deployment** es la declaración de cómo deben correr los pods: qué imagen usar, cuántas réplicas mantener, qué recursos asignarles, etc.

```yaml
spec:
  replicas: 3          # Kubernetes mantiene siempre 3 pods corriendo
  containers:
  - image: amesitos/balanceo-app:v4
    resources:
      requests:
        cpu: "100m"    # mínimo garantizado: 0.1 núcleos de CPU
      limits:
        cpu: "300m"    # máximo permitido: 0.3 núcleos de CPU
```

Si un pod muere o el nodo falla, el Deployment detecta que el estado actual (2 pods) no coincide con el deseado (3 pods) y crea uno nuevo automáticamente.

### Service y balanceo de carga

Un **Service** es una abstracción que expone un conjunto de pods como un único punto de acceso estable. Como los pods pueden morir y nacer con IPs distintas, el Service actúa como intermediario con IP fija.

El Service de tipo `LoadBalancer` de este proyecto distribuye el tráfico entre los pods disponibles usando **kube-proxy**, que mantiene reglas de red (iptables) para repartir las peticiones en round-robin.

```
Petición entrante → Service (IP fija) → elige un pod disponible → responde
```

Esto explica por qué distintos pods responden a peticiones consecutivas: el Service no envía todo al mismo pod, sino que los alterna.

### Auto-reparación (self-healing)

Kubernetes monitorea continuamente el estado de los pods mediante dos tipos de sondas configuradas en el Deployment:

**Readiness probe** — Kubernetes pregunta "¿estás listo para recibir tráfico?" antes de enviarle peticiones al pod. Si el pod responde mal, el Service lo excluye temporalmente aunque esté corriendo.

**Liveness probe** — Kubernetes pregunta "¿sigues vivo?" cada cierto tiempo. Si el pod no responde, Kubernetes lo mata y crea uno nuevo.

En este proyecto ambas sondas apuntan al endpoint `GET /health`:

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5    # espera 5s antes del primer chequeo
  periodSeconds: 5           # chequea cada 5s

livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 10
```

El resultado: si borras un pod manualmente o si este falla, el clúster vuelve al estado deseado solo, sin intervención humana.

### Autoescalado con HPA

El **HorizontalPodAutoscaler (HPA)** ajusta automáticamente el número de réplicas según el uso de recursos. En este proyecto escala según CPU:

```yaml
spec:
  minReplicas: 2       # nunca menos de 2 pods
  maxReplicas: 6       # nunca más de 6 pods
  metrics:
  - resource:
      name: cpu
      target:
        averageUtilization: 50   # si el promedio de CPU supera 50%, escala
```

Para que el HPA funcione necesita datos de CPU en tiempo real. Esos datos los provee el **metrics-server**, un componente de Kubernetes que recolecta métricas de los nodos y las expone a través de la API del clúster.

Sin metrics-server, el HPA no puede leer el CPU y queda en estado `<unknown>`, sin escalar nunca.

El ciclo de autoescalado funciona así:

```
metrics-server mide CPU de los pods
        ↓
HPA calcula el promedio entre todas las réplicas
        ↓
Si promedio > 50% → crea más pods (hasta 6)
Si promedio < 50% por varios minutos → elimina pods (hasta 2)
```

### Aplicaciones stateless y estado compartido

Los pods de la app Flask son **stateless**: no guardan ningún dato entre peticiones. Si un pod muere, no se pierde información.

El estado (el contador global de peticiones) vive en MongoDB, que es el único componente **stateful** del proyecto. Todos los pods comparten la misma instancia de MongoDB, por lo que el contador sigue siendo consistente aunque distintos pods atiendan cada petición.

Este patrón es fundamental en arquitecturas de microservicios: los servicios de cómputo escalan horizontalmente sin estado propio, mientras que el estado se delega a una base de datos centralizada.

---

## Resumen de recursos de Kubernetes usados

| Recurso | Archivo | Para qué sirve |
|---|---|---|
| `Deployment` | `app-deployment.yaml` | Mantiene 3 réplicas de la app Flask |
| `Deployment` | `mongo-deployment.yaml` | Mantiene 1 réplica de MongoDB |
| `Service (LoadBalancer)` | `app-deployment.yaml` | Expone la app al exterior y balancea el tráfico |
| `Service (ClusterIP)` | `mongo-deployment.yaml` | Expone MongoDB internamente para que los pods lo encuentren por nombre |
| `HorizontalPodAutoscaler` | `hpa.yaml` | Escala la app entre 2 y 6 réplicas según CPU |

---

→ Siguiente: [EJECUCION.md](EJECUCION.md)
