from tipos import tipo_literal_desde_valor, promover_tipo, es_numerico, tipo_valor_runtime
from matriz import matriz_desde_literal, Matriz, matmul_transpose, matmul_block, transpose, crear_matriz_ceros

def evaluar_literal_numero(token_valor):
    return tipo_literal_desde_valor(token_valor)

def evaluar_expr(nodo, tabla_simbolos, errores, opciones_op=None):
    if opciones_op is None:
        opciones_op = {'usar_bloque': False, 'tile': 32}
    if nodo[0] == 'LIT_NUM':
        tipo, val = tipo_literal_desde_valor(nodo[1])
        return {'tipo': 'escalar', 'tipo_elemento': tipo, 'valor': val}
    if nodo[0] == 'LIT_MAT':
        try:
            mat = matriz_desde_literal(nodo[1])
            return {'tipo': 'matriz', 'tipo_elemento': mat.tipo_elemento, 'filas': mat.filas, 'columnas': mat.columnas, 'valor': mat}
        except Exception as e:
            errores.append({'mensaje': f"Error literal matriz: {e}"})
            return {'tipo': 'error'}
    if nodo[0] == 'REF':
        nombre = nodo[1]
        if nombre not in tabla_simbolos:
            errores.append({'mensaje': f"Variable no declarada: {nombre}"})
            return {'tipo': 'error'}
        info = tabla_simbolos[nombre]
        return info
    if nodo[0] == 'NEG':
        op = evaluar_expr(nodo[1], tabla_simbolos, errores, opciones_op)
        if op.get('tipo') != 'escalar':
            errores.append({'mensaje': "Negación solo aplicable a escalares"})
            return {'tipo': 'error'}
        return {'tipo': 'escalar', 'tipo_elemento': op['tipo_elemento'], 'valor': -op['valor']}
    if nodo[0] in ('MAS', 'MENOS', 'POR', 'DIV', 'ARITM'):
        op_iz = evaluar_expr(nodo[1], tabla_simbolos, errores, opciones_op)
        op_dr = evaluar_expr(nodo[2], tabla_simbolos, errores, opciones_op)
        if op_iz.get('tipo') == 'escalar' and op_dr.get('tipo') == 'escalar':
            if not es_numerico(op_iz['tipo_elemento']) or not es_numerico(op_dr['tipo_elemento']):
                errores.append({'mensaje': "Operación aritmética solo para numéricos"})
                return {'tipo': 'error'}
            tipo_res = promover_tipo(op_iz['tipo_elemento'], op_dr['tipo_elemento'])
            if tipo_res is None:
                errores.append({'mensaje': f"Tipos no compatibles: {op_iz['tipo_elemento']} y {op_dr['tipo_elemento']}"})
                return {'tipo': 'error'}
            v1 = op_iz['valor']; v2 = op_dr['valor']
            if nodo[0] == 'MAS':
                res = v1 + v2
            elif nodo[0] == 'MENOS':
                res = v1 - v2
            elif nodo[0] == 'POR':
                res = v1 * v2
            else:
                try:
                    res = v1 / v2
                except Exception:
                    errores.append({'mensaje': "Error en división (posible división por cero)"})
                    return {'tipo': 'error'}
            if tipo_res == 'entero':
                res = int(res)
            else:
                res = float(res)
            return {'tipo': 'escalar', 'tipo_elemento': tipo_res, 'valor': res}
        if nodo[0] == 'POR':
            if op_iz.get('tipo') == 'escalar' and op_dr.get('tipo') == 'matriz':
                esc = op_iz['valor']
                M = op_dr['valor']
                tipo_res = promover_tipo(op_iz['tipo_elemento'], op_dr['tipo_elemento'])
                if tipo_res is None:
                    errores.append({'mensaje': "Tipos no compatibles en multiplicación escalar*matriz"})
                    return {'tipo': 'error'}
                C = crear_matriz_ceros(M.filas, M.columnas, tipo_res)
                for i in range(M.filas):
                    for j in range(M.columnas):
                        v = M.get(i, j) * esc
                        C.set(i, j, float(v) if tipo_res == 'flotante' else int(v))
                return {'tipo': 'matriz', 'tipo_elemento': tipo_res, 'filas': C.filas, 'columnas': C.columnas, 'valor': C}
            if op_iz.get('tipo') == 'matriz' and op_dr.get('tipo') == 'escalar':
                esc = op_dr['valor']
                M = op_iz['valor']
                tipo_res = promover_tipo(op_iz['tipo_elemento'], op_dr['tipo_elemento'])
                if tipo_res is None:
                    errores.append({'mensaje': "Tipos no compatibles en multiplicación matriz*escalar"})
                    return {'tipo': 'error'}
                C = crear_matriz_ceros(M.filas, M.columnas, tipo_res)
                for i in range(M.filas):
                    for j in range(M.columnas):
                        v = M.get(i, j) * esc
                        C.set(i, j, float(v) if tipo_res == 'flotante' else int(v))
                return {'tipo': 'matriz', 'tipo_elemento': tipo_res, 'filas': C.filas, 'columnas': C.columnas, 'valor': C}
        if op_iz.get('tipo') == 'matriz' and op_dr.get('tipo') == 'matriz':
            A = op_iz['valor']; B = op_dr['valor']
            if A.filas != B.filas or A.columnas != B.columnas:
                errores.append({'mensaje': "Operación entre matrices: dimensiones deben coincidir para suma/resta"})
                return {'tipo': 'error'}
            tipo_res = promover_tipo(A.tipo_elemento, B.tipo_elemento)
            if tipo_res is None:
                errores.append({'mensaje': f"Tipos de elementos incompatibles: {A.tipo_elemento} y {B.tipo_elemento}"})
                return {'tipo': 'error'}
            C = crear_matriz_ceros(A.filas, A.columnas, tipo_res)
            for i in range(A.filas):
                for j in range(A.columnas):
                    a = A.get(i, j); b = B.get(i, j)
                    if nodo[0] == 'MAS':
                        v = a + b
                    else:
                        v = a - b
                    C.set(i, j, float(v) if tipo_res == 'flotante' else int(v))
            return {'tipo': 'matriz', 'tipo_elemento': tipo_res, 'filas': C.filas, 'columnas': C.columnas, 'valor': C}
        errores.append({'mensaje': 'Operación aritmética inválida entre tipos'})
        return {'tipo': 'error'}
    if nodo[0] == 'ARROBA': 
        op_iz = evaluar_expr(nodo[1], tabla_simbolos, errores, opciones_op)
        op_dr = evaluar_expr(nodo[2], tabla_simbolos, errores, opciones_op)
        if op_iz.get('tipo') != 'matriz' or op_dr.get('tipo') != 'matriz':
            errores.append({'mensaje': "El operador @ requiere dos matrices"})
            return {'tipo': 'error'}
        A = op_iz['valor']; B = op_dr['valor']
        try:
            if opciones_op.get('usar_bloque'):
                C = matmul_block(A, B, opciones_op.get('tile', 32))
            else:
                C = matmul_transpose(A, B)
            return {'tipo': 'matriz', 'tipo_elemento': C.tipo_elemento, 'filas': C.filas, 'columnas': C.columnas, 'valor': C}
        except Exception as e:
            errores.append({'mensaje': f"Error multiplicación matricial: {e}"})
            return {'tipo': 'error'}
    if nodo[0] == 'PRODUCTO_FUNC':
        a = evaluar_expr(nodo[1], tabla_simbolos, errores, opciones_op)
        b = evaluar_expr(nodo[2], tabla_simbolos, errores, opciones_op)
        return evaluar_expr(('ARROBA', nodo[1], nodo[2]), tabla_simbolos, errores, opciones_op)
    errores.append({'mensaje': f"Expresión desconocida: {nodo[0]}"})
    return {'tipo': 'error'}