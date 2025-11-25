# FILE: ui/panel.py
import bpy
from bpy.types import Panel, Operator

from ..locale_loader import get_text
from ..preferences import get_ui_language, get_preferences

class SHARPDECIMATE_OT_auto_setup_materials(Operator):
    """Автоматически создать и настроить материалы"""
    bl_idname = "sharpdecimate.auto_setup_materials"
    bl_label = "Auto Setup Materials"
    bl_description = "Automatically create and setup materials for material-based decimation"
    
    def execute(self, context):
        try:
            obj = context.active_object
            if not obj or obj.type != 'MESH':
                self.report({'WARNING'}, get_text("select_mesh_first", bpy.context))
                return {'CANCELLED'}
            
            # Получаем язык для названий материалов
            lang = get_ui_language(context)
            
            # ТОЛЬКО 2 материала с локализацией
            materials_data = [
                {"name": get_text("high_detail_material", lang), "color": (1.0, 0.2, 0.2, 1.0)},  # Красный
                {"name": get_text("low_detail_material", lang), "color": (0.7, 0.7, 0.7, 1.0)},   # Серый
            ]
            
            # Очищаем существующие материалы
            obj.data.materials.clear()
            
            # Создаем новые материалы
            for mat_data in materials_data:
                mat = bpy.data.materials.new(name=mat_data["name"])
                mat.use_nodes = True
                mat.diffuse_color = mat_data["color"]
                
                # Настраиваем ноды для видимости цвета
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                
                # Очищаем стандартные ноды
                nodes.clear()
                
                # Добавляем Diffuse BSDF и Output
                diffuse = nodes.new(type='ShaderNodeBsdfDiffuse')
                output = nodes.new(type='ShaderNodeOutputMaterial')
                diffuse.inputs['Color'].default_value = mat_data["color"]
                
                # Соединяем
                links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])
                
                # Добавляем материал к объекту
                obj.data.materials.append(mat)
            
            # Сразу назначаем ВЕСЬ объект на LowDetail материал
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            
            # Устанавливаем активный материал как LowDetail (индекс 1)
            obj.active_material_index = 1
            bpy.ops.object.material_slot_assign()
            
            bpy.ops.object.mode_set(mode='OBJECT')
            
            self.report({'INFO'}, get_text("materials_created", lang))
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, get_text("setup_failed", lang) + f": {str(e)}")
            return {'CANCELLED'}

class SHARPDECIMATE_OT_quick_tutorial(Operator):
    """Быстрая инструкция по работе"""
    bl_idname = "sharpdecimate.quick_tutorial" 
    bl_label = "Quick Tutorial"
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=400)
    
    def draw(self, context):
        layout = self.layout
        lang = get_ui_language(bpy.context)
        layout.label(text="🎯 " + get_text("quick_tutorial", lang), icon='INFO')
        layout.separator()
        
        steps = [
            get_text("tutorial_step1", lang),
            get_text("tutorial_step2", lang),
            get_text("tutorial_step3", lang),
            get_text("tutorial_step4", lang),
            get_text("tutorial_step5", lang),
            get_text("tutorial_step6", lang),
        ]
        
        for step in steps:
            row = layout.row()
            row.label(text=step)
        
        layout.separator()
        layout.label(text="💡 " + get_text("tutorial_tip", lang))

class SHARPDECIMATE_OT_show_tooltip(Operator):
    """Показать подсказку"""
    bl_idname = "sharpdecimate.show_tooltip"
    bl_label = "Tooltip"
    
    text: bpy.props.StringProperty()
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=300)
    
    def draw(self, context):
        layout = self.layout
        words = self.text.split()
        lines = []
        current_line = []
        
        for word in words:
            if len(' '.join(current_line + [word])) < 50:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        for line in lines:
            layout.label(text=line)

