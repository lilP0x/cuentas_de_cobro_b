import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

async def test_connection():
    """Probar la conexión a MongoDB Atlas"""
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB", "facturacion")
    
    print("🔄 Intentando conectar a MongoDB Atlas...")
    print(f"📦 Base de datos: {MONGO_DB_NAME}")
    
    try:
        # Crear cliente
        client = AsyncIOMotorClient(MONGO_URI)
        
        # Probar conexión
        await client.admin.command('ping')
        print("✅ Conexión exitosa a MongoDB Atlas!")
        
        # Obtener información del servidor
        server_info = await client.server_info()
        print(f"📊 Versión de MongoDB: {server_info.get('version')}")
        
        # Listar bases de datos
        db_list = await client.list_database_names()
        print(f"📁 Bases de datos disponibles: {db_list}")
        
        # Obtener colecciones de la base de datos
        database = client[MONGO_DB_NAME]
        collections = await database.list_collection_names()
        print(f"📂 Colecciones en '{MONGO_DB_NAME}': {collections if collections else 'Ninguna (base de datos vacía)'}")
        
        # Cerrar conexión
        client.close()
        print("🔌 Conexión cerrada correctamente")
        
    except Exception as e:
        print(f"❌ Error al conectar: {type(e).__name__}")
        print(f"📝 Detalles: {str(e)}")
        print("\n💡 Verifica:")
        print("  1. Que tu MONGO_URI en .env no tenga < > alrededor de la contraseña")
        print("  2. Que tu IP esté permitida en MongoDB Atlas (0.0.0.0/0 para permitir todas)")
        print("  3. Que el usuario y contraseña sean correctos")

if __name__ == "__main__":
    asyncio.run(test_connection())
