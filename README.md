# Mini-clúster auto-reparable con balanceo de carga

App Flask conectada a MongoDB, desplegada en Kubernetes con 3 réplicas detrás de un Service que balancea el tráfico. Cada petición devuelve el nombre del pod que la atendió y un contador global guardado en Mongo.

```
  [Service LoadBalancer]
    /        |        \
 Pod 1     Pod 2     Pod 3   ← app Flask
    \        |        /
         [MongoDB]           ← guarda el contador
```

## Requisitos

- Docker Desktop con Docker Engine corriendo
- minikube
- Cuenta en Docker Hub

## Despliegue

```bash
# 1. Construir y publicar la imagen
docker build -t amesitos/balanceo-app:v1 .
docker push amesitos/balanceo-app:v1

# 2. Arrancar minikube
minikube start

# 3. Desplegar MongoDB
kubectl apply -f mongo-deployment.yaml

# 4. Desplegar la app (3 réplicas) y el Service
kubectl apply -f app-deployment.yaml

# 5. Verificar que todo está Running
kubectl get pods

# 6. Exponer el puerto (déjalo abierto en otra terminal)
kubectl port-forward svc/balanceo-app-svc 8080:80
```

Prueba en `http://localhost:8080/` — respuesta esperada:

```json
{"peticiones_totales": 1, "pod": "balanceo-app-645568b955-pb9db"}
```

---

## Demo en 4 pasos

### Paso 1 — Balanceo visible

Varias peticiones al mismo endpoint, pods distintos responden:

```powershell
for ($i=1; $i -le 8; $i++) { Invoke-RestMethod http://localhost:8080/ | ConvertTo-Json }
```

El campo `"pod"` cambia entre las 3 réplicas → kube-proxy distribuye el tráfico (round-robin / iptables).

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

El pod pasa a `Terminating` y Kubernetes crea uno nuevo automáticamente hasta volver a 3 réplicas.

---

### Paso 4 — Escalado horizontal

```bash
kubectl scale deployment balanceo-app --replicas=5
kubectl get pods -w

# Volver a 3 al terminar
kubectl scale deployment balanceo-app --replicas=3
```

---

## Limpieza

```bash
kubectl delete -f app-deployment.yaml
kubectl delete -f mongo-deployment.yaml
minikube stop
```
