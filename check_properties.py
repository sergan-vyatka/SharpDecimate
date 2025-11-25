import bpy

# Проверим какие свойства есть в классе
if hasattr(bpy.types, 'SharpDecimateProperties'):
    props_class = bpy.types.SharpDecimateProperties
    print("=== PROPERTIES IN SharpDecimateProperties ===")
    for prop in props_class.bl_rna.properties:
        print(f"  - {prop.identifier}")
else:
    print("SharpDecimateProperties class not found!")

# Проверим свойства в сцене  
if hasattr(bpy.types.Scene, 'sharpdecimate_props'):
    props = bpy.context.scene.sharpdecimate_props
    print("=== PROPERTIES IN SCENE ===")
    for prop in props.bl_rna.properties:
        print(f"  - {prop.identifier}")
else:
    print("sharpdecimate_props not found in Scene!")