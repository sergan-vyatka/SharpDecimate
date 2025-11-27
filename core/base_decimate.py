# FILE: core/base_decimate.py
import bpy
import bmesh
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, BoolProperty, PointerProperty, StringProperty

from ..locale_loader import get_text
from ..preferences import get_ui_language
from .edge_analyzer import (analyze_sharp_edges, get_manual_sharp_edges, 
                           get_creased_edges, preserve_hard_edges, analyze_protected_edges)

class SharpDecimateProperties(PropertyGroup):
    sharp_angle: FloatProperty(
        name="Sharp Angle",
        description="Edges with higher angle will be preserved",
        min=70.0,
        max=85.0,
        default=75.0,
        precision=1
    )
    
    keep_sharp: BoolProperty(
        name="Keep Marked Sharp",
        description="Preserve manually marked sharp edges",
        default=True,
    )
    
    keep_crease: BoolProperty(
        name="Keep Edge Crease", 
        description="Preserve edges with crease values",
        default=True,
    )
    
    ratio: FloatProperty(
        name="Ratio",
        description="Target polygon ratio (0.1 = 10% of original)",
        min=0.01,
        max=0.99,
        default=0.3,
        precision=2,
        subtype='FACTOR'
    )
    
    # Material-based decimation properties
    use_material_decimation: BoolProperty(
        name="Enable Material Decimation",
        description="Use different decimation ratios based on materials",
        default=False,
    )
    
    material_high_ratio: FloatProperty(
        name="High Detail Ratio",
        description="Decimation ratio for important materials (first 2-3 slots)",
        min=0.01,
        max=0.99,
        default=0.8,
        precision=2,
        subtype='FACTOR'
    )
    
    material_low_ratio: FloatProperty(
        name="Low Detail Ratio",
        description="Decimation ratio for less important materials",
        min=0.01,
        max=0.99,
        default=0.2,
        precision=2,
        subtype='FACTOR'
    )

def safe_select_all(action='DESELECT'):
    """Безопасное выделение/снятие выделения"""
    try:
        if bpy.context.mode == 'OBJECT':
            bpy.ops.object.select_all(action=action)
        elif bpy.context.mode == 'EDIT_MESH':
            bpy.ops.mesh.select_all(action=action)
    except Exception as e:
        print(f"SharpDecimate: Safe select failed: {e}")

def safe_mode_set(mode='OBJECT'):
    """Безопасное переключение режима"""
    try:
        if bpy.context.mode != mode:
            bpy.ops.object.mode_set(mode=mode)
    except Exception as e:
        print(f"SharpDecimate: Safe mode set failed: {e}")

def check_mesh_integrity(obj):
    """Проверка целостности меша после децимации"""
    try:
        # Проверка что меш не пустой
        if len(obj.data.polygons) == 0:
            return False, "Mesh has no polygons after decimation"
        
        # Проверка на наличие геометрии
        if len(obj.data.vertices) < 3:
            return False, "Mesh has too few vertices"
            
        # Проверка водонепроницаемости
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        
        issues = []
        
        # Проверка на non-manifold geometry
        non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
        if non_manifold_edges:
            issues.append(f"Non-manifold edges: {len(non_manifold_edges)}")
            
        # Проверка на loose geometry
        loose_verts = [v for v in bm.verts if not v.link_edges]
        if loose_verts:
            issues.append(f"Loose vertices: {len(loose_verts)}")
        
        # Проверка на degenerate faces
        degenerate_faces = [f for f in bm.faces if f.calc_area() < 0.0001]
        if degenerate_faces:
            issues.append(f"Degenerate faces: {len(degenerate_faces)}")
        
        bm.free()
        
        if issues:
            return False, ", ".join(issues)
            
        return True, "Mesh integrity OK"
        
    except Exception as e:
        return False, f"Mesh check failed: {str(e)}"

