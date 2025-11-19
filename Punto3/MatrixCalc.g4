grammar MatrixCalc;

programa
    : sentencia* EOF
    ;

sentencia
    : declaracion PUNTO_COMA?
    | asignacion PUNTO_COMA?
    | imprimir PUNTO_COMA?
    | expr PUNTO_COMA?
    ;

declaracion
    : DECLARAR IDENT ( DOS_PUNTOS tipo_anotacion ( IGUAL expr )? | IGUAL expr )?
    ;

tipo_elemento
    : ENTERO
    | FLOTANTE
    ;

tipo_anotacion
    : MATRIZ MENOR tipo_elemento COMA NUMERO COMA NUMERO MAYOR
    | ENTERO
    | FLOTANTE
    ;

asignacion
    : IDENT IGUAL expr
    ;

imprimir
    : IMPRIMIR PAR_ABRE expr PAR_CIERRA
    ;

expr
    : expr_suma
    ;

expr_suma
    : expr_prod ( (MAS | MENOS) expr_prod )*
    ;

expr_prod
    : expr_factor ( (POR | DIV | ARROBA) expr_factor )*
    ;

expr_factor
    : MENOS expr_factor                          #unariaNeg
    | NUMERO                                     #literalNumero
    | literal_matriz                             #literalMatriz
    | PRODUCTO PAR_ABRE expr COMA expr PAR_CIERRA #funcProducto
    | IDENT                                      #referencia
    | PAR_ABRE expr PAR_CIERRA                   #parenExpr
    ;

/* literal de matriz: [[1,2],[3,4]] */
literal_matriz
    : CORCH_ABRE fila ( COMA fila )* CORCH_CIERRA
    ;

fila
    : CORCH_ABRE NUMERO ( COMA NUMERO )* CORCH_CIERRA
    ;


DECLARAR : [dD][eE][cC][lL][aA][rR][aA][rR] ;
MATRIZ  : [mM][aA][tT][rR][iI][zZ] ;
IMPRIMIR: [iI][mM][pP][rR][iI][mM][iI][rR] ;
PRODUCTO: [pP][rR][oO][dD][uU][cC][tT][oO] ;
ENTERO  : [eE][nN][tT][eE][rR][oO] ;
FLOTANTE: [fF][lL][oO][tT][aA][nN][tT][eE] ;

PUNTO_COMA : ';' ;
COMA       : ',' ;
DOS_PUNTOS : ':' ;
PAR_ABRE   : '(' ;
PAR_CIERRA : ')' ;
CORCH_ABRE : '[' ;
CORCH_CIERRA: ']' ;
MENOR      : '<' ;
MAYOR      : '>' ;
IGUAL      : '=' ;
ARROBA     : '@' ;
MAS        : '+' ;
MENOS      : '-' ;
POR        : '*' ;
DIV        : '/' ;

NUMERO : DIGITO+ ('.' DIGITO+)? ;

IDENT : [A-Za-z_][A-Za-z0-9_]* ;

COMMENT : '--' ~[\r\n]* -> skip ;
WS      : [ \t\r\n]+ -> skip ;

fragment DIGITO : [0-9] ;