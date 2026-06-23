# Mini-clúster auto-reparable con balanceo de carga

App Flask conectada a MongoDB, desplegada en Kubernetes con 3 réplicas detrás de un Service que balancea el tráfico. Cada petición devuelve el nombre del pod que la atendió y un contador global guardado en Mongo.

```
  [Service LoadBalancer]
    /        |        \
 Pod 1     Pod 2     Pod 3   ← app Flask
    \        |        /
         [MongoDB]           ← guarda el contador
```

## Endpoints

| Ruta | Descripción |
|---|---|
| `GET /` | Incrementa el contador global y devuelve el pod que respondió |
| `GET /stats` | Peticiones atendidas por **este pod** + total global |
| `GET /health` | Sonda de salud (usada por Kubernetes) |
| `GET /stress` | Calcula primos hasta 8000 para disparar el HPA |
| `GET /dashboard` | Panel web en tiempo real del balanceo de carga |

## Requisitos

- Docker Desktop con Docker Engine corriendo
- minikube
- Cuenta en Docker Hub

## Despliegue

```bash
# 1. Construir y publicar la imagen
docker build -t amesitos/balanceo-app:v3 .
docker push amesitos/balanceo-app:v3

# 2. Arrancar minikube y activar metrics-server
minikube start
minikube addons enable metrics-server

# 3. Desplegar MongoDB
kubectl apply -f mongo-deployment.yaml

# 4. Desplegar la app (3 réplicas), el Service y el HPA
kubectl apply -f app-deployment.yaml
kubectl apply -f hpa.yaml

# 5. Verificar que todo está Running
kubectl get pods
kubectl get hpa

# 6. Exponer el puerto (déjalo abierto en otra terminal)
kubectl port-forward svc/balanceo-app-svc 8080:8080
```

### Verificar que funciona

```powershell
# Endpoint normal
curl http://localhost:8080/
# {"peticiones_totales": 1, "pod": "balanceo-app-...-pb9db"}

# Peticiones atendidas por este pod específico
curl http://localhost:8080/stats
# {"peticiones_este_pod": 3, "peticiones_totales": 12, "pod": "balanceo-app-...-pb9db"}

# Sonda de salud (la usa Kubernetes internamente)
curl http://localhost:8080/health
# {"status": "ok", "pod": "balanceo-app-...-pb9db"}

# Endpoint de estrés (tarda 1-2 segundos, está calculando primos)
curl http://localhost:8080/stress
# {"pod": "balanceo-app-...-pb9db", "primos_encontrados": 1007}

# Estado del HPA (espera hasta que TARGETS deje de mostrar <unknown>)
kubectl get hpa
# NAME               TARGETS    MINPODS   MAXPODS   REPLICAS
# balanceo-app-hpa   2%/50%     2         6         3
```

### Dashboard visual

Abre **http://localhost:8080/dashboard** en el navegador para ver el balanceo de carga en tiempo real: cada pod aparece con un color distinto y la barra muestra cómo se distribuyen las peticiones.

---

## Demo en 4 pasos

### Paso 1 — Balanceo visible

Varias peticiones al mismo endpoint, pods distintos responden:

```powershell
for ($i=1; $i -le 8; $i++) { Invoke-RestMethod http://localhost:8080/ | ConvertTo-Json }
```

El campo `"pod"` cambia entre las 3 réplicas → kube-proxy distribuye el tráfico (round-robin / iptables).

O abre el dashboard en el navegador: **http://localhost:8080/dashboard**

---

### Paso 2 — Estado compartido

```bash
curl http://localhost:8080/
# {"pod": "balanceo-app-xxxx-yyy", "peticiones_totales": 7}
curl http://localhost:8080/
# {"pod": "balanceo-app-xxxx-zzz", "peticiones_totales": 8}  ← pod distinto, contador sigue
```

Los pods son stateless e intercambiables. MongoDB es el único que tiene estado.

---

### Paso 3 — Auto-reparación en vivo

```bash
# Ver los pods actuales
kubectl get pods

# Borrar uno (copia el nombre de la columna NAME)
kubectl delete pod balanceo-app-<NOMBRE-COMPLETO>

# En otra terminal, observar cómo K8s lo recrea solo
kubectl get pods -w
```

El pod pasa a `Terminating` y Kubernetes crea uno nuevo automáticamente hasta volver a 3 réplicas. Las liveness/readiness probes sobre `/health` permiten a K8s detectar pods no saludables y reemplazarlos antes incluso de que el pod muera.

---

### Paso 4 — Autoescalado con HPA

El HPA escala los pods automáticamente cuando el CPU supera el 50%. No hay que hacer nada a mano.

**Terminal 1 — lanzar carga de CPU:**
```powershell
while ($true) { Invoke-RestMethod http://localhost:8080/stress | Out-Null }
```

**Terminal 2 — observar cómo escala solo:**
```powershell
kubectl get hpa -w
```

Verás el CPU subir por encima del 50% y los pods pasar de 3 hasta 6 automáticamente. Para detener la carga pulsa `Ctrl+C` en la Terminal 1 y en unos minutos el HPA reducirá las réplicas de vuelta al mínimo (2).

---

## Limpieza

```bash
kubectl delete -f hpa.yaml
kubectl delete -f app-deployment.yaml
kubectl delete -f mongo-deployment.yaml
minikube stop
```