def apply_decimate_modifier(obj, ratio):
    """Применяет модификатор Decimate к объекту"""
    try:
        print(f"🔧 Applying decimation with ratio: {ratio}")
        
        # ГАРАНТИРУЕМ что в объектном режиме
        safe_mode_set('OBJECT')
        
        # 🔴 ПРОВЕРКА ПЕРЕД ДЕЦИМАЦИЕЙ
        pre_check, pre_message = check_mesh_integrity(obj)
        if not pre_check:
            print(f"⚠️ Mesh issues before decimation: {pre_message}")
        
        # СОЗДАЕМ МОДИФИКАТОР
        mod = obj.modifiers.new(name="SharpDecimate_Temp", type='DECIMATE')
        mod.decimate_type = 'COLLAPSE'
        mod.ratio = ratio
        
        # ПРИМЕНЯЕМ МОДИФИКАТОР через оператор
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        
        # Пробуем применить модификатор
        try:
            bpy.ops.object.modifier_apply(modifier="SharpDecimate_Temp")
            print(f"✅ Decimation applied successfully via operator!")
        except Exception as e:
            print(f"⚠️ Operator apply failed, trying alternative method: {e}")
            # Альтернативный метод
            depsgraph = bpy.context.evaluated_depsgraph_get()
            eval_obj = obj.evaluated_get(depsgraph)
            mesh_copy = bpy.data.meshes.new_from_object(eval_obj)
            
            # УДАЛЯЕМ МОДИФИКАТОР И ПРИМЕНЯЕМ НОВЫЙ МЕШ
            obj.modifiers.remove(mod)
            old_mesh = obj.data
            obj.data = mesh_copy
            
            # УДАЛЯЕМ СТАРЫЙ МЕШ
            bpy.data.meshes.remove(old_mesh)
            print(f"✅ Decimation applied via alternative method!")
        
        # 🔴 ПРОВЕРКА ПОСЛЕ ДЕЦИМАЦИИ
        post_check, post_message = check_mesh_integrity(obj)
        if not post_check:
            print(f"⚠️ Mesh issues after decimation: {post_message}")
        else:
            print(f"✅ Mesh integrity check passed")
        
    except Exception as e:
        print(f"❌ Decimate modifier failed: {e}")

