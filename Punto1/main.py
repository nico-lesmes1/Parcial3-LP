import os

RUTA_ENTRADA = os.path.join(os.path.dirname(__file__), 'entrada.txt')

def ejecutar_archivo_entrada(ruta=RUTA_ENTRADA):
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            texto = f.read()
    except FileNotFoundError:
        print(f"Archivo de entrada no encontrado: {ruta}")
        return
    except Exception as e:
        print(f"Error leyendo {ruta}: {e}")
        return

    try:
        from lexer import tokenizar
    except Exception as e:
        print("Error lexer.py:", e)
        try:
            import importlib, inspect
            m = importlib.import_module('lexer')
            print("Módulo lexer cargado desde:", getattr(m, '__file__', 'desconocido'))
            if not hasattr(m, 'tokenizar'):
                print("Verifica lexer.py")
        except Exception:
            pass
        return

    try:
        from base_datos import BaseDatosMemoria
        from parser import Parser
    except Exception as e:
        print("Error", e)
        return

    # tokenizar y parsear
    try:
        tokens = tokenizar(texto)
    except Exception as e:
        print("Error tokenización:", e)
        return

    bd = BaseDatosMemoria()
    parser = Parser(tokens, bd)
    try:
        resultados = parser.parsear_programa()
    except Exception as e:
        print("Error parseo/ejecución:", e)
        return

    if parser.errores:
        print("\nERRORES ENCONTRADOS:")
        for e in parser.errores:
            print("-", e.get('mensaje', str(e)))
    else:
        print("\nEjecución completada sin errores.")
    return resultados

if __name__ == '__main__':
    ejecutar_archivo_entrada()