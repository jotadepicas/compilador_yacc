"""
Universidad Nacional de La Matanza
Catedra Lenguajes y Compiladores - 2013
Mariano Francischini, Alejandro Giorgi, Roberto Bravo

TP Compilador
Basado en PLY (Python Lex-Yacc)
    http://www.dabeaz.com/ply/
    Ej: http://www.dalkescientific.com/writings/NBN/parsing_with_ply.html
"""
# coding=utf8
import ply.yacc as yacc
from lexer import Lexer, tokens
from tabla_sim import TablaSim, Simbolo
import sys

def concatena(lista):
    """
    Test. Por ahora concatena los operandos como string en vez
    de generar codigo (tercetos)
    """
    string = ""
    for item in lista[1:]:
        string += str(item)
    return string

tabla_sim = TablaSim()
tabla_sim.ambito_actual = 'main'

class Terceto():
    lista = []

    def __init__(self, *args):
        """ Crea y agrega un terceto a la lista """
        self.items = args
        self.id = len(Terceto.lista)

        Terceto.lista.append(self)
    def __str__(self):
        return "ter[%s]" % self.id

    def __repr__(self):
        """ ToString del terceto """
        items = []
        for item in self.items:
            items.append(str(item))
        return "%s: (%s)" % (self.id, ', '.join(items))

nro_regla = 0
def get_nro_regla():
    """ Contador de numero de regla 'actual'. Incrementa a medida que se crean"""
    global nro_regla
    regla = "ter[%s]" % nro_regla
    nro_regla += 1
    return regla

"""
    ###############################
    BNF y mapeo al codigo resultado
    Start Symbol: "programa"
    ###############################
"""
def p_programa(p):
    'programa : bloque_dec main'
    p[0] = Terceto(p[2])


def p_bloque_dec(p):
    ('bloque_dec : PR_DEC DOS_PUNTOS '
        'ABRE_BLOQUE '
            'declaraciones '
        'CIERRA_BLOQUE '
     'PR_ENDEC FIN_LINEA ')
    p[0] = p[4]

    if tabla_sim.ambito_actual == 'main':
        # Reseteamos ambito_actual una vez que lo usa el main para su dec.
        tabla_sim.ambito_actual = None

def p_declaraciones(p):
    'declaraciones : declaracion FIN_LINEA declaraciones'
    pass

def p_declaraciones_simple(p):
    'declaraciones : declaracion'
    pass

def p_declaracion(p):
    """
    declaracion : tipo_dato DOS_PUNTOS lista_ids
    """
    # Tabla de simbolos
    # TODO: Solo acepta la declaracion de un ID en lista_ids
    simbolo = tabla_sim.declarar_variable(tipo=p[1], lista_ids=p[3])

    p[0] = simbolo


def p_lista_ids(p):
    """
    lista_ids : ID COMA lista_ids
    """
    p[0] = Terceto(p[1], p[3])


def p_lista_ids_simple(p):
    """
    lista_ids : ID
    """
    p[0] = p[1]

def p_main(p):
    """
    main : main bloque
    main : main funcion
    """
    p[0] = Terceto(p[1], p[2])


def p_main_simple(p):
    """
    main : bloque
    main : funcion
    """
    p[0] = p[1]

def p_funcion(p):
    ('funcion : '
        'PR_DEF ID DOS_PUNTOS tipo_dato '
            'ABRE_BLOQUE '
                'bloque_dec '
                'bloque '
            'CIERRA_BLOQUE '
        'PR_RETURN expresion FIN_LINEA'
     )

    # Tabla de simbolos
    simbolo = tabla_sim.declarar_funcion(nombre=p[2])

    # Terceto: id, tipo_dato, bloque, return_expresion
    p[0] = Terceto(simbolo, p[4], p[7], p[10])

    # Termina la funcion. Reset ambito
    tabla_sim.ambito_actual = None

def p_tipo_dato(p):
    """
    tipo_dato : PR_INT
    tipo_dato : PR_FLOAT
    tipo_dato : PR_STRING
    """
    p[0] = p[1]

def p_bloque(p):
    """
    bloque : sentencia bloque
    """
    p[0] = Terceto(p[1], p[2])

def p_bloque_simple(p):
    """
    bloque : sentencia
    """
    p[0] = p[1]