def material_based_decimate(context, original_obj, props):
    """Material-based decimation - разные ratio для разных материалов"""
    try:
        print("🎨 Starting material-based decimation...")
        
        # Проверяем наличие материалов
        if not original_obj.data.materials:
            print("❌ No materials found, falling back to standard decimation")
            return standard_decimate(context, original_obj, props)
        
        # Сохраняем исходное состояние
        original_active = context.view_layer.objects.active
        original_selected = context.selected_objects.copy()
        original_collections = original_obj.users_collection
        
        # Создаем коллекцию для временных объектов
        temp_collection = bpy.data.collections.new("SharpDecimate_Temp")
        context.scene.collection.children.link(temp_collection)
        
        decimated_parts = []
        
        # Для КАЖДОГО материала создаем отдельный объект
        for material_index, material in enumerate(original_obj.data.materials):
            if material is None:
                continue
                
            print(f"🔧 Processing material {material_index}: {material.name}")
            
            # Дублируем исходный объект
            safe_select_all('DESELECT')
            original_obj.select_set(True)
            context.view_layer.objects.active = original_obj
            
            safe_mode_set('OBJECT')
            bpy.ops.object.duplicate()
            material_obj = context.active_object
            material_obj.name = f"Temp_{original_obj.name}_Mat_{material_index}"
            
            # Перемещаем во временную коллекцию
            for coll in material_obj.users_collection:
                coll.objects.unlink(material_obj)
            temp_collection.objects.link(material_obj)
            
            # Выделяем только полигоны с текущим материалом
            safe_mode_set('EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            safe_mode_set('OBJECT')
            
            # Выбираем полигоны с этим материалом
            for poly in material_obj.data.polygons:
                if poly.material_index == material_index:
                    poly.select = True
            
            # Переходим в edit mode и УДАЛЯЕМ все остальные полигоны
            safe_mode_set('EDIT')
            bpy.ops.mesh.select_mode(type='FACE')
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='FACE')
            safe_mode_set('OBJECT')
            
            # Пропускаем пустые объекты
            if len(material_obj.data.polygons) == 0:
                bpy.data.objects.remove(material_obj)
                continue
            
            # Определяем ratio по типу материала
            if "HighDetail" in material.name:
                target_ratio = props.material_high_ratio
                print(f"  🎯 HighDetail material, ratio: {target_ratio}")
            else:  # LowDetail или любой другой
                target_ratio = props.material_low_ratio
                print(f"  🎯 LowDetail material, ratio: {target_ratio}")
            
            # Применяем decimation к ЭТОЙ ЧАСТИ
            apply_decimate_modifier(material_obj, target_ratio)
            
            decimated_parts.append(material_obj)
        
        # Объединяем все части обратно
        if len(decimated_parts) > 0:
            print("🔗 Merging decimated parts...")
            safe_select_all('DESELECT')
            
            # Перемещаем все части обратно в оригинальные коллекции ПЕРЕД объединением
            for obj in decimated_parts:
                for coll in obj.users_collection:
                    coll.objects.unlink(obj)
                for coll in original_collections:
                    coll.objects.link(obj)
                obj.select_set(True)
            
            # Делаем первую часть активной
            context.view_layer.objects.active = decimated_parts[0]
            
            # Объединяем
            bpy.ops.object.join()
            final_obj = context.active_object
            final_obj.name = "Low_" + original_obj.name
            
            # Очищаем материалы (оставляем только один)
            final_obj.data.materials.clear()
            
        else:
            # Если ничего не получилось - fallback
            print("❌ No parts to merge, using standard decimation")
            return standard_decimate(context, original_obj, props)
        
        # Удаляем временную коллекцию
        bpy.data.collections.remove(temp_collection)
        
        # Восстанавливаем sharp edges
        safe_mode_set('OBJECT')
        final_bm = bmesh.new()
        final_bm.from_mesh(final_obj.data)
        
        for edge in final_bm.edges:
            if len(edge.link_faces) == 2:
                angle = edge.calc_face_angle()
                angle_degrees = angle * 180.0 / 3.14159
                if angle_degrees > props.sharp_angle:
                    edge.smooth = False
        
        final_bm.to_mesh(final_obj.data)
        final_bm.free()
        
        # Настройка авто-сглаживания
        final_obj.data.use_auto_smooth = True
        final_obj.data.auto_smooth_angle = 3.14159
        
        # Гарантируем что объект видим
        final_obj.hide_set(False)
        final_obj.hide_viewport = False
        final_obj.hide_render = False
        
        # 🔴 ФИНАЛЬНАЯ ПРОВЕРКА ЦЕЛОСТНОСТИ
        final_check, final_message = check_mesh_integrity(final_obj)
        if not final_check:
            print(f"⚠️ Final mesh integrity check failed: {final_message}")
        else:
            print(f"✅ Final mesh integrity check passed")
        
        # Восстанавливаем исходное выделение
        safe_select_all('DESELECT')
        for obj in original_selected:
            obj.select_set(True)
        context.view_layer.objects.active = original_active
        
        print(f"✅ Material-based decimation completed! Created: {final_obj.name}")
        return final_obj
        
    except Exception as e:
        print(f"❌ Material-based decimation failed: {e}")
        # Fallback на стандартную децимацию
        try:
            return standard_decimate(context, original_obj, props)
        except:
            return None

