# API con FastAPI

API REST básica creada con FastAPI.

## Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt
```

## Ejecutar

```bash
# Método 1: Ejecutar directamente
python main.py

# Método 2: Usar uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Documentación

Una vez ejecutada la aplicación, accede a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints disponibles

- `GET /` - Página de bienvenida
- `GET /items` - Obtener todos los items
- `GET /items/{item_id}` - Obtener un item específico
- `POST /items` - Crear un nuevo item
- `PUT /items/{item_id}` - Actualizar un item
- `DELETE /items/{item_id}` - Eliminar un item
- `GET /health` - Estado del servicio

## Ejemplo de uso

```bash
# Crear un item
curl -X POST "http://localhost:8000/items" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Producto 1",
    "descripcion": "Descripción del producto",
    "precio": 99.99,
    "stock": 10
  }'

# Obtener todos los items
curl http://localhost:8000/items

# Obtener un item específico
curl http://localhost:8000/items/1
```
