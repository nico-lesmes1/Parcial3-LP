from tipos import promover_tipo

class Matriz:
    def __init__(self, filas, columnas, tipo_elemento, datos=None):
        self.filas = filas
        self.columnas = columnas
        self.tipo_elemento = tipo_elemento
        if datos is None:
            self.datos = [0] * (filas * columnas)
        else:
            if len(datos) != filas * columnas:
                raise ValueError("Longitud de datos no coincide con dimensiones")
            self.datos = list(datos)

    def get(self, i, j):
        return self.datos[i * self.columnas + j]

    def set(self, i, j, val):
        self.datos[i * self.columnas + j] = val

    def copiar(self):
        return Matriz(self.filas, self.columnas, self.tipo_elemento, list(self.datos))

    def __repr__(self):
        filas = []
        for i in range(self.filas):
            fila = [str(self.get(i, j)) for j in range(self.columnas)]
            filas.append("[" + ", ".join(fila) + "]")
        return "[" + ", ".join(filas) + "]"

def crear_matriz_ceros(filas, columnas, tipo_elemento):
    return Matriz(filas, columnas, tipo_elemento)

def matriz_desde_literal(lista_de_filas):
    if not isinstance(lista_de_filas, list) or len(lista_de_filas) == 0:
        raise ValueError("Literal de matriz vacío o inválido")
    filas = len(lista_de_filas)
    columnas = None
    tipo_elem = None
    flat = []
    for i, fila in enumerate(lista_de_filas):
        if not isinstance(fila, list):
            raise ValueError(f"Fila {i} de la matriz literal no es una lista")
        if columnas is None:
            columnas = len(fila)
            if columnas == 0:
                raise ValueError("Filas de la matriz no pueden ser vacías")
        else:
            if len(fila) != columnas:
                raise ValueError(f"Literal de matriz no rectangular: fila {i} longitud {len(fila)} != {columnas}")
        for v in fila:
            if isinstance(v, float):
                t = 'flotante'
            elif isinstance(v, int):
                t = 'entero'
            else:
                raise ValueError("Valores de matriz deben ser numéricos (int o float)")
            if tipo_elem is None:
                tipo_elem = t
            else:
                tipo_elem = promover_tipo(tipo_elem, t) or tipo_elem
            flat.append(v)
    if tipo_elem is None:
        raise ValueError("No se pudo inferir tipo de matriz")
    if tipo_elem == 'flotante':
        flat = [float(x) for x in flat]
    return Matriz(filas, columnas, tipo_elem, flat)

def transpose(m):
    datos = [0] * (m.filas * m.columnas)
    for i in range(m.filas):
        for j in range(m.columnas):
            datos[j * m.filas + i] = m.get(i, j)
    return Matriz(m.columnas, m.filas, m.tipo_elemento, datos)

def matmul_transpose(A, B):
    if A.columnas != B.filas:
        raise ValueError(f"Dimensiones incompatibles para multiplicación: cols(A)={A.columnas} != filas(B)={B.filas}")
    tipo_res = promover_tipo(A.tipo_elemento, B.tipo_elemento)
    if tipo_res is None:
        raise ValueError(f"Tipos de elemento incompatibles: {A.tipo_elemento} vs {B.tipo_elemento}")
    B_T = transpose(B)
    m = A.filas
    p = B.columnas
    n = A.columnas
    C = crear_matriz_ceros(m, p, tipo_res)
    for i in range(m):
        offA = i * A.columnas
        for j in range(p):
            offBT = j * B_T.columnas  
            s = 0
            for k in range(n):
                a = A.datos[offA + k]
                b = B_T.datos[offBT + k]
                s += a * b
            C.datos[i * p + j] = float(s) if tipo_res == 'flotante' else int(s)
    return C

def matmul_block(A, B, tile=32):
    if A.columnas != B.filas:
        raise ValueError(f"Dimensiones incompatibles para multiplicación: cols(A)={A.columnas} != filas(B)={B.filas}")
    tipo_res = promover_tipo(A.tipo_elemento, B.tipo_elemento)
    if tipo_res is None:
        raise ValueError(f"Tipos de elemento incompatibles: {A.tipo_elemento} vs {B.tipo_elemento}")
    m, n, p = A.filas, A.columnas, B.columnas
    C = crear_matriz_ceros(m, p, tipo_res)
    for ii in range(0, m, tile):
        for jj in range(0, p, tile):
            for kk in range(0, n, tile):
                i_lim = min(ii + tile, m)
                j_lim = min(jj + tile, p)
                k_lim = min(kk + tile, n)
                for i in range(ii, i_lim):
                    for k in range(kk, k_lim):
                        a = A.get(i, k)
                        baseC = i * p
                        baseB = k * p
                        for j in range(jj, j_lim):
                            C.datos[baseC + j] += a * B.datos[baseB + j]
    if tipo_res == 'entero':
        C.datos = [int(x) for x in C.datos]
    else:
        C.datos = [float(x) for x in C.datos]
    return C