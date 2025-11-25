# FILE: operators/generate_lowpoly.py
import bpy
import bmesh
from bpy.types import Operator

from ..locale_loader import get_text
from ..preferences import get_ui_language
from ..core.base_decimate import decimate_single_object

class SHARPDECIMATE_OT_generate_lowpoly(Operator):
    bl_idname = "mesh.sharpdecimate_generate_lowpoly"
    bl_label = "Generate Lowpoly"
    bl_description = "Create lowpoly version preserving sharp edges"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and 
                context.active_object.type == 'MESH')

    def execute(self, context):
        scene = context.scene
        props = scene.sharpdecimate_props
        lang = get_ui_language(context)
        
        original_obj = context.active_object
        if original_obj.type != 'MESH':
            self.report({'WARNING'}, get_text("no_mesh", lang))
            return {'CANCELLED'}
        
        # 🔴 НАЧАЛО ПРОГРЕСС-БАРА
        wm = context.window_manager
        wm.progress_begin(0, 100)
        
        try:
            # ПРАВКА: Добавляем валидацию меша
            if not self.validate_mesh(original_obj):
                self.report({'ERROR'}, get_text("invalid_mesh", lang))
                wm.progress_end()
                return {'CANCELLED'}
            
            wm.progress_update(10)
            
            # 🔴 ПРОВЕРКА ВОДОНЕПРОНИЦАЕМОСТИ ДО ДЕЦИМАЦИИ
            pre_check_ok, pre_check_message = self.validate_mesh_watertight(original_obj)
            if not pre_check_ok:
                self.report({'WARNING'}, f"Mesh issues before decimation: {pre_check_message}")
                # Не отменяем, но предупреждаем пользователя
            
            wm.progress_update(20)
            
            # Сохраняем статистику исходного меша
            original_polycount = len(original_obj.data.polygons)
            original_vertices = len(original_obj.data.vertices)
            
            # В free-версии только одиночный объект
            if len(context.selected_objects) > 1:
                self.report({'WARNING'}, get_text("multi_select", lang))
                wm.progress_end()
                return {'CANCELLED'}

            print(f"🟡 STARTING DECIMATION: {original_obj.name}")
            
            # 🔴 БЕЗОПАСНАЯ ДЕЦИМАЦИЯ С ОБРАБОТКОЙ ОШИБОК
            lowpoly_obj = self.safe_decimate(context, original_obj, props, wm)
            
            if lowpoly_obj is None:
                self.report({'ERROR'}, get_text("decimation_failed", lang))
                wm.progress_end()
                return {'CANCELLED'}
            
            wm.progress_update(90)
            
            # 🔴 ПРОВЕРКА ВОДОНЕПРОНИЦАЕМОСТИ ПОСЛЕ ДЕЦИМАЦИИ
            post_check_ok, post_check_message = self.validate_mesh_watertight(lowpoly_obj)
            if not post_check_ok:
                self.report({'WARNING'}, f"Mesh issues after decimation: {post_check_message}")
                # Показываем предупреждение, но не отменяем операцию
            
            # ДОБАВЛЯЕМ ОТЛАДОЧНУЮ ИНФОРМАЦИЮ
            print(f"🟢 LOWPOLY OBJECT CREATED: {lowpoly_obj.name}")
            print(f"📍 Location: {lowpoly_obj.location}")
            print(f"👀 Visible: {lowpoly_obj.visible_get()}")
            print(f"📊 Polycount: {len(lowpoly_obj.data.polygons)}")
            
            # Делаем объект видимым и выделяем его
            lowpoly_obj.hide_set(False)
            lowpoly_obj.hide_viewport = False
            lowpoly_obj.hide_render = False
            
            # Выделяем новый объект
            bpy.ops.object.select_all(action='DESELECT')
            lowpoly_obj.select_set(True)
            context.view_layer.objects.active = lowpoly_obj
            
            # Статистика результата
            final_polycount = len(lowpoly_obj.data.polygons)
            final_vertices = len(lowpoly_obj.data.vertices)
            
            # ПРАВКА: Защита от деления на ноль
            if original_polycount > 0:
                reduction = (1 - final_polycount / original_polycount) * 100
            else:
                reduction = 0
            
            success_message = (
                f"{get_text('success', lang)}{lowpoly_obj.name} | "
                f"Polys: {original_polycount} → {final_polycount} "
                f"({reduction:.1f}% reduction)"
            )
            
            # Добавляем информацию о проверке водонепроницаемости
            if not post_check_ok:
                success_message += f" | ⚠️ Check mesh integrity"
            
            self.report({'INFO'}, success_message)
            wm.progress_update(100)
            return {'FINISHED'}
            
        except Exception as e:
            error_msg = f"{get_text('decimation_error', lang)}: {str(e)}"
            self.report({'ERROR'}, error_msg)
            print(f"🔴 DECIMATION ERROR: {e}")
            import traceback
            traceback.print_exc()
            wm.progress_end()
            return {'CANCELLED'}
        finally:
            # 🔴 ГАРАНТИРУЕМ ЗАВЕРШЕНИЕ ПРОГРЕСС-БАРА
            try:
                wm.progress_end()
            except:
                pass
    
    def safe_decimate(self, context, original_obj, props, wm):
        """Безопасная децимация с обработкой ошибок и прогресс-баром"""
        try:
            wm.progress_update(30)
            result = decimate_single_object(context, original_obj, props)
            wm.progress_update(80)
            return result
        except Exception as e:
            print(f"🔴 Safe decimate failed: {e}")
            # Восстанавливаем состояние Blender
            self.restore_blender_state(context, original_obj)
            return None
    
    def restore_blender_state(self, context, original_obj):
        """Восстановление состояния Blender после ошибки"""
        try:
            # Гарантируем выход в объектный режим
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Восстанавливаем выделение оригинала
            bpy.ops.object.select_all(action='DESELECT')
            original_obj.select_set(True)
            context.view_layer.objects.active = original_obj
            
            print("✅ Blender state restored after error")
        except Exception as restore_error:
            print(f"⚠️ State restore failed: {restore_error}")
    
    def validate_mesh(self, obj):
        """Проверка пригодности меша для упрощения"""
        try:
            mesh = obj.data
            
            # Проверка что объект доступен
            if not mesh or not hasattr(mesh, 'polygons'):
                return False
            
            # Проверка минимального количества полигонов
            if len(mesh.polygons) < 4:
                return False
            
            # Проверка минимального количества вершин
            if len(mesh.vertices) < 4:
                return False
            
            # Проверка на наличие геометрии
            if not mesh.polygons:
                return False
                
            return True
        except Exception as e:
            print(f"⚠️ Mesh validation error: {e}")
            return False
    
    def validate_mesh_watertight(self, obj):
        """Проверка что меш водонепроницаем и не имеет проблемной геометрии"""
        try:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.edges.ensure_lookup_table()
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            
            issues = []
            
            # 1. Проверка на non-manifold edges (грани с >2 полигонов)
            non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
            if non_manifold_edges:
                issues.append(f"Non-manifold edges: {len(non_manifold_edges)}")
            
            # 2. Проверка на loose vertices (вершины без полигонов)
            loose_verts = [v for v in bm.verts if not v.link_edges]
            if loose_verts:
                issues.append(f"Loose vertices: {len(loose_verts)}")
            
            # 3. Проверка на degenerate geometry (вырожденные полигоны)
            degenerate_faces = [f for f in bm.faces if f.calc_area() < 0.0001]
            if degenerate_faces:
                issues.append(f"Degenerate faces: {len(degenerate_faces)}")
            
            # 4. Проверка на overlapping vertices (пересекающиеся вершины)
            vert_locations = {}
            for v in bm.verts:
                key = (round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))
                if key in vert_locations:
                    vert_locations[key] += 1
                else:
                    vert_locations[key] = 1
            
            overlapping_verts = sum(1 for count in vert_locations.values() if count > 1)
            if overlapping_verts > 0:
                issues.append(f"Overlapping vertices: {overlapping_verts}")
            
            bm.free()
            
            if issues:
                return False, "; ".join(issues)
            
            return True, "Mesh is watertight"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"

def register():
    bpy.utils.register_class(SHARPDECIMATE_OT_generate_lowpoly)

def unregister():
    bpy.utils.unregister_class(SHARPDECIMATE_OT_generate_lowpoly)