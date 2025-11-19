import re

PATTERNS = [
    ('ESPACIO', r'\s+'),
    ('COMENTARIO', r'--[^\n]*'),
    ('NUMERO', r'\d+\.\d+|\d+'),
    ('DOS_PUNTOS', r':'),                 
    ('CORCH_ABRE', r'\['),
    ('CORCH_CIERRA', r'\]'),
    ('PAR_ABRE', r'\('),
    ('PAR_CIERRA', r'\)'),
    ('MENOR_IGUAL', r'<='),
    ('MAYOR_IGUAL', r'>='),
    ('DISTINTO', r'<>|!='), 
    ('MENOR', r'<'),
    ('MAYOR', r'>'),
    ('IGUAL', r'='),
    ('MAS', r'\+'),
    ('MENOS', r'-'),
    ('POR', r'\*'),
    ('DIV', r'\/'),
    ('ARROBA', r'@'),
    ('COMA', r','),
    ('PUNTO_COMA', r';'),
    ('IDENT', r'[A-Za-z_][A-Za-z0-9_]*'),
    ('CADENA', r"'([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\""),
]

PALABRAS_RESERVADAS = {
    'DECLARAR', 'COMO', 'MATRIZ', 'IMPRIMIR', 'PRODUCTO',
    'ENTERO', 'FLOTANTE', 'SI', 'SINO'
}

token_regex = re.compile('|'.join('(?P<%s>%s)' % p for p in PATTERNS), re.IGNORECASE)

class Token:
    def __init__(self, tipo, valor, linea, columna):
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.columna = columna
    def __repr__(self):
        return f"Token({self.tipo}, {self.valor!r}, {self.linea}, {self.columna})"

def tokenizar(texto):
    pos = 0
    linea = 1
    columna = 1
    tokens = []
    while pos < len(texto):
        m = token_regex.match(texto, pos)
        if not m:
            raise SyntaxError(f"Error léxico en línea {linea} columna {columna}: {texto[pos]!r}")
        tipo = m.lastgroup
        valor = m.group(tipo)
        if tipo == 'ESPACIO':
            nueva_lineas = valor.count('\n')
            if nueva_lineas:
                linea += nueva_lineas
                columna = len(valor) - valor.rfind('\n')
            else:
                columna += len(valor)
            pos = m.end()
            continue
        if tipo == 'COMENTARIO':
            nueva_lineas = valor.count('\n')
            if nueva_lineas:
                linea += nueva_lineas
                columna = 1
            else:
                columna += len(valor)
            pos = m.end()
            continue
        if tipo == 'IDENT':
            val_upper = valor.upper()
            if val_upper in PALABRAS_RESERVADAS:
                tipo = val_upper
                valor = val_upper
        tokens.append(Token(tipo, valor, linea, columna))
        advance = len(valor)
        pos = m.end()
        columna += advance
    tokens.append(Token('EOF', '', linea, columna))
    return tokens

__all__ = ['tokenizar', 'Token', 'PALABRAS_RESERVADAS']