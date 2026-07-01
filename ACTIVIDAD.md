# Trabajo Práctico — Kubernetes: balanceo de carga y autoescalado

**Modalidad:** individual  
**Entregable:** documento con capturas de pantalla y respuestas a las preguntas de cada actividad

---

## Antes de empezar

1. Lee [README.md](README.md) completo para entender los conceptos del proyecto.
2. Sigue [EJECUCION.md](EJECUCION.md) para desplegar el proyecto en tu máquina.
3. Verifica que todos los pods estén en estado `Running` y que el HPA muestre un valor real en `TARGETS` (no `<unknown>`) antes de continuar con las actividades.

> Este práctico asume que ya conoces Docker. Kubernetes hace algo similar a `docker run`, pero a escala y con gestión automática del estado deseado.

---

## Actividad 1 — Balanceo de carga

Ejecuta 10 peticiones seguidas al endpoint raíz:

```powershell
for ($i=1; $i -le 10; $i++) { Invoke-RestMethod http://127.0.0.1:XXXXX/ }
```

**Captura requerida:** salida completa del comando anterior, donde se vean los campos `pod` y `peticiones_totales`.

**Preguntas:**

1. ¿Cuántos pods distintos aparecen en el campo `pod` de las respuestas? ¿Siempre responde el mismo?
2. En Docker, cuando ejecutas un contenedor con `docker run`, ¿cómo llegarías a tener múltiples instancias del mismo servicio atendiendo peticiones? ¿Qué problema resuelve Kubernetes en comparación?
3. El campo `peticiones_totales` sube de forma continua aunque respondan pods distintos. ¿Por qué no se "resetea" cuando cambia el pod que responde?

---

## Actividad 2 — Auto-reparación

Primero anota cuántos pods están corriendo:

```powershell
kubectl get pods
```

Ahora elimina uno de los pods de la app (no el de mongo):

```powershell
kubectl delete pod balanceo-app-NOMBRE-COMPLETO
```

En otra terminal, observa en tiempo real cómo reacciona el clúster:

```powershell
kubectl get pods -w
```

Espera hasta que el nuevo pod esté en `Running` y detén la observación con Ctrl+C.

**Captura requerida:** la salida del `kubectl get pods -w` donde se vean las transiciones `Terminating` → `ContainerCreating` → `Running`.

**Preguntas:**

1. ¿Cuántos segundos tardó aproximadamente el nuevo pod en pasar a `Running`?
2. ¿Qué componente de Kubernetes detectó que faltaba un pod y ordenó crear uno nuevo? (pista: está en los archivos YAML del proyecto)
3. Si durante esos segundos un usuario hacía una petición al endpoint `/`, ¿le habría llegado al pod que estaba muriendo? ¿Por qué? (pista: busca `readinessProbe` en `app-deployment.yaml`)
4. ¿Qué diferencia hay entre la `readinessProbe` y la `livenessProbe`? ¿Para qué sirve cada una?

---

## Actividad 3 — Autoescalado con HPA

Abre dos terminales.

**Terminal 1** — genera carga de CPU:

```powershell
while ($true) { Invoke-RestMethod http://127.0.0.1:XXXXX/stress | Out-Null }
```

**Terminal 2** — observa cómo responde el clúster:

```powershell
kubectl get hpa -w
```

Espera hasta que el número de réplicas cambie al menos dos veces (puede tardar 2–4 minutos). Luego detén la carga con Ctrl+C en la Terminal 1 y sigue observando el HPA hasta que las réplicas vuelvan a bajar.

**Captura requerida:** la salida del `kubectl get hpa -w` donde se vea la columna `REPLICAS` aumentar por la carga y luego reducirse al detenerla.

**Preguntas:**

1. ¿A qué porcentaje de CPU comenzó a escalar el HPA? ¿Coincide con lo configurado en `hpa.yaml`?
2. ¿Cuántos pods llegó a crear como máximo? ¿Podría haber creado más? ¿Por qué?
3. ¿Cuánto tiempo tardó aproximadamente en reducir los pods después de detener la carga? ¿Por qué crees que no lo hace de inmediato?
4. El HPA necesita el `metrics-server` para funcionar. ¿Qué pasaría si lo desactivaras? ¿Cómo podrías verificarlo?

---

## Actividad 4 — Modificación del comportamiento

Esta actividad requiere que modifiques un archivo de configuración, redespliegues y observes el cambio.

Abre `hpa.yaml` y cambia los siguientes valores:

```yaml
minReplicas: 1      # antes era 2
maxReplicas: 4      # antes era 6
averageUtilization: 30  # antes era 50
```

Aplica el cambio:

```powershell
kubectl apply -f hpa.yaml
```

Verifica que el HPA tomó la nueva configuración:

```powershell
kubectl get hpa
```

Vuelve a correr el stress test y observa el comportamiento:

```powershell
# Terminal 1
while ($true) { Invoke-RestMethod http://127.0.0.1:XXXXX/stress | Out-Null }

# Terminal 2
kubectl get hpa -w
```

**Captura requerida:** el `kubectl get hpa` con los nuevos valores de `MINPODS`, `MAXPODS` y el comportamiento durante la carga.

**Preguntas:**

1. Con `averageUtilization: 30`, ¿el HPA escala más rápido o más lento que antes? ¿Por qué?
2. ¿Qué pasó con el número mínimo de pods cuando bajaste `minReplicas` a 1? ¿Cuándo lo verías reducirse a 1 solo?
3. ¿Qué impacto tiene reducir `maxReplicas` de 6 a 4 en un escenario de mucha carga?
4. En un sistema productivo real, ¿qué criterios usarías para definir los valores de `minReplicas`, `maxReplicas` y `averageUtilization`?

---

## Entregable

Un documento (PDF o similar) con:

- **Por cada actividad:** la captura de pantalla solicitada y las respuestas a las preguntas.
- Las respuestas deben ser con tus propias palabras, no copias de la documentación.