class SHARPDECIMATE_PT_main_panel(Panel):
    bl_label = "Sharp Decimate"
    bl_idname = "SHARPDECIMATE_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sharpdecimate_props
        
        try:
            prefs = get_preferences(context)
            lang = get_ui_language(context)
        except (KeyError, AttributeError):
            lang = 'en'
        
        self.bl_label = get_text("panel_name", lang)
        
        # === ПЕРЕКЛЮЧАТЕЛЬ ЯЗЫКА ===
        box = layout.box()
        row = box.row(align=True)
        row.label(text=get_text("language", lang) + ":", icon='WORLD_DATA')
        row.prop(prefs, "ui_language", text="")
        
        # === СТАТУС ОБЪЕКТА ===
        if context.active_object and context.active_object.type == 'MESH':
            obj = context.active_object
            original_faces = len(obj.data.polygons)
            
            box = layout.box()
            row = box.row()
            row.label(text=get_text("selected_object", lang) + f": {obj.name}", icon='OBJECT_DATA')
            row = box.row()
            row.label(text=get_text("faces_count", lang) + f": {original_faces}", icon='MESH_DATA')
        else:
            box = layout.box()
            row = box.row()
            row.label(text=get_text("select_mesh", lang), icon='INFO')
            return
        
        # === РЕЖИМЫ ДЕЦИМАЦИИ ===
        box = layout.box()
        box.label(text="🎯 " + get_text("decimation_mode", lang), icon='MOD_DECIM')
        
        # Переключатель режимов
        row = box.row()
        row.prop(props, "use_material_decimation", text=get_text("smart_decimation", lang), toggle=True)
        op = row.operator("sharpdecimate.show_tooltip", text="", icon='QUESTION')
        op.text = get_text("smart_decimation_desc", lang)
        
        # === ДИНАМИЧЕСКИЙ ИНТЕРФЕЙС ===
        if props.use_material_decimation:
            # SMART MODE - Material-Based
            self.draw_smart_mode(layout, context, props, lang)
        else:
            # STANDARD MODE
            self.draw_standard_mode(layout, context, props, lang)
        
        # Основная кнопка генерации
        layout.separator()
        box = layout.box()
        box.label(text="🚀 " + get_text("generate_lowpoly", lang), icon='RENDER_RESULT')
        
        col = box.column()
        row = col.row()
        row.operator(
            "mesh.sharpdecimate_generate_lowpoly",
            text=get_text("generate_button", lang),
            icon='EXPORT'
        )
        
        # Информация о режиме
        if props.use_material_decimation:
            row = box.row()
            row.label(text="🎯 " + get_text("smart_mode_info", lang))
        else:
            row = box.row()
            row.label(text="🔧 " + get_text("standard_mode_info", lang))
        
        # Помощь
        row = layout.row()
        row.operator("sharpdecimate.quick_tutorial", text=get_text("need_help", lang), icon='QUESTION')
        
        # ПРОМО PRO-ВЕРСИИ
        self.draw_pro_promotion(layout, lang)
    
    def draw_standard_mode(self, layout, context, props, lang):
        """Отрисовка стандартного режима"""
        box = layout.box()
        box.label(text="🔧 " + get_text("standard_settings", lang), icon='SETTINGS')
        
        # Ratio
        row = box.row()
        row.prop(props, "ratio", text=get_text("simplification", lang), slider=True)
        
        # Статистика
        if context.active_object and context.active_object.type == 'MESH':
            obj = context.active_object
            original_faces = len(obj.data.polygons)
            target_faces = int(original_faces * props.ratio)
            reduction = (1 - props.ratio) * 100
            
            row = box.row()
            row.label(text=get_text("result_faces", lang) + f": {original_faces} → {target_faces}", icon='SORTTIME')
            row = box.row()
            row.label(text=get_text("reduction", lang) + f": {reduction:.0f}%", icon='TRIA_DOWN')
        
        # Дополнительные настройки
        col = box.column(align=True)
        col.prop(props, "sharp_angle", text=get_text("sharp_angle", lang))
        col.prop(props, "keep_sharp", text=get_text("keep_sharp", lang))
        col.prop(props, "keep_crease", text=get_text("keep_crease", lang))
    
    def draw_smart_mode(self, layout, context, props, lang):
        """Отрисовка smart режима"""
        box = layout.box()
        box.label(text="🎯 " + get_text("smart_settings", lang), icon='SOLO_ON')
        
        # Кнопка настройки материалов
        if context.active_object and context.active_object.type == 'MESH':
            obj = context.active_object
            
            # Проверяем материалы
            has_correct_materials = (
                len(obj.data.materials) >= 2 and 
                any(get_text("high_detail_material", lang) in mat.name for mat in obj.data.materials) and
                any(get_text("low_detail_material", lang) in mat.name for mat in obj.data.materials)
            )
            
            if not has_correct_materials:
                row = box.row()
                row.operator("sharpdecimate.auto_setup_materials", icon='MATERIAL', text=get_text("setup_materials", lang))
                row = box.row()
                row.label(text=get_text("setup_materials_desc", lang), icon='INFO')
            else:
                row = box.row()
                row.label(text="✅ " + get_text("materials_ready", lang), icon='CHECKMARK')
                row = box.row()
                row.label(text=get_text("assign_high_detail", lang), icon='EDITMODE_HLT')
        
        # Ratios для smart режима
        col = box.column(align=True)
        col.prop(props, "material_high_ratio", text=get_text("important_areas", lang), slider=True)
        col.prop(props, "material_low_ratio", text=get_text("other_areas", lang), slider=True)
        
        # Статистика для smart режима
        if context.active_object and context.active_object.type == 'MESH':
            obj = context.active_object
            if obj.data.materials:
                high_detail_faces = 0
                low_detail_faces = 0
                
                for poly in obj.data.polygons:
                    if poly.material_index < len(obj.data.materials):
                        mat = obj.data.materials[poly.material_index]
                        if mat and get_text("high_detail_material", lang) in mat.name:
                            high_detail_faces += 1
                        else:
                            low_detail_faces += 1
                
                total_faces = high_detail_faces + low_detail_faces
                if total_faces > 0:
                    box_inner = box.box()
                    box_inner.label(text="📊 " + get_text("face_distribution", lang), icon='MESH_DATA')
                    row = box_inner.row()
                    row.label(text=get_text("high_detail_faces", lang) + f": {high_detail_faces} ({high_detail_faces/total_faces*100:.0f}%)")
                    row = box_inner.row()
                    row.label(text=get_text("low_detail_faces", lang) + f": {low_detail_faces} ({low_detail_faces/total_faces*100:.0f}%)")
        
        # Дополнительные настройки (общие)
        col = box.column(align=True)
        col.prop(props, "sharp_angle", text=get_text("sharp_angle", lang))
        col.prop(props, "keep_sharp", text=get_text("keep_sharp", lang))
        col.prop(props, "keep_crease", text=get_text("keep_crease", lang))
    
    def draw_pro_promotion(self, layout, lang):
        """Промо Pro-версии"""
        layout.separator()
        box = layout.box()
        box.label(text="💎 " + get_text("pro_version", lang), icon='SOLO_ON')
        
        features = [
            get_text("pro_feature_lod", lang),
            get_text("pro_feature_batch", lang),
            get_text("pro_feature_presets", lang),
            get_text("pro_feature_uv", lang)
        ]
        
        for feature in features:
            row = box.row()
            row.label(text=feature)
        
        row = box.row()
        row.operator("wm.url_open", text=get_text("get_pro_version", lang), icon='URL').url = "https://boosty.to/cmapnep"

def register():
    bpy.utils.register_class(SHARPDECIMATE_OT_auto_setup_materials)
    bpy.utils.register_class(SHARPDECIMATE_OT_quick_tutorial)
    bpy.utils.register_class(SHARPDECIMATE_OT_show_tooltip)
    bpy.utils.register_class(SHARPDECIMATE_PT_main_panel)

def unregister():
    bpy.utils.unregister_class(SHARPDECIMATE_PT_main_panel)
    bpy.utils.unregister_class(SHARPDECIMATE_OT_show_tooltip)
    bpy.utils.unregister_class(SHARPDECIMATE_OT_quick_tutorial)
    bpy.utils.unregister_class(SHARPDECIMATE_OT_auto_setup_materials)