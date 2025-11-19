class BaseDatosMemoria:
    def __init__(self):
        self.tablas = {}

    def crear_tabla(self, nombre, columnas):
        if nombre in self.tablas:
            raise RuntimeError(f"Ya existe la tabla {nombre}")
        self.tablas[nombre] = {'columnas': dict(columnas), 'registros': []}

    def insertar(self, nombre, fila):
        if nombre not in self.tablas:
            raise RuntimeError(f"Tabla {nombre} no existe")
        esquema = self.tablas[nombre]['columnas']
        for col in fila.keys():
            if col not in esquema:
                raise RuntimeError(f"Columna {col} no existe en tabla {nombre}")
        self.tablas[nombre]['registros'].append(dict(fila))

    def actualizar(self, nombre, condicion_fn, asignaciones):
        if nombre not in self.tablas:
            raise RuntimeError(f"Tabla {nombre} no existe")
        conteo = 0
        for registro in self.tablas[nombre]['registros']:
            if condicion_fn(registro):
                for col, valor_fn in asignaciones.items():
                    registro[col] = valor_fn(registro)
                conteo += 1
        return conteo

    def borrar(self, nombre, condicion_fn):
        if nombre not in self.tablas:
            raise RuntimeError(f"Tabla {nombre} no existe")
        nuevos = []
        borrados = 0
        for registro in self.tablas[nombre]['registros']:
            if condicion_fn(registro):
                borrados += 1
            else:
                nuevos.append(registro)
        self.tablas[nombre]['registros'] = nuevos
        return borrados