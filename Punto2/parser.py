from lexer import tokenizar, Token
from tipos import tipo_literal_desde_valor
from expresiones import evaluar_expr
from matriz import matriz_desde_literal

class Parser:
    def __init__(self, tokens, opciones_op=None):
        self.tokens = tokens
        self.pos = 0
        self.errores = []
        self.tabla_simbolos = {}  
        self.opciones_op = opciones_op or {'usar_bloque': False, 'tile': 32}

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
            raise SyntaxError(f"Se esperaba {tipo} en línea {tok.linea} col {tok.columna}, se obtuvo {tok.tipo} ({tok.valor})")
        return t

    def parsear_programa(self):
        while self.actual().tipo != 'EOF':
            if self.actual().tipo == 'PUNTO_COMA':
                self.adelantar()
                continue
            try:
                self.parsear_sentencia()
            except Exception as e:
                self.errores.append({'mensaje': f"Error parseo/ejecución: {e}"})
                while self.actual().tipo not in ('PUNTO_COMA','EOF'):
                    self.adelantar()
                if self.actual().tipo == 'PUNTO_COMA':
                    self.adelantar()
        return {'errores': self.errores, 'tabla_simbolos': self.tabla_simbolos}

    def parsear_sentencia(self):
        tok = self.actual()
        if tok.tipo == 'DECLARAR':
            self.parsear_declaracion()
            self.aceptar('PUNTO_COMA')
            return
        if tok.tipo == 'IMPRIMIR':
            self.parsear_imprimir()
            self.aceptar('PUNTO_COMA')
            return
        if tok.tipo == 'IDENT':
            if self.tokens[self.pos + 1].tipo == 'IGUAL':
                self.parsear_asignacion()
                self.aceptar('PUNTO_COMA')
                return
        expr = self.parsear_expr()
        self.aceptar('PUNTO_COMA')
        res = evaluar_expr(expr, self.tabla_simbolos, self.errores, self.opciones_op)
        return

    def parsear_declaracion(self):
        self.esperar('DECLARAR')
        id_tok = self.esperar('IDENT')
        nombre = id_tok.valor

        if self.aceptar('DOS_PUNTOS'):
            pass

        if self.aceptar('IGUAL'):
            expr = self.parsear_expr()
            res = evaluar_expr(expr, self.tabla_simbolos, self.errores, self.opciones_op)
            if res.get('tipo') in ('matriz','escalar'):
                self.tabla_simbolos[nombre] = res
            else:
                self.errores.append({'mensaje': f"Declaración {nombre}: tipo desconocido al inicializar"})
            return

        if self.actual().tipo == 'MATRIZ':
            self.adelantar()  
            self.esperar('MENOR') 
            tipo_elem_tok = self.actual()
            if tipo_elem_tok.tipo in ('ENTERO','FLOTANTE','IDENT'):
                self.adelantar()
                tipo_elem = tipo_elem_tok.valor.lower()
            else:
                self.errores.append({'mensaje': f"Tipo de elemento esperado (entero|flotante) en declaración de {nombre}", 'linea': tipo_elem_tok.linea})
                tipo_elem = 'entero'  
            self.esperar('COMA')
            n1 = self.esperar('NUMERO')
            filas = int(n1.valor)
            self.esperar('COMA')
            n2 = self.esperar('NUMERO')
            columnas = int(n2.valor)
            self.esperar('MAYOR')  
            if self.aceptar('IGUAL'):
                expr = self.parsear_expr()
                res = evaluar_expr(expr, self.tabla_simbolos, self.errores, self.opciones_op)
                if res.get('tipo') != 'matriz':
                    self.errores.append({'mensaje': f"Inicialización debe ser una matriz para {nombre}"})
                else:
                    if res['filas'] != filas or res['columnas'] != columnas:
                        self.errores.append({'mensaje': f"Inicialización dimensiones no coinciden para {nombre}: se esperaban {filas}x{columnas} y se obtuvieron {res['filas']}x{res['columnas']}"})
                    else:
                        if res['tipo_elemento'] != tipo_elem:
                            if res['tipo_elemento'] == 'entero' and tipo_elem == 'flotante':
                                res['valor'].datos = [float(x) for x in res['valor'].datos]
                                res['tipo_elemento'] = 'flotante'
                            else:
                                self.errores.append({'mensaje': f"No se puede convertir tipo {res['tipo_elemento']} a {tipo_elem} en inicialización de {nombre}"})
                        self.tabla_simbolos[nombre] = {'tipo': 'matriz', 'tipo_elemento': tipo_elem, 'filas': filas, 'columnas': columnas, 'valor': res['valor']}
                return
            else:
                from matriz import crear_matriz_ceros
                M = crear_matriz_ceros(filas, columnas, tipo_elem)
                self.tabla_simbolos[nombre] = {'tipo': 'matriz', 'tipo_elemento': tipo_elem, 'filas': filas, 'columnas': columnas, 'valor': M}
                return

        if self.actual().tipo in ('ENTERO','FLOTANTE','IDENT'):
            tipo_tok = self.adelantar()
            tipo_simple = tipo_tok.valor.lower()
            if self.aceptar('IGUAL'):
                expr = self.parsear_expr()
                res = evaluar_expr(expr, self.tabla_simbolos, self.errores, self.opciones_op)
                if res.get('tipo') == 'escalar':
                    val = res.get('valor')
                    if tipo_simple == 'entero':
                        try:
                            val = int(val)
                        except Exception:
                            self.errores.append({'mensaje': f"No se puede convertir valor a entero para {nombre}"})
                    else:
                        try:
                            val = float(val)
                        except Exception:
                            self.errores.append({'mensaje': f"No se puede convertir valor a flotante para {nombre}"})
                    self.tabla_simbolos[nombre] = {'tipo': 'escalar', 'tipo_elemento': tipo_simple, 'valor': val}
                else:
                    self.errores.append({'mensaje': f"Inicialización inválida para escalar {nombre}"})
                return
            else:
                self.errores.append({'mensaje': f"Declaración mínima sin inicialización no soportada para {nombre}"})
                return

    def parsear_imprimir(self):
        self.esperar('IMPRIMIR')
        self.esperar('PAR_ABRE')
        expr = self.parsear_expr()
        self.esperar('PAR_CIERRA')
        res = evaluar_expr(expr, self.tabla_simbolos, self.errores, self.opciones_op)
        if res.get('tipo') == 'escalar':
            print(res.get('valor'))
        elif res.get('tipo') == 'matriz':
            print("Matriz", res['filas'], "x", res['columnas'])
            print(res['valor'])
        else:
            print("Imprimir: valor inválido o error")

    def parsear_asignacion(self):
        id_tok = self.esperar('IDENT')
        nombre = id_tok.valor
        self.esperar('IGUAL')
        expr = self.parsear_expr()
        res = evaluar_expr(expr, self.tabla_simbolos, self.errores, self.opciones_op)
        if res.get('tipo') == 'error':
            return
        if nombre in self.tabla_simbolos:
            info = self.tabla_simbolos[nombre]
            if info.get('tipo') == 'matriz' and res.get('tipo') == 'matriz':
                if info['filas'] != res['filas'] or info['columnas'] != res['columnas']:
                    self.errores.append({'mensaje': f"Asignación: dimensiones no coinciden para {nombre}: {info['filas']}x{info['columnas']} vs {res['filas']}x{res['columnas']}"})
                else:
                    self.tabla_simbolos[nombre] = res
            else:
                if info.get('tipo') == res.get('tipo'):
                    self.tabla_simbolos[nombre] = res
                else:
                    self.errores.append({'mensaje': f"Asignación inválida: tipos no coinciden para {nombre}"})
        else:
            self.tabla_simbolos[nombre] = res

    def parsear_expr(self):
        return self.parsear_suma()

    def parsear_suma(self):
        nodo = self.parsear_producto()
        while self.actual().tipo in ('MAS','MENOS'):
            op_tok = self.adelantar()
            rhs = self.parsear_producto()
            nodo = ('MAS' if op_tok.tipo == 'MAS' else 'MENOS', nodo, rhs)
        return nodo

    def parsear_producto(self):
        nodo = self.parsear_factor()
        while self.actual().tipo in ('POR','DIV','ARROBA'):
            op_tok = self.adelantar()
            if op_tok.tipo == 'POR':
                rhs = self.parsear_factor()
                nodo = ('POR', nodo, rhs)
            elif op_tok.tipo == 'DIV':
                rhs = self.parsear_factor()
                nodo = ('DIV', nodo, rhs)
            else:  
                rhs = self.parsear_factor()
                nodo = ('ARROBA', nodo, rhs)
        return nodo

    def parsear_factor(self):
        tok = self.actual()
        if tok.tipo == 'PAR_ABRE':
            self.adelantar()
            expr = self.parsear_expr()
            self.esperar('PAR_CIERRA')
            return expr
        if tok.tipo == 'NUMERO':
            self.adelantar()
            return ('LIT_NUM', tok.valor)
        if tok.tipo == 'CORCH_ABRE':
            lista = self.parsear_literal_matriz()
            return ('LIT_MAT', lista)
        if tok.tipo == 'PRODUCTO':
            self.adelantar()
            self.esperar('PAR_ABRE')
            a = self.parsear_expr()
            self.esperar('COMA')
            b = self.parsear_expr()
            self.esperar('PAR_CIERRA')
            return ('PRODUCTO_FUNC', a, b)
        if tok.tipo == 'IDENT':
            self.adelantar()
            return ('REF', tok.valor)
        if tok.tipo == 'MENOS':
            self.adelantar()
            f = self.parsear_factor()
            return ('NEG', f)
        raise SyntaxError(f"Factor inesperado {tok.tipo} ({tok.valor}) en línea {tok.linea}")

    def parsear_literal_matriz(self):
        self.esperar('CORCH_ABRE')
        filas = []
        while True:
            self.esperar('CORCH_ABRE')
            fila = []
            while True:
                num_tok = self.esperar('NUMERO')
                if '.' in num_tok.valor:
                    val = float(num_tok.valor)
                else:
                    val = int(num_tok.valor)
                fila.append(val)
                if self.aceptar('COMA'):
                    continue
                else:
                    break
            self.esperar('CORCH_CIERRA')
            filas.append(fila)
            if self.aceptar('COMA'):
                continue
            else:
                break
        self.esperar('CORCH_CIERRA')
        return filas