import bpy
from bpy.types import AddonPreferences
from bpy.props import EnumProperty

from .locale_loader import get_text, get_available_languages

# Основное имя аддона
ADDON_NAME = "SharpDecimate"

def get_preferences(context=None):
    """Получение настроек аддона"""
    if context is None:
        context = bpy.context
    return context.preferences.addons[ADDON_NAME].preferences

def get_ui_language(context=None):
    """Получение языка UI с автоматическим определением системного"""
    prefs = get_preferences(context)
    
    # Если язык установлен в "Auto", определяем системный
    if prefs.ui_language == 'auto':
        # Получаем язык Blender
        system_lang = bpy.context.preferences.view.language
        if system_lang in ['ru_RU', 'ru']:
            return 'ru'
        else:
            return 'en'
    else:
        return prefs.ui_language

class SharpDecimatePreferences(AddonPreferences):
    bl_idname = ADDON_NAME

    def update_language(self, context):
        """Принудительное обновление всех панелей при изменении языка"""
        # Перерисовываем все области
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()

    ui_language: EnumProperty(
        name="Language",
        description="Interface language",
        items=get_available_languages(),
        default='auto',
        update=update_language
    )

    def draw(self, context):
        layout = self.layout
        lang = get_ui_language(context)
        layout.prop(self, "ui_language", text=get_text("language", lang))
        
        # Информация о текущем языке
        current_lang = get_ui_language(context)
        if current_lang == 'auto':
            system_lang = bpy.context.preferences.view.language
            layout.label(text=get_text("system_language", lang) + f": {system_lang}")
        
        layout.label(text=get_text("by_nefas", lang))

def register():
    bpy.utils.register_class(SharpDecimatePreferences)

def unregister():
    bpy.utils.unregister_class(SharpDecimatePreferences)