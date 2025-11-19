from lexer import tokenizar, Token
from tipos import tipo_literal_desde_valor, TIPOS_VALIDOS
from base_datos import BaseDatosMemoria
from expresiones import evaluar_expr_con_contexto, evaluar_expr_sin_contexto

class Parser:
    def __init__(self, tokens, base_datos):
        self.tokens = tokens
        self.pos = 0
        self.base_datos = base_datos
        self.errores = []

    def actual(self):
        return self.tokens[self.pos]

    def adelantar(self):
        self.pos += 1
        return self.tokens[self.pos - 1]

    def aceptar(self, tipo):
        if self.actual().tipo == tipo:
            return self.adelantar()
        return None

    def esperar(self, tipo):
        t = self.aceptar(tipo)
        if t is None:
            tok = self.actual()
            raise SyntaxError(f"Se esperaba {tipo} en linea {tok.linea} col {tok.columna}, se obtuvo {tok.tipo} ({tok.valor})")
        return t

    def parsear_programa(self):
        resultados = []
        while self.actual().tipo != 'EOF':
            if self.actual().tipo == 'PUNTO_COMA':
                self.adelantar()
                continue
            res = self.parsear_sentencia()
            resultados.append(res)
            if self.aceptar('PUNTO_COMA'):
                pass
        return resultados

    def parsear_sentencia(self):
        tok = self.actual()
        if tok.tipo == 'SELECT':
            return self.parsear_select()
        if tok.tipo == 'INSERT':
            return self.parsear_insert()
        if tok.tipo == 'UPDATE':
            return self.parsear_update()
        if tok.tipo == 'DELETE':
            return self.parsear_delete()
        if tok.tipo == 'CREATE':
            return self.parsear_create()
        raise SyntaxError(f"Sentencia desconocida en linea {tok.linea} col {tok.columna}: {tok.valor}")

    def parsear_create(self):
        self.esperar('CREATE')
        self.esperar('TABLE')
        id_tok = self.esperar('IDENT')
        nombre_tabla = id_tok.valor
        self.esperar('PAR_ABRE')
        columnas = {}
        first = True
        while True:
            if not first:
                self.esperar('COMA')
            first = False
            col_tok = self.esperar('IDENT')
            nombre_col = col_tok.valor
            tipo_tok = self.esperar('IDENT')
            tipo_col = tipo_tok.valor.lower()
            if tipo_col not in TIPOS_VALIDOS:
                self.errores.append({'mensaje': f"Tipo desconocido {tipo_col} para columna {nombre_col}", 'linea': tipo_tok.linea})
            columnas[nombre_col] = tipo_col
            if self.aceptar('PAR_CIERRA'):
                break
        try:
            self.base_datos.crear_tabla(nombre_tabla, columnas.items())
        except Exception as e:
            self.errores.append({'mensaje': str(e), 'linea': id_tok.linea})
        return {'tipo_sentencia': 'CREATE', 'tabla': nombre_tabla, 'columnas': columnas}

    def parsear_insert(self):
        self.esperar('INSERT')
        self.esperar('INTO')
        id_tok = self.esperar('IDENT')
        nombre_tabla = id_tok.valor
        self.esperar('PAR_ABRE')
        columnas = []
        first = True
        while True:
            if not first:
                self.esperar('COMA')
            first = False
            col_tok = self.esperar('IDENT')
            columnas.append(col_tok.valor)
            if self.aceptar('PAR_CIERRA'):
                break
        self.esperar('VALUES')
        self.esperar('PAR_ABRE')
        valores = []
        first = True
        while True:
            if not first:
                self.esperar('COMA')
            first = False
            expr = self.parsear_expr()
            valores.append(expr)
            if self.aceptar('PAR_CIERRA'):
                break
        if nombre_tabla not in self.base_datos.tablas:
            self.errores.append({'mensaje': f"Tabla {nombre_tabla} no existe", 'linea': id_tok.linea})
            return {'tipo_sentencia': 'INSERT', 'tabla': nombre_tabla, 'columnas': columnas, 'valores': valores}
        esquema = self.base_datos.tablas[nombre_tabla]['columnas']
        if len(columnas) != len(valores):
            self.errores.append({'mensaje': f"INSERT: número de columnas y valores no coincide para {nombre_tabla}", 'linea': id_tok.linea})
        fila = {}
        for i, col in enumerate(columnas):
            if col not in esquema:
                self.errores.append({'mensaje': f"INSERT: columna {col} no existe en {nombre_tabla}", 'linea': id_tok.linea})
                continue
            tipo_col = esquema[col]
            tipo_val, valor = evaluar_expr_sin_contexto(valores[i])
            if tipo_val != tipo_col:
                if tipo_val == 'entero' and tipo_col == 'flotante':
                    valor = float(valor)
                    tipo_val = 'flotante'
                elif tipo_val == 'flotante' and tipo_col == 'entero':
                    valor = int(valor)
                    tipo_val = 'entero'
                elif tipo_col == 'cadena':
                    valor = str(valor)
                    tipo_val = 'cadena'
                else:
                    pass
            fila[col] = valor
        try:
            self.base_datos.insertar(nombre_tabla, fila)
        except Exception as e:
            self.errores.append({'mensaje': str(e), 'linea': id_tok.linea})
        return {'tipo_sentencia': 'INSERT', 'tabla': nombre_tabla, 'columnas': columnas, 'valores': valores}

    def parsear_update(self):
        self.esperar('UPDATE')
        id_tok = self.esperar('IDENT')
        nombre_tabla = id_tok.valor
        self.esperar('SET')
        asignaciones = {}
        first = True
        while True:
            if not first:
                if not self.aceptar('COMA'):
                    break
            first = False
            col_tok = self.esperar('IDENT')
            col_name = col_tok.valor
            self.esperar('IGUAL')
            expr = self.parsear_expr()
            asignaciones[col_name] = expr
        condicion = None
        if self.aceptar('WHERE'):
            condicion = self.parsear_expr()
        if nombre_tabla not in self.base_datos.tablas:
            self.errores.append({'mensaje': f"UPDATE: tabla {nombre_tabla} no existe", 'linea': id_tok.linea})
            return {'tipo_sentencia': 'UPDATE', 'tabla': nombre_tabla, 'asignaciones': asignaciones, 'where': condicion}
        esquema = self.base_datos.tablas[nombre_tabla]['columnas']
        for col in asignaciones.keys():
            if col not in esquema:
                self.errores.append({'mensaje': f"UPDATE: columna {col} no existe en {nombre_tabla}", 'linea': id_tok.linea})
        def condicion_fn(registro):
            if condicion is None:
                return True
            tipo_c, val = evaluar_expr_con_contexto(condicion, {None: registro}, esquema)
            if tipo_c != 'booleano':
                return bool(val)
            return bool(val)
        asign_fns = {}
        for col, expr in asignaciones.items():
            def make_fn(e):
                return lambda reg, e=e: evaluar_expr_con_contexto(e, {None: reg}, esquema)[1]
            asign_fns[col] = make_fn(expr)
        conteo = self.base_datos.actualizar(nombre_tabla, condicion_fn, asign_fns)
        return {'tipo_sentencia': 'UPDATE', 'tabla': nombre_tabla, 'afectadas': conteo}

    def parsear_delete(self):
        self.esperar('DELETE')
        self.esperar('FROM')
        id_tok = self.esperar('IDENT')
        nombre_tabla = id_tok.valor
        condicion = None
        if self.aceptar('WHERE'):
            condicion = self.parsear_expr()
        if nombre_tabla not in self.base_datos.tablas:
            self.errores.append({'mensaje': f"DELETE: tabla {nombre_tabla} no existe", 'linea': id_tok.linea})
            return {'tipo_sentencia': 'DELETE', 'tabla': nombre_tabla, 'where': condicion}
        def condicion_fn(registro):
            if condicion is None:
                return True
            tipo_c, val = evaluar_expr_con_contexto(condicion, {None: registro}, self.base_datos.tablas[nombre_tabla]['columnas'])
            if tipo_c != 'booleano':
                return bool(val)
            return bool(val)
        borrados = self.base_datos.borrar(nombre_tabla, condicion_fn)
        return {'tipo_sentencia': 'DELETE', 'tabla': nombre_tabla, 'borrados': borrados}

    def parsear_select(self):
        self.esperar('SELECT')
        lista_campos = []
        if self.aceptar('AST'):  # '*'
            lista_campos.append({'tipo': 'STAR'})
        else:
            while True:
                tok_campo = self.esperar('IDENT')
                nombre = tok_campo.valor
                if self.aceptar('PUNTO'):
                    col_tok = self.esperar('IDENT')
                    campo = {'tipo': 'CAMPO', 'tabla_o_alias': nombre, 'columna': col_tok.valor, 'linea': tok_campo.linea}
                else:
                    campo = {'tipo': 'CAMPO', 'tabla_o_alias': None, 'columna': nombre, 'linea': tok_campo.linea}
                if self.aceptar('AS'):
                    alias_tok = self.esperar('IDENT')
                    campo['alias'] = alias_tok.valor
                lista_campos.append(campo)
                if not self.aceptar('COMA'):
                    break
        self.esperar('FROM')
        lista_tablas = []
        while True:
            tbl_tok = self.esperar('IDENT')
            nombre_tabla = tbl_tok.valor
            alias = None
            if self.aceptar('AS'):
                alias_tok = self.esperar('IDENT')
                alias = alias_tok.valor
            else:
                nxt = self.tokens[self.pos]
                if nxt.tipo not in ('COMA', 'PUNTO_COMA', 'WHERE', 'EOF'):
                    alias = self.adelantar().valor
            lista_tablas.append((nombre_tabla, alias or nombre_tabla))
            if not self.aceptar('COMA'):
                break
        columnas_disponibles = {}
        for nombre_tabla, alias in lista_tablas:
            if nombre_tabla not in self.base_datos.tablas:
                self.errores.append({'mensaje': f"SELECT: tabla {nombre_tabla} no existe", 'linea': tbl_tok.linea})
                continue
            esquema = self.base_datos.tablas[nombre_tabla]['columnas']
            for col, tipo in esquema.items():
                if col not in columnas_disponibles:
                    columnas_disponibles[col] = []
                columnas_disponibles[col].append({'alias': alias, 'tabla': nombre_tabla, 'tipo': tipo})
        condicion = None
        if self.aceptar('WHERE'):
            condicion = self.parsear_expr()
        resultado_schema = []
        def resolver_campo(campo):
            if campo['tipo'] == 'STAR':
                expansiones = []
                for nombre_tabla, alias in lista_tablas:
                    esquema = self.base_datos.tablas.get(nombre_tabla, {}).get('columnas', {})
                    for col, tipo in esquema.items():
                        nombre_salida = f"{alias}.{col}"
                        expansiones.append({'alias': alias, 'tabla': nombre_tabla, 'columna': col, 'tipo': tipo, 'nombre_salida': nombre_salida})
                return expansiones
            col = campo['columna']
            if campo['tabla_o_alias'] is not None:
                alias = campo['tabla_o_alias']
                for nombre_tabla, al in lista_tablas:
                    if al == alias:
                        esquema = self.base_datos.tablas.get(nombre_tabla, {}).get('columnas', {})
                        if col not in esquema:
                            self.errores.append({'mensaje': f"Columna {col} no existe en tabla {nombre_tabla} (alias {alias})", 'linea': campo.get('linea')})
                            return []
                        nombre_salida = campo.get('alias', col)
                        return [{'alias': alias, 'tabla': nombre_tabla, 'columna': col, 'tipo': esquema[col], 'nombre_salida': nombre_salida}]
                self.errores.append({'mensaje': f"Alias o tabla {alias} no encontrada en FROM", 'linea': campo.get('linea')})
                return []
            else:
                entradas = columnas_disponibles.get(col, [])
                if len(entradas) == 0:
                    self.errores.append({'mensaje': f"Columna {col} no encontrada en FROM", 'linea': campo.get('linea')})
                    return []
                if len(entradas) > 1:
                    self.errores.append({'mensaje': f"Columna {col} es ambigua en FROM; use alias", 'linea': campo.get('linea')})
                    return []
                entrada = entradas[0]
                nombre_salida = campo.get('alias', col)
                return [{'alias': entrada['alias'], 'tabla': entrada['tabla'], 'columna': col, 'tipo': entrada['tipo'], 'nombre_salida': nombre_salida}]
        proyecciones = []
        for campo in lista_campos:
            expans = resolver_campo(campo)
            for e in expans:
                resultado_schema.append((e['nombre_salida'], e['tipo']))
                proyecciones.append(e)
        def funcion_ejecucion():
            tablas_registros = []
            for nombre_tabla, alias in lista_tablas:
                if nombre_tabla not in self.base_datos.tablas:
                    tablas_registros.append((alias, []))
                else:
                    tablas_registros.append((alias, self.base_datos.tablas[nombre_tabla]['registros']))
            resultados = []
            def combinar(i, contexto):
                if i >= len(tablas_registros):
                    if condicion is not None:
                        tipo_c, val = evaluar_expr_con_contexto(condicion, contexto, None)
                        if tipo_c != 'booleano':
                            if not val:
                                return
                        else:
                            if not val:
                                return
                    fila = {}
                    for p in proyecciones:
                        alias = p['alias']
                        col = p['columna']
                        nombre_salida = p['nombre_salida']
                        valor = None
                        if alias in contexto:
                            valor = contexto[alias].get(col)
                        fila[nombre_salida] = valor
                    resultados.append(fila)
                    return
                alias, registros = tablas_registros[i]
                if len(registros) == 0:
                    return
                for reg in registros:
                    contexto[alias] = reg
                    combinar(i+1, contexto)
                contexto.pop(alias, None)
            combinar(0, {})
            return resultados
        filas = funcion_ejecucion()
        print("RESULTADO SELECT:")
        if resultado_schema:
            cabeceras = [c[0] for c in resultado_schema]
            print("\t".join(cabeceras))
            for f in filas:
                vals = [str(f.get(c, 'NULL')) for c in cabeceras]
                print("\t".join(vals))
        else:
            print("No hay columnas en proyección")
        return {'tipo_sentencia': 'SELECT', 'schema': resultado_schema, 'filas': filas}

    def parsear_expr(self):
        return self.parsear_or()

    def parsear_or(self):
        nodo = self.parsear_and()
        while self.actual().tipo == 'OR':
            self.adelantar()
            rhs = self.parsear_and()
            nodo = ('OR', nodo, rhs)
        return nodo

    def parsear_and(self):
        nodo = self.parsear_not()
        while self.actual().tipo == 'AND':
            self.adelantar()
            rhs = self.parsear_not()
            nodo = ('AND', nodo, rhs)
        return nodo

    def parsear_not(self):
        if self.actual().tipo == 'NOT':
            self.adelantar()
            expr = self.parsear_not()
            return ('NOT', expr)
        return self.parsear_comparacion()

    def parsear_comparacion(self):
        nodo = self.parsear_suma()
        while self.actual().tipo in ('IGUAL','MENOR','MAYOR','MENOR_IGUAL','MAYOR_IGUAL','DISTINTO'):
            op = self.adelantar().tipo
            rhs = self.parsear_suma()
            nodo = (op, nodo, rhs)
        return nodo

    def parsear_suma(self):
        nodo = self.parsear_producto()
        while self.actual().tipo in ('MAS','MENOS'):
            op = self.adelantar().tipo
            rhs = self.parsear_producto()
            nodo = (op, nodo, rhs)
        return nodo

    def parsear_producto(self):
        nodo = self.parsear_factor()
        while self.actual().tipo in ('POR','DIV'):
            op = self.adelantar().tipo
            rhs = self.parsear_factor()
            nodo = (op, nodo, rhs)
        return nodo

    def parsear_factor(self):
        tok = self.actual()
        if tok.tipo == 'PAR_ABRE':
            self.adelantar()
            expr = self.parsear_expr()
            self.esperar('PAR_CIERRA')
            return expr
        if tok.tipo in ('NUMERO','CADENA','TRUE','FALSE'):
            self.adelantar()
            return ('LIT', tok.valor)
        if tok.tipo == 'IDENT':
            id1 = self.adelantar().valor
            if self.aceptar('PUNTO'):
                col_tok = self.esperar('IDENT')
                return ('REF', id1, col_tok.valor)
            else:
                return ('REF', None, id1)
        if tok.tipo == 'MENOS':
            self.adelantar()
            factor = self.parsear_factor()
            return ('NEG', factor)
        raise SyntaxError(f"Factor inesperado {tok.tipo} ({tok.valor}) en linea {tok.linea}")