def p_sentencia(p):
    """
    sentencia : asig
    sentencia : sentencia_condicional
    sentencia : sentencia_while
    sentencia : sentencia_print
    sentencia : sentencia_percent
    """
    p[0] = p[1]

def p_sentencia_sentencia(p):
    """
    sentencia : sentencia FIN_LINEA sentencia
    """
    p[0] = Terceto(p[1], p[3])

def p_sentencia_print(p):
    """
    sentencia_print : PR_PRINT ID
    """
    simbolo = tabla_sim.obtener_variable(p[2])
    p[0] = Terceto(p[1], simbolo)

def p_sentencia_while(p):
    """
    sentencia_while : PR_WHILE condicion DOS_PUNTOS ABRE_BLOQUE bloque CIERRA_BLOQUE
    """
    # (while, condicion, bloque)
    p[0] = Terceto(p[1], p[2], p[5])

def p_sentencia_condicional(p):
    'sentencia_condicional : PR_IF condicion DOS_PUNTOS ABRE_BLOQUE bloque CIERRA_BLOQUE'
    # (if, condicion, bloque)
    p[0] = Terceto(p[1], p[2], p[5])

def p_sentencia_percent(p):
    """
    sentencia_percent : PR_PERCENT factor COMA factor
    """
    # ej: (percent, expresion, expresion)
    p[0] = Terceto(p[1], p[2], p[4])

def p_asig(p):
    """
    asig : ID OP_AS expresion
    asig : ID OP_AS asig
    asig : ID OP_AS cte_string
    """
    simbolo = tabla_sim.obtener_variable(p[1])
    # (=, ID, exp)
    p[0] = Terceto(p[2], simbolo, p[3])

def p_cte_string(p):
    """ cte_string : CTE_STRING """
    p[0] = tabla_sim.declarar_cte_string(p[1])

def p_condicion(p):
    """
    condicion : expresion OP_MAYOR expresion
    condicion : expresion OP_MENOR expresion
    condicion : expresion OP_MENORIGUAL expresion
    condicion : expresion OP_DISTINTO expresion
    condicion : condicion PR_AND condicion
    condicion : condicion PR_OR condicion
    """
    # ej: (<, expresion, expresion)
    p[0] = Terceto(p[2], p[1], p[3])

def p_condicion_between(p):
    """
    condicion : factor PR_BETWEEN factor PR_AND factor
    """
    # ej: (<, expresion, expresion)
    p[0] = Terceto(p[2], p[1], p[3], p[5])

def p_expresion(p):
    """
    expresion : expresion OP_SUMA termino
    expresion : expresion OP_RESTA termino
    expresion : expresion OP_MUL termino
    expresion : expresion OP_DIV termino
    """
    # (+, exp, ter)
    p[0] = Terceto(p[2], p[1], p[3])

def p_expression_term(p):
    'expresion : termino'
    p[0] = p[1]

def p_term_factor(p):
    'termino : factor'
    p[0] = p[1]

def p_factor_parentesis(p):
    """
    factor : PAREN_ABRE expresion PAREN_CIERRA
    """
    p[0] = p[2]

def p_factor_id(p):
    """
    factor : ID
    """
    # try:
    simbolo = tabla_sim.obtener_variable(p[1])
    p[0] = simbolo
    # except TypeError:
    #    p[0] = p[1]

def p_factor_cte(p):
    """
    factor : CTE_ENT
    factor : CTE_REAL
    """
    p[0] = p[1]


# Error rule for syntax errors
def p_error(p):
    raise TypeError("Syntax error: %s" % str(p))

# Build the parser

yyparse = yacc.yacc(debug=1)
yylex = Lexer()

try:
    filename = sys.argv[1]
except:
    filename = "fuente.zz"
fuente = open(filename).read()

print '\nTokens:\n=======\n'
result = yyparse.parse(fuente, lexer=yylex)

if result is not None:
    print '\nSimbolos:\n=========\n'
    with open('simbolos.txt', 'w') as archivo:
            print tabla_sim
            archivo.write("%s\n" % tabla_sim)

    print '\nTercetos:\n=========\n'
    with open('intermedia.txt', 'w') as archivo:
        for terceto in Terceto.lista:
            print repr(terceto)
            archivo.write("%s\n" % repr(terceto))
else:
    print "\nError!!"
