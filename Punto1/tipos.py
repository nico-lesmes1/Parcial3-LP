TIPOS_VALIDOS = {'entero', 'flotante', 'cadena', 'booleano'}

import re

def tipo_literal_desde_valor(valor_str):

    if re.fullmatch(r'\d+\.\d+', valor_str):
        return 'flotante', float(valor_str)
    if re.fullmatch(r'\d+', valor_str):
        return 'entero', int(valor_str)
    if (valor_str.startswith("'") and valor_str.endswith("'")) or (valor_str.startswith('"') and valor_str.endswith('"')):
        inner = valor_str[1:-1].encode('utf-8').decode('unicode_escape')
        return 'cadena', inner
    if valor_str.upper() == 'TRUE':
        return 'booleano', True
    if valor_str.upper() == 'FALSE':
        return 'booleano', False
    return 'cadena', valor_str

def promover_tipos(t1, t2):
    if t1 == t2:
        return t1
    if (t1 == 'entero' and t2 == 'flotante') or (t1 == 'flotante' and t2 == 'entero'):
        return 'flotante'
    return None

def es_numerico(tipo):
    return tipo in ('entero', 'flotante')

def tipo_valor_runtime(val):
    if isinstance(val, bool):
        return 'booleano'
    if isinstance(val, int):
        return 'entero'
    if isinstance(val, float):
        return 'flotante'
    if isinstance(val, str):
        return 'cadena'
    if val is None:
        return 'nulo'
    return 'cadena'