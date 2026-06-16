# 🚀 Guía de Onboarding: Acceso a OmniCore-AI

Esta guía detalla el proceso exacto para que un desarrollador pase desde cero hasta la ejecución de comandos en la API.

## ⚠️ Concepto Clave: Identidades Duales

OmniCore-AI utiliza dos tipos de identidad para separar la administración de la ejecución:

1.  **Identidad de Usuario (`USER_ID`)**: Es tu identidad administrativa. Se usa para gestionar agentes, crear tokens y administrar la cuenta. 
    - **Uso**: Header `Authorization: Bearer <USER_ID>`
    - **Ámbito**: Endpoints de `/api/auth/...` y `/api/agent/onboard`.

2.  **Identidad de Agente (`JWT_TOKEN`)**: Es un token firmado que contiene el ADN del agente (permisos, tier, app_id). 
    - **Uso**: Header `Authorization: Bearer <JWT_TOKEN>`
    - **Ámbito**: Endpoints de `/api/gateway/execute` y `/api/agent/me`.

---

## 🛠️ El Camino Dorado (Golden Path)

Sigue estos pasos en orden secuencial:

### Paso 1: Crear tu Cuenta de Desarrollador
Registra tu email y contraseña en el sistema.

**Request:**
`POST /api/auth/register`
```json
{
  "email": "dev@example.com",
  "password": "password123"
}
```
**Respuesta:** Obtendrás tu `user_id`. Guárdalo bien.

---

### Paso 2: Onboarding del Agente
Un usuario puede tener varios agentes. Primero debes "dar de alta" un agente para que el sistema cree su infraestructura base.

**Request:**
`POST /api/agent/onboard`
**Header:** `Authorization: Bearer <TU_USER_ID>`
```json
{
  "agent_name": "MiAgenteVentas",
  "tier": "FREE"
}
```
**Respuesta:** Obtendrás el `agent_id`. Este ID identifica al "trabajador" de IA.

---

### Paso 3: Generar Token de API Permanente
El token del onboarding es temporal. Para integrar tu aplicación, genera un token JWT permanente.

**Request:**
`POST /api/auth/tokens/create`
**Header:** `Authorization: Bearer <TU_USER_ID>`
```json
{
  "agent_id": "<TU_AGENT_ID>",
  "token_name": "Produccion-App-1",
  "mode": "PRODUCTION"
}
```
**Respuesta:** Obtendrás el `api_token` (el JWT). **Este es el token que usarás en tu código.**

---

### Paso 4: Ejecutar Comandos de Negocio
Ahora ya puedes interactuar con la infraestructura de negocio.

**Request:**
`POST /api/gateway/execute`
**Header:** `Authorization: Bearer <TU_JWT_TOKEN>`
```json
{
  "command": "stock.list",
  "params": {}
}
```

---

## 📋 Tabla de Referencia Rápida

| Objetivo | Endpoint | Auth Header | Identidad Usada |
| :--- | :--- | :--- | :--- |
| Registrarse | `/api/auth/register` | Ninguno | N/A |
| Login | `/api/auth/login` | Ninguno | N/A |
| Crear Agente | `/api/agent/onboard` | `Bearer <USER_ID>` | Usuario |
| Crear Token JWT | `/api/auth/tokens/create` | `Bearer <USER_ID>` | Usuario |
| Ejecutar Lógica | `/api/gateway/execute` | `Bearer <JWT_TOKEN>` | Agente |
| Ver mi Perfil | `/api/agent/me` | `Bearer <JWT_TOKEN>` | Agente |