def standard_decimate(context, original_obj, props):
    """Стандартная децимация (без material-based)"""
    try:
        # Сохраняем исходное состояние выделения
        original_active = context.view_layer.objects.active
        original_selected = context.selected_objects.copy()
        
        # Дублирование объекта
        safe_select_all('DESELECT')
        original_obj.select_set(True)
        context.view_layer.objects.active = original_obj
        
        # Безопасное дублирование
        safe_mode_set('OBJECT')
        bpy.ops.object.duplicate()
        
        lowpoly_obj = context.active_object
        lowpoly_obj.name = "Low_" + original_obj.name
        
        # Применяем децимацию
        print(f"🔥 STEP 1: Applying decimation with ratio {props.ratio}")
        apply_decimate_modifier(lowpoly_obj, props.ratio)
        
        # Анализ исходного меша с поддержкой crease
        original_bm = bmesh.new()
        original_bm.from_mesh(original_obj.data)
        
        # ПРАВКА: Правильная работа с crease layer
        crease_layer = original_bm.edges.layers.crease.verify()
        original_bm.edges.ensure_lookup_table()
        
        # Получаем все типы острых граней
        manual_sharp_edges = get_manual_sharp_edges(original_bm) if props.keep_sharp else []
        creased_edges = get_creased_edges(original_bm) if props.keep_crease else []
        
        # Работа с lowpoly мешем - ГАРАНТИРУЕМ что вышли из edit mode
        safe_mode_set('OBJECT')
        bm = bmesh.new()
        bm.from_mesh(lowpoly_obj.data)
        
        # ПРАВКА: Правильная работа с crease layer
        target_crease_layer = bm.edges.layers.crease.verify()
        bm.edges.ensure_lookup_table()
        
        # Сброс smooth для перерасчета
        for edge in bm.edges:
            edge.smooth = True
        
        # Анализ ВСЕХ защищенных ребер
        protected_edges = analyze_protected_edges(bm, original_obj, props.sharp_angle)
        
        # Сохраняем ВСЕ типы острых граней
        preserve_hard_edges(bm, protected_edges, manual_sharp_edges, creased_edges, crease_layer, target_crease_layer)
        
        # Применение изменений
        safe_mode_set('OBJECT')
        bm.to_mesh(lowpoly_obj.data)
        bm.free()
        original_bm.free()
        
        # Восстанавливаем sharp edges на финальном меше с поддержкой crease
        safe_mode_set('OBJECT')
        final_bm = bmesh.new()
        final_bm.from_mesh(lowpoly_obj.data)
        final_crease_layer = final_bm.edges.layers.crease.verify()
        
        # Повторно применяем sharp метки к финальной геометрии - ВСЕГДА используем sharp_angle!
        for edge in final_bm.edges:
            if len(edge.link_faces) == 2:
                angle = edge.calc_face_angle()
                angle_degrees = angle * 180.0 / 3.14159
                if angle_degrees > props.sharp_angle:
                    edge.smooth = False
        
        # Применяем изменения - ГАРАНТИРУЕМ что вышли из edit mode
        safe_mode_set('OBJECT')
        final_bm.to_mesh(lowpoly_obj.data)
        final_bm.free()
        
        # Настройка авто-сглаживания для корректного отображения
        lowpoly_obj.data.use_auto_smooth = True
        lowpoly_obj.data.auto_smooth_angle = 3.14159  # 180 градусов
        
        # 🔴 ФИНАЛЬНАЯ ПРОВЕРКА ЦЕЛОСТНОСТИ
        final_check, final_message = check_mesh_integrity(lowpoly_obj)
        if not final_check:
            print(f"⚠️ Final mesh integrity check failed: {final_message}")
        else:
            print(f"✅ Final mesh integrity check passed")
        
        # Восстанавливаем исходное выделение БЕЗОПАСНО
        safe_mode_set('OBJECT')
        safe_select_all('DESELECT')
        for obj in original_selected:
            obj.select_set(True)
        context.view_layer.objects.active = original_active
        
        # 🔥 ВЫВОДИМ СТАТИСТИКУ ДЕЦИМАЦИИ
        original_faces = len(original_obj.data.polygons)
        final_faces = len(lowpoly_obj.data.polygons)
        reduction = ((1 - final_faces / original_faces) * 100) if original_faces > 0 else 0
        
        print(f"📊 DECIMATION RESULT: {original_faces} -> {final_faces} faces ({reduction:.1f}% reduction)")
        print(f"✅ Standard decimation completed! Created: {lowpoly_obj.name}")
        
        return lowpoly_obj
        
    except Exception as e:
        # Восстанавливаем состояние в случае ошибки БЕЗОПАСНО
        try:
            safe_mode_set('OBJECT')
            safe_select_all('DESELECT')
            for obj in original_selected:
                obj.select_set(True)
            context.view_layer.objects.active = original_active
        except Exception as restore_error:
            print(f"SharpDecimate: Restore failed: {restore_error}")
        print(f"❌ Standard decimation failed: {e}")
        raise e

def decimate_single_object(context, original_obj, props):
    """Основная логика упрощения одного объекта с сохранением острых граней"""
    
    # Выбираем алгоритм децимации
    if props.use_material_decimation and original_obj.data.materials:
        print("🎨 Using MATERIAL-BASED decimation")
        return material_based_decimate(context, original_obj, props)
    else:
        print("🔧 Using STANDARD decimation")
        return standard_decimate(context, original_obj, props)

def register():
    try:
        bpy.utils.register_class(SharpDecimateProperties)
        bpy.types.Scene.sharpdecimate_props = PointerProperty(type=SharpDecimateProperties)
    except Exception as e:
        print(f"SharpDecimate: Failed to register properties: {e}")

def unregister():
    try:
        if hasattr(bpy.types.Scene, 'sharpdecimate_props'):
            del bpy.types.Scene.sharpdecimate_props
        bpy.utils.unregister_class(SharpDecimateProperties)
    except Exception as e:
        print(f"SharpDecimate: Failed to unregister properties: {e}")