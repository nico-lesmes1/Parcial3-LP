from tipos import tipo_literal_desde_valor, promover_tipos, es_numerico, tipo_valor_runtime

def evaluar_expr_sin_contexto(nodo_expr):
    tipo, valor = evaluar_expr_con_contexto(nodo_expr, {}, None)
    return tipo, valor

def evaluar_expr_con_contexto(nodo_expr, contexto_alias_a_registro, esquema_local):
    if isinstance(nodo_expr, tuple):
        op = nodo_expr[0]
        if op == 'LIT':
            return tipo_literal_desde_valor(nodo_expr[1])
        if op == 'REF':
            alias, col = nodo_expr[1], nodo_expr[2]
            if alias is None:
                if esquema_local is not None:
                    registro = contexto_alias_a_registro.get(None) or contexto_alias_a_registro.get('')
                    if registro is None:
                        return 'nulo', None
                    val = registro.get(col)
                    return tipo_valor_runtime(val), val
                if len(contexto_alias_a_registro) == 1:
                    registro = list(contexto_alias_a_registro.values())[0]
                    val = registro.get(col)
                    return tipo_valor_runtime(val), val
                if None in contexto_alias_a_registro:
                    registro = contexto_alias_a_registro[None]
                    val = registro.get(col)
                    return tipo_valor_runtime(val), val
                encontrados = []
                for reg in contexto_alias_a_registro.values():
                    if isinstance(reg, dict) and col in reg:
                        encontrados.append(reg)
                if len(encontrados) == 1:
                    val = encontrados[0][col]
                    return tipo_valor_runtime(val), val
                return 'nulo', None
            else:
                registro = contexto_alias_a_registro.get(alias)
                if registro is None:
                    return 'nulo', None
                val = registro.get(col)
                return tipo_valor_runtime(val), val
        if op == 'NEG':
            t, v = evaluar_expr_con_contexto(nodo_expr[1], contexto_alias_a_registro, esquema_local)
            if not es_numerico(t):
                return 'nulo', None
            return t, -v
        if op in ('MAS','MENOS','POR','DIV'):
            t1, v1 = evaluar_expr_con_contexto(nodo_expr[1], contexto_alias_a_registro, esquema_local)
            t2, v2 = evaluar_expr_con_contexto(nodo_expr[2], contexto_alias_a_registro, esquema_local)
            tp = promover_tipos(t1, t2)
            if tp is None:
                if t1 == 'cadena' and t2 == 'cadena' and op == 'MAS':
                    return 'cadena', str(v1) + str(v2)
                return 'nulo', None
            try:
                if op == 'MAS':
                    return tp, (v1 + v2)
                if op == 'MENOS':
                    return tp, (v1 - v2)
                if op == 'POR':
                    return tp, (v1 * v2)
                if op == 'DIV':
                    # división: resultado en flotante si uno es flotante o se fuerza
                    if v2 == 0:
                        return 'nulo', None
                    return 'flotante' if tp == 'flotante' or op == 'DIV' else tp, (v1 / v2)
            except Exception:
                return 'nulo', None
        if op in ('IGUAL','MENOR','MAYOR','MENOR_IGUAL','MAYOR_IGUAL','DISTINTO'):
            t1, v1 = evaluar_expr_con_contexto(nodo_expr[1], contexto_alias_a_registro, esquema_local)
            t2, v2 = evaluar_expr_con_contexto(nodo_expr[2], contexto_alias_a_registro, esquema_local)
            if op == 'IGUAL':
                return 'booleano', (v1 == v2)
            if op == 'DISTINTO':
                return 'booleano', (v1 != v2)
            if op == 'MENOR':
                return 'booleano', (v1 < v2)
            if op == 'MAYOR':
                return 'booleano', (v1 > v2)
            if op == 'MENOR_IGUAL':
                return 'booleano', (v1 <= v2)
            if op == 'MAYOR_IGUAL':
                return 'booleano', (v1 >= v2)
        if op == 'AND':
            t1, v1 = evaluar_expr_con_contexto(nodo_expr[1], contexto_alias_a_registro, esquema_local)
            if not bool(v1):
                return 'booleano', False
            t2, v2 = evaluar_expr_con_contexto(nodo_expr[2], contexto_alias_a_registro, esquema_local)
            return 'booleano', bool(v2)
        if op == 'OR':
            t1, v1 = evaluar_expr_con_contexto(nodo_expr[1], contexto_alias_a_registro, esquema_local)
            if bool(v1):
                return 'booleano', True
            t2, v2 = evaluar_expr_con_contexto(nodo_expr[2], contexto_alias_a_registro, esquema_local)
            return 'booleano', bool(v2)
        if op == 'NOT':
            t, v = evaluar_expr_con_contexto(nodo_expr[1], contexto_alias_a_registro, esquema_local)
            return 'booleano', (not bool(v))
    return 'nulo', None