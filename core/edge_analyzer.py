# FILE: core/edge_analyzer.py
import bmesh
import bpy

def analyze_sharp_edges(bm, angle_threshold):
    """Анализ острых граней по углу между полигонами"""
    sharp_edges = []
    
    for edge in bm.edges:
        if len(edge.link_faces) == 2:
            angle = edge.calc_face_angle()
            angle_degrees = angle * 180.0 / 3.14159
            
            if angle_degrees > angle_threshold:
                sharp_edges.append(edge)
    
    return sharp_edges

def get_manual_sharp_edges(source_bm):
    """Получение граней, помеченных как Sharp вручную"""
    manual_sharp = []
    for edge in source_bm.edges:
        if not edge.smooth:  # Sharp edges have smooth=False
            manual_sharp.append(edge)
    return manual_sharp

def get_creased_edges(source_bm, crease_threshold=0.01):
    """Получение граней с Crease значениями"""
    creased_edges = []
    
    # Проверяем, поддерживает ли bmesh crease
    if hasattr(source_bm.edges, 'layers'):
        crease_layer = source_bm.edges.layers.crease.active
        if crease_layer:
            for edge in source_bm.edges:
                crease_value = edge[crease_layer]
                if crease_value > crease_threshold:
                    creased_edges.append(edge)
    
    return creased_edges

def analyze_protected_edges(bm, obj, angle_threshold, detail_group=None, detail_weight=0.5):
    """Анализ всех защищенных ребер (острые + детальные зоны)"""
    protected_edges = set()
    
    # 1. Автоматические острые грани
    sharp_edges = analyze_sharp_edges(bm, angle_threshold)
    protected_edges.update(sharp_edges)
    
    # 2. Ручные Sharp метки
    manual_sharp = get_manual_sharp_edges(bm)
    protected_edges.update(manual_sharp)
    
    # 3. Crease значения
    creased_edges = get_creased_edges(bm)
    protected_edges.update(creased_edges)
    
    return list(protected_edges)

def transfer_edge_data(source_bm, target_bm, keep_sharp=True, keep_crease=True, crease_threshold=0.01):
    """Перенос данных граней из исходного меша в целевой"""
    source_bm.edges.ensure_lookup_table()
    target_bm.edges.ensure_lookup_table()
    
    if keep_sharp:
        # Перенос ручных Sharp меток
        for i, edge in enumerate(source_bm.edges):
            if i < len(target_bm.edges) and not edge.smooth:
                target_bm.edges[i].smooth = False
    if keep_crease:
        # Перенос Crease значений (если поддерживается)
        if hasattr(source_bm.edges, 'layers') and hasattr(target_bm.edges, 'layers'):
            source_crease_layer = source_bm.edges.layers.crease.active
            target_crease_layer = target_bm.edges.layers.crease.active
            
            if source_crease_layer and target_crease_layer:
                for i, edge in enumerate(source_bm.edges):
                    if i < len(target_bm.edges):
                        crease_value = edge[source_crease_layer]
                        if crease_value > crease_threshold:
                            target_bm.edges[i][target_crease_layer] = crease_value

def preserve_hard_edges(target_bm, sharp_edges, manual_sharp_edges, creased_edges, source_crease_layer=None, target_crease_layer=None):
    """Сохранение всех типов острых граней в целевом меше"""
    
    # ПРАВКА: Используем множества для избежания дублирования
    processed_edges = set()
    
    # Сохраняем автоматически найденные острые грани
    for edge in sharp_edges:
        edge.smooth = False
        processed_edges.add(edge.index)
    
    # Сохраняем ручные Sharp метки (только для непроцессированных ребер)
    for edge in manual_sharp_edges:
        if edge.index < len(target_bm.edges) and edge.index not in processed_edges:
            target_edge = target_bm.edges[edge.index]
            target_edge.smooth = False
            processed_edges.add(edge.index)
    
    # Сохраняем Crease значения (если поддерживается)
    if (hasattr(target_bm.edges, 'layers') and 
        source_crease_layer is not None and 
        target_crease_layer is not None):
        
        for edge in creased_edges:
            if edge.index < len(target_bm.edges):
                target_edge = target_bm.edges[edge.index]
                
                # Получаем crease значение из исходного edge
                if hasattr(edge, 'layers'):
                    try:
                        crease_value = edge[source_crease_layer]
                        target_edge[target_crease_layer] = crease_value
                    except (KeyError, TypeError):
                        # Если crease значение недоступно, пропускаем
                        pass

def register():
    pass

def unregister():
    pass