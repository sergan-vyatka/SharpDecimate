# debug.py
import bpy
print("=== SHARPDECIMATE DEBUG ===")

# Проверим свойства сцены
if hasattr(bpy.types.Scene, 'sharpdecimate_props'):
    props = bpy.context.scene.sharpdecimate_props
    print("Properties in sharpdecimate_props:")
    for prop in props.bl_rna.properties:
        print(f"  - {prop.identifier}")
else:
    print("NO sharpdecimate_props in Scene!")

# Проверим сам класс
try:
    from core.base_decimate import SharpDecimateProperties
    print("SharpDecimateProperties class found")
    print("Properties in class:")
    for prop in SharpDecimateProperties.bl_rna.properties:
        print(f"  - {prop.identifier}")
except Exception as e:
    print(f"Error importing: {e}")