# Chatbuddy MVP API Dokumentáció

## Áttekintés

A Chatbuddy MVP REST API magyar nyelvű omnichannel ügyfélszolgálati chatbot funkcionalitást biztosít.

**Base URL**: `http://localhost:8000`  
**API Version**: `v1`  
**Content-Type**: `application/json`

## Authentication

A jelenlegi MVP verzióban nincs authentication implementálva. Production környezetben JWT token alapú autentikáció lesz.

## Endpoints

### Health Check

#### GET /health
Alapvető health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "0.1.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "ai_models": "available"
  }
}
```

### Chat Endpoints

#### POST /chat
Chat üzenet küldése és válasz fogadása.

**Request Body:**
```json
{
  "message": "Szeretnék információt kapni a termékekről",
  "user_id": "user_123",
  "session_id": "session_456",
  "context": {
    "language": "hu",
    "channel": "web"
  }
}
```

**Response:**
```json
{
  "response": "Természetesen! Milyen termékekről szeretne információt kapni?",
  "session_id": "session_456",
  "agent_type": "coordinator",
  "confidence": 0.95,
  "suggestions": [
    "Termék keresés",
    "Rendelés nyomon követése",
    "Ajánlatok"
  ]
}
```

#### GET /chat/session/{session_id}
Chat session lekérdezése.

**Response:**
```json
{
  "session_id": "session_456",
  "user_id": "user_123",
  "messages": [
    {
      "id": "msg_1",
      "content": "Szeretnék információt kapni a termékekről",
      "timestamp": "2024-01-15T10:30:00Z",
      "sender": "user"
    },
    {
      "id": "msg_2", 
      "content": "Természetesen! Milyen termékekről szeretne információt kapni?",
      "timestamp": "2024-01-15T10:30:05Z",
      "sender": "assistant"
    }
  ],
  "agent_state": {
    "current_agent": "coordinator",
    "context": {
      "intent": "product_inquiry",
      "confidence": 0.95
    }
  }
}
```

### Product Endpoints

#### GET /products/search
Termékek keresése.

**Query Parameters:**
- `q` (string): Keresési kifejezés
- `category` (string, optional): Kategória szűrő
- `limit` (integer, optional): Eredmények száma (default: 10)
- `offset` (integer, optional): Offset (default: 0)

**Response:**
```json
{
  "products": [
    {
      "id": "prod_123",
      "name": "iPhone 15 Pro",
      "price": 499999,
      "currency": "HUF",
      "description": "Apple iPhone 15 Pro 128GB",
      "category": "electronics",
      "available": true,
      "image_url": "https://example.com/iphone15.jpg"
    }
  ],
  "total": 1,
  "query": "iPhone"
}
```

#### GET /products/{product_id}
Termék részletei.

**Response:**
```json
{
  "id": "prod_123",
  "name": "iPhone 15 Pro",
  "price": 499999,
  "currency": "HUF",
  "description": "Apple iPhone 15 Pro 128GB",
  "category": "electronics",
  "available": true,
  "image_url": "https://example.com/iphone15.jpg",
  "specifications": {
    "storage": "128GB",
    "color": "Titanium",
    "screen": "6.1 inch"
  },
  "similar_products": [
    "prod_124",
    "prod_125"
  ]
}
```

### Order Endpoints

#### GET /orders/{order_id}
Rendelés részletei.

**Response:**
```json
{
  "id": "order_123",
  "user_id": "user_123",
  "status": "shipped",
  "total": 499999,
  "currency": "HUF",
  "created_at": "2024-01-10T15:30:00Z",
  "updated_at": "2024-01-12T09:15:00Z",
  "items": [
    {
      "product_id": "prod_123",
      "name": "iPhone 15 Pro",
      "quantity": 1,
      "price": 499999
    }
  ],
  "shipping": {
    "address": "Budapest, 1234 utca 1.",
    "tracking_number": "TRK123456789"
  }
}
```

#### GET /orders/user/{user_id}
Felhasználó rendelései.

**Response:**
```json
{
  "orders": [
    {
      "id": "order_123",
      "status": "shipped",
      "total": 499999,
      "created_at": "2024-01-10T15:30:00Z"
    }
  ],
  "total": 1
}
```

### Agent Endpoints

#### POST /agents/coordinator
Koordinátor agent közvetlen hívása.

**Request Body:**
```json
{
  "message": "Szeretnék rendelést nyomon követni",
  "user_context": {
    "user_id": "user_123",
    "language": "hu"
  }
}
```

**Response:**
```json
{
  "response": "Rendben! Kérem adja meg a rendelés számát.",
  "agent_type": "order_status",
  "confidence": 0.98,
  "next_actions": [
    "order_tracking"
  ]
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "validation_error",
  "message": "Invalid request body",
  "details": {
    "field": "message",
    "issue": "Field is required"
  }
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "Product not found",
  "resource": "product",
  "id": "prod_999"
}
```

### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred",
  "request_id": "req_123456"
}
```

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **Chat endpoints**: 50 requests per minute per user
- **Search endpoints**: 200 requests per minute per IP

## WebSocket Endpoints

### /ws/chat
Valós idejű chat kommunikáció.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');
```

**Message Format:**
```json
{
  "type": "message",
  "content": "Üzenet szövege",
  "user_id": "user_123",
  "session_id": "session_456"
}
```

**Response Format:**
```json
{
  "type": "response",
  "content": "Válasz szövege",
  "agent_type": "coordinator",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## SDK és Klienskódok

### Python
```python
import requests

# Chat üzenet küldése
response = requests.post('http://localhost:8000/chat', json={
    'message': 'Szeretnék információt kapni a termékekről',
    'user_id': 'user_123'
})

print(response.json())
```

### JavaScript
```javascript
// Chat üzenet küldése
const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        message: 'Szeretnék információt kapni a termékekről',
        user_id: 'user_123'
    })
});

const data = await response.json();
console.log(data);
```

## Fejlesztői Eszközök

### Swagger UI
- **URL**: `http://localhost:8000/docs`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

### ReDoc
- **URL**: `http://localhost:8000/redoc`

## Verziókezelés

A jelenlegi API verzió: `v1`

Verzióváltás esetén a következő formátumot használjuk:
- `http://localhost:8000/v1/chat`
- `http://localhost:8000/v2/chat`

## Következő Verziók

### v1.1 (Tervezett)
- Authentication és authorization
- User management endpoints
- Advanced search filters
- Webhook support

### v2.0 (Tervezett)
- GraphQL API
- Real-time notifications
- Advanced analytics endpoints
- Multi-language support 