import os
from lexer import tokenizar
from parser import Parser

RUTA_ENTRADA = os.path.join(os.path.dirname(__file__), 'entrada.txt')

def ejecutar_archivo(ruta=RUTA_ENTRADA, opciones_op=None):
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            texto = f.read()
    except FileNotFoundError:
        print(f"Archivo de entrada no encontrado: {ruta}")
        return
    tokens = tokenizar(texto)
    parser = Parser(tokens, opciones_op=opciones_op)
    resultado = parser.parsear_programa()
    if parser.errores:
        print("\nERRORES:")
        for e in parser.errores:
            print("-", e.get('mensaje', str(e)))
    else:
        print("\nEjecución finalizada sin errores.")
    print("\nEstado final de variables:")
    for nombre, info in parser.tabla_simbolos.items():
        if info.get('tipo') == 'escalar':
            print(f"{nombre} = {info.get('valor')} (escalar {info.get('tipo_elemento')})")
        elif info.get('tipo') == 'matriz':
            print(f"{nombre} = Matriz {info.get('filas')}x{info.get('columnas')} tipo {info.get('tipo_elemento')}")
            print(info.get('valor'))

if __name__ == '__main__':
    opciones = {'usar_bloque': False, 'tile': 32}
    ejecutar_archivo(opciones_op=opciones)