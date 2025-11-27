# FILE: __init__.py
bl_info = {
    "name": "SharpDecimate",
    "author": "NEFAS, Sukhikh Sergey",
    "version": (1, 0, 4),
    "blender": (3, 6, 23),
    "location": "View3D > Sidebar > Tool",
    "description": "Decimate with sharp edges preservation - FREE VERSION",
    "category": "Mesh",
}

import bpy
import sys
import importlib
import os

# ТОЛЬКО БАЗОВЫЕ МОДУЛИ FREE-ВЕРСИИ
base_modules = [
    ".locale_loader",
    ".preferences",
    ".core.edge_analyzer",
    ".core.base_decimate",
    ".operators.generate_lowpoly",
    ".ui.panel"
]

# FREE-ВЕРСИЯ - НЕТ PRO-ФУНКЦИЙ
has_pro = False
all_modules = base_modules

def register_modules(modules_list):
    """Рекурсивная регистрация всех модулей"""
    registered = []
    for module_name in modules_list:
        try:
            if module_name.startswith("."):
                full_name = __package__ + module_name
            else:
                full_name = module_name
                
            if full_name in sys.modules:
                importlib.reload(sys.modules[full_name])
            else:
                importlib.import_module(full_name, package=__package__)
                
            # Регистрация классов Blender
            module = sys.modules[full_name]
            if hasattr(module, 'register'):
                module.register()
                
            registered.append(module)
            
        except Exception as e:
            print(f"SharpDecimate: Failed to register {module_name}: {e}")
    
    return registered

def unregister_modules(modules_list):
    """Рекурсивная отмена регистрации всех модулей"""
    for module_name in reversed(modules_list):
        try:
            if module_name.startswith("."):
                full_name = __package__ + module_name
            else:
                full_name = module_name
                
            if full_name in sys.modules:
                module = sys.modules[full_name]
                if hasattr(module, 'unregister'):
                    module.unregister()
                    
        except Exception as e:
            print(f"SharpDecimate: Failed to unregister {module_name}: {e}")

def register():
    """Регистрация аддона"""
    print("SharpDecimate: FREE VERSION LOADED")
    
    # Очистка кэша локалей
    from .locale_loader import get_text
    if hasattr(get_text, "_cache"):
        delattr(get_text, "_cache")
    
    # УДАЛЕНО: safe_cleanup() - опасная функция
    
    # Регистрация всех модулей
    register_modules(all_modules)
    
    print(f"SharpDecimate FREE v{bl_info['version']} registered")

def unregister():
    """Отмена регистрации аддона"""
    # Отмена регистрации модулей
    unregister_modules(all_modules)
    
    # УДАЛЕНО: reset_all() - опасная функция
    
    # Очистка кэша локалей
    from .locale_loader import get_text
    if hasattr(get_text, "_cache"):
        delattr(get_text, "_cache")
    
    print("SharpDecimate unregistered")

if __name__ == "__main__":
    register()