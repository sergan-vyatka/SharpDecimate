import bpy
import os
import shutil

def remove_pycache_directories():
    """Рекурсивное удаление всех __pycache__ директорий в аддоне"""
    addon_dir = os.path.dirname(os.path.dirname(__file__))  # Папка SharpDecimate
    
    for root, dirs, files in os.walk(addon_dir):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"SharpDecimate: Removed {pycache_path}")
            except Exception as e:
                print(f"SharpDecimate: Failed to remove {pycache_path}: {e}")

def reset_all():
    """Полная очистка временных данных аддона"""
    try:
        # Очистка данных Blender
        if hasattr(bpy.data, 'objects'):
            # Удаление временных объектов
            for obj in list(bpy.data.objects):
                if obj.name.startswith("Low_") and obj.users == 0:
                    bpy.data.objects.remove(obj)
        
        if hasattr(bpy.data, 'meshes'):
            # Удаление временных мешей
            for mesh in list(bpy.data.meshes):
                if mesh.name.startswith("Low_") and mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
        
        if hasattr(bpy.data, 'collections'):
            # Очистка временных коллекций
            for coll in list(bpy.data.collections):
                if coll.name.startswith("LOD_") and not coll.objects:
                    bpy.data.collections.remove(coll)
        
        # Очистка __pycache__ директорий
        remove_pycache_directories()
        
        print("SharpDecimate: Cleanup completed")
    except Exception as e:
        print(f"SharpDecimate: Cleanup skipped - {e}")

def safe_cleanup():
    """Безопасная очистка, которая не вызывает ошибок при регистрации"""
    try:
        # Всегда очищаем __pycache__, даже если данные Blender недоступны
        remove_pycache_directories()
        
        # Пытаемся очистить данные Blender, если они доступны
        reset_all()
    except:
        pass  # Игнорируем ошибки при недоступности данных

def register():
    pass

def unregister():
    pass