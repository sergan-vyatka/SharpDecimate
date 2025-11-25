# FILE: locale_loader.py
import os
import json
import bpy

def load_locales():
    """Загрузка локалей из JSON файла"""
    addon_dir = os.path.dirname(__file__)
    locales_path = os.path.join(addon_dir, "locales.json")
    
    try:
        with open(locales_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"SharpDecimate: Error loading locales: {e}")
        return {"en": {}}

def get_available_languages():
    """Получение списка доступных языков из locales.json"""
    locales = load_locales()
    languages = []
    
    # Автоматически получаем языки из JSON
    lang_names = {
        'en': "English",
        'ru': "Russian", 
        'de': "German",
        'es': "Spanish",
        'fr': "French",
        'it': "Italian",
        'ja': "Japanese",
        'ko': "Korean",
        'zh': "Chinese",
        'pt': "Portuguese",
        'pl': "Polish",
        'cs': "Czech",
        'sk': "Slovak",
        'uk': "Ukrainian",
        'tr': "Turkish",
        'ar': "Arabic",
        'vi': "Vietnamese",
        'id': "Indonesian",
        'ms': "Malay",
        'th': "Thai",
        'hi': "Hindi",
        'he': "Hebrew",
        'fa': "Persian",
        'ro': "Romanian",
        'hu': "Hungarian",
        'nl': "Dutch",
        'sv': "Swedish",
        'no': "Norwegian",
        'fi': "Finnish",
        'da': "Danish",
        'el': "Greek",
        'bg': "Bulgarian",
        'sr': "Serbian",
        'hr': "Croatian",
        'sl': "Slovenian",
        'et': "Estonian",
        'lv': "Latvian",
        'lt': "Lithuanian",
        'ca': "Catalan",
        'eu': "Basque",
        'gl': "Galician"
    }
    
    for lang_code in locales.keys():
        display_name = lang_names.get(lang_code, lang_code.upper())
        languages.append((lang_code, display_name, f"{display_name} interface"))
    
    # Добавляем автоопределение
    languages.insert(0, ('auto', "Auto", "Use system language"))
    
    return languages

def get_text(key, lang="en"):
    """Получение перевода с кэшированием"""
    if not hasattr(get_text, "_cache"):
        get_text._cache = load_locales()
    
    locales = get_text._cache
    
    # Если язык auto, определяем системный
    if lang == 'auto':
        system_lang = bpy.context.preferences.view.language
        
        # Полная карта всех локалей Blender
        lang_mapping = {
            # Европейские языки
            'en_US': 'en', 'en': 'en', 'en_GB': 'en',
            'ru_RU': 'ru', 'ru': 'ru', 'ru_UA': 'ru',
            'de_DE': 'de', 'de': 'de', 'de_AT': 'de', 'de_CH': 'de',
            'es_ES': 'es', 'es': 'es', 'es_MX': 'es', 'es_AR': 'es',
            'fr_FR': 'fr', 'fr': 'fr', 'fr_CA': 'fr', 'fr_BE': 'fr', 'fr_CH': 'fr',
            'it_IT': 'it', 'it': 'it', 'it_CH': 'it',
            'pt_BR': 'pt', 'pt': 'pt', 'pt_PT': 'pt',
            'pl_PL': 'pl', 'pl': 'pl',
            'cs_CZ': 'cs', 'cs': 'cs',
            'sk_SK': 'sk', 'sk': 'sk',
            'uk_UA': 'uk', 'uk': 'uk',
            'ro_RO': 'ro', 'ro': 'ro',
            'hu_HU': 'hu', 'hu': 'hu',
            'nl_NL': 'nl', 'nl': 'nl', 'nl_BE': 'nl',
            'sv_SE': 'sv', 'sv': 'sv',
            'no_NO': 'no', 'no': 'no', 'nb_NO': 'no', 'nn_NO': 'no',
            'fi_FI': 'fi', 'fi': 'fi',
            'da_DK': 'da', 'da': 'da',
            'el_GR': 'el', 'el': 'el',
            'bg_BG': 'bg', 'bg': 'bg',
            'sr_RS': 'sr', 'sr': 'sr', 'sr_CS': 'sr', 'sr_ME': 'sr',
            'hr_HR': 'hr', 'hr': 'hr',
            'sl_SI': 'sl', 'sl': 'sl',
            'et_EE': 'et', 'et': 'et',
            'lv_LV': 'lv', 'lv': 'lv',
            'lt_LT': 'lt', 'lt': 'lt',
            'ca_ES': 'ca', 'ca': 'ca',
            'eu_ES': 'eu', 'eu': 'eu',
            'gl_ES': 'gl', 'gl': 'gl',
            
            # Азиатские языки
            'ja_JP': 'ja', 'ja': 'ja',
            'ko_KR': 'ko', 'ko': 'ko',
            'zh_CN': 'zh', 'zh': 'zh', 'zh_HANS': 'zh', 'zh_SG': 'zh',
            'zh_TW': 'zh', 'zh_HANT': 'zh', 'zh_HK': 'zh', 'zh_MO': 'zh',
            'vi_VN': 'vi', 'vi': 'vi',
            'th_TH': 'th', 'th': 'th',
            'hi_IN': 'hi', 'hi': 'hi',
            'id_ID': 'id', 'id': 'id',
            'ms_MY': 'ms', 'ms': 'ms',
            
            # Ближний Восток и Африка
            'ar_SA': 'ar', 'ar': 'ar', 'ar_EG': 'ar', 'ar_DZ': 'ar', 'ar_MA': 'ar',
            'he_IL': 'he', 'he': 'he',
            'fa_IR': 'fa', 'fa': 'fa',
            'tr_TR': 'tr', 'tr': 'tr',
            
            # Другие
            'af_ZA': 'en',  # Африкаанс → английский
            'sq_AL': 'en',  # Албанский → английский
            'hy_AM': 'en',  # Армянский → английский
            'az_AZ': 'en',  # Азербайджанский → английский
            'be_BY': 'en',  # Белорусский → английский
            'bs_BA': 'en',  # Боснийский → английский
            'cy_GB': 'en',  # Валлийский → английский
            'eo': 'en',     # Эсперанто → английский
            'fo_FO': 'en',  # Фарерский → английский
            'ga_IE': 'en',  # Ирландский → английский
            'gu_IN': 'en',  # Гуджарати → английский
            'is_IS': 'en',  # Исландский → английский
            'ka_GE': 'en',  # Грузинский → английский
            'kn_IN': 'en',  # Каннада → английский
            'km_KH': 'en',  # Кхмерский → английский
            'lo_LA': 'en',  # Лаосский → английский
            'mk_MK': 'en',  # Македонский → английский
            'ml_IN': 'en',  # Малаялам → английский
            'mr_IN': 'en',  # Маратхи → английский
            'ne_NP': 'en',  # Непальский → английский
            'pa_IN': 'en',  # Панджаби → английский
            'sa_IN': 'en',  # Санскрит → английский
            'si_LK': 'en',  # Сингальский → английский
            'sw_KE': 'en',  # Суахили → английский
            'ta_IN': 'en',  # Тамильский → английский
            'te_IN': 'en',  # Телугу → английский
            'ur_PK': 'en',  # Урду → английский
            'uz_UZ': 'en',  # Узбекский → английский
            'zu_ZA': 'en'   # Зулу → английский
        }
        
        lang = lang_mapping.get(system_lang, 'en')
    
    # Возвращаем перевод или ключ, если перевода нет
    return locales.get(lang, locales["en"]).get(key, key)