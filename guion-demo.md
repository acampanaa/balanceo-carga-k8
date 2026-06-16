# Guion de demo — Mini-clúster auto-reparable con balanceo de carga

## Preparación (antes de subir al escenario)

```bash
# 1. Construir y publicar la imagen
docker build -t amesitos/balanceo-app:v1 .
docker push amesitos/balanceo-app:v1

# 2. Desplegar MongoDB
kubectl apply -f mongo-deployment.yaml

# 3. Desplegar la app (3 réplicas) y el Service LoadBalancer
kubectl apply -f app-deployment.yaml

# 4. Verificar que todo está Running
kubectl get pods
kubectl get svc balanceo-app-svc
# En Docker Desktop el EXTERNAL-IP aparece como "localhost"
```

---

## Paso 1 — Balanceo visible (slide 5 y 6)

> "Voy a hacer varias peticiones seguidas al mismo endpoint y vamos a ver que pods distintos me responden."

```bash
# Opción A: bucle en PowerShell
for ($i=1; $i -le 6; $i++) { Invoke-RestMethod http://localhost/ | ConvertTo-Json }

# Opción B: bucle en bash/Git Bash
for i in $(seq 6); do curl -s http://localhost/ ; echo; done
```

**Qué mostrar:** el campo `"pod"` cambia entre las 3 réplicas → kube-proxy está distribuyendo el tráfico (round-robin / iptables).

---

## Paso 2 — Estado compartido (app stateless, Mongo guarda el estado)

> "Fíjense en el contador. Cada petición lo incrementa sin importar qué pod responde. El pod no guarda nada: el estado vive en MongoDB."

```bash
curl http://localhost/
# {"pod": "balanceo-app-xxxx-yyy", "peticiones_totales": 7}
curl http://localhost/
# {"pod": "balanceo-app-xxxx-zzz", "peticiones_totales": 8}  ← pod distinto, contador sigue
```

**Mensaje clave:** los pods son intercambiables porque son stateless. Mongo es el único que tiene estado.

---

## Paso 3 — Auto-reparación en vivo (Idea Clave #1)

> "Voy a borrar uno de los pods ahora mismo, en directo."

```bash
# Ver los pods actuales
kubectl get pods

# Borrar uno (copia el nombre de arriba)
kubectl delete pod balanceo-app-<NOMBRE-COMPLETO>

# En otra terminal, observar cómo K8s lo recrea solo
kubectl get pods -w
```

**Qué mostrar:** el pod pasa a `Terminating` y casi inmediatamente aparece uno nuevo en `ContainerCreating` → `Running`. El Deployment tiene `replicas: 3` y el ReplicaSet garantiza ese número siempre.

> "Nadie tuvo que hacer nada. Kubernetes vio que faltaba una réplica y la recreó solo."

---

## Paso 4 — Escalado horizontal

> "Ahora vamos a pasar de 3 a 5 réplicas con un solo comando."

```bash
kubectl scale deployment balanceo-app --replicas=5

# Ver los pods nuevos aparecer
kubectl get pods -w
```

**Qué mostrar:** dos pods nuevos pasan de `Pending` → `ContainerCreating` → `Running` en segundos. Después puedes hacer más peticiones y verás 5 pods distintos respondiendo.

```bash
# Volver a 3 al final (opcional, para dejar limpio)
kubectl scale deployment balanceo-app --replicas=3
```

---

## Limpieza al terminar

```bash
kubectl delete -f app-deployment.yaml
kubectl delete -f mongo-deployment.yaml
```
