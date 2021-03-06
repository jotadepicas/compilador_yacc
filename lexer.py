"""
Universidad Nacional de La Matanza
Catedra Lenguajes y Compiladores - 2013
Mariano Francischini, Alejandro Giorgi, Roberto Bravo

TP Compilador - Analizador Lexico
"""
# coding=utf8
import re
from ctypes import c_float
tokens = [
   'ID',
   'OP_AS',
   'OP_SUMA',
   'PR_WHILE',
   'OP_DISTINTO',
   'CTE_ENT',
   'CTE_REAL',
   'CTE_STRING',
   'FIN_LINEA',
   'ABRE_BLOQUE',
   'CIERRA_BLOQUE',
   'PR_IF',
   'PR_ELSE',
   'DOS_PUNTOS',
   'OP_MAYOR',
   'OP_MAYORIGUAL',
   'OP_MENOR',
   'OP_MENORIGUAL',
   'OP_MUL',
   'OP_DIV',
   'OP_RESTA',
   'OP_IGUALDAD',
   'OP_RESTO',
   'PR_AND',
   'PR_OR',
   'PR_INT',
   'PR_FLOAT',
   'PR_DEC',
   'PR_ENDEC',
   'PR_DEF',
   'PR_RETURN',
   'PR_STRING',
   'PR_TECLA',
   'PR_BREAK',
   'PR_STDIN',
   'PR_CONTINUE',
   'PAREN_ABRE',
   'PAREN_CIERRA',
   'COMA',
   'PR_PRINT',
   'PR_PRINTC',
   'PR_PRINTNL',
   'PR_BETWEEN',
   'PR_PERCENT',
]

class Token(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value
        self.lineno = None
        self.lexpos = None
    def __repr__(self):
        return "<Token: %s, %s>" % (self.type, self.value.strip("\n"))

class Val(object):
    """ Reg Exps """
    CUALQUIER = "."

    """ Estados automata """
    E_FINAL = "F"
    E_FIN_LINEA = "2"

    """ Cotas """
    MAX_CTE_STRING = 120
    MIN_CTE_ENT = -32768
    MAX_CTE_ENT = 32767
    MAX_TAM_ID = 25

class Lexer(object):
    """
    YYLEX
    Analizador Lexico.
    Automata finito de Terminales
    """
    def __init__(self):
        self.nivel_bloques = [0]  # Nivel de tab del bloque actual
        self.nivel_espacios_sentencia = 0  # Nivel de tab de la sentencia actual

        """Cuando se descubren varios tokens juntos se los envia \
           a esta cola para irlos devolviendo en sucesivas llamadas
        """
        self.cola_tokens = []

        from automata import matriz
        self.matriz = matriz

    def input(self, text):
        """ Metodo requerido por yyparse """
        # Se apendea una marca de finde de fuente
        self.text = text.strip('\n ') + "\x00"
        self.generate = self.generator()

    def iterar_estado(self, estado_actual, input_char):
        for (simbolo, accion) in estado_actual.items():
            if accion[0] == Val.E_FINAL:
                self.estado = "0"
                accion[3](self, simbolo)
                return Token(type=accion[1], value=self.cadena[0:-1])
            elif re.match(simbolo, input_char) is not None:
                if accion[2] and re.match(accion[2], input_char):
                    continue  # es un excepto, entonces continue
                resultado = accion[3](self, simbolo)
                if resultado is not None:
                    self.estado = "0"
                    return resultado
                self.estado = accion[0]
                return "NEXT"  # Se pide el proximo caracter

        # Fin de archivo
        # Revisamos si es necesario cerrar bloques abiertos
        tokens = []
        if len(self.nivel_bloques) > 1:
            for _ in self.nivel_bloques[1:]:  # se ignora el primero (nivel 0)
                token = Token(type="CIERRA_BLOQUE", value="}\n")
                tokens.append(token)
        fin_archivo = Token(type="$end", value="")
        tokens.append(fin_archivo)
        return tokens  # Devolvemos todos los cierres juntos + fin de archivo


    def generator(self):
        """
            Automata
        """
        self.estado = "0"  # estado actual del automata. Inicial: cero
        self.cadena = ""  # Cadena que se acumula a medida que entran caracteres

        i = 0
        while i < len(self.text):
            """ Primero nos fijamos si hay tokens encolados"""
            if len(self.cola_tokens):
                yield self.cola_tokens.pop()
                continue

            """ 
                Itera caracter por caracter 
            """
            input_char = self.text[i]

            if self.estado == '0' and input_char == ' ':
                """ Ignormos espacios como inicio de un token """
                i += 1
                continue

            if input_char == '\r':
                """ Se ignoran completamente esos caracteres """
                i += 1
                continue
            self.cadena += input_char
            estado_actual = self.matriz[self.estado]

            """ Avanza por la matriz de estados """
            token = self.iterar_estado(estado_actual, input_char)
            if token == "NEXT":
                """ Cuando se necesita consumir mas 
                    input_char para determinar el token 
                """
                i += 1
                continue
            elif token == "IGNORE":
                """ Por ej los comentarios"""
                self.cadena = ""
                continue
            elif token == "ENCOLADOS":
                """ Por ej cuando se encuentran 
                    varios CIERRA_BLOQUE juntos 
                """
                self.cadena = ""
                continue
            elif isinstance(token, Token) and token.type == 'ID':
                ### Cotas de ID ####
                if len(token.value) > Val.MAX_TAM_ID:
                    raise TypeError("ID supera cota maxima (%s): %s"
                                    % (Val.MAX_TAM_ID, token.value))
                """
                    #######################
                    Palabras reservadas PR_
                    #######################
                """
                if token.value == 'if':
                    token = Token(type="PR_IF", value="if")
                elif token.value == 'while':
                    token = Token(type="PR_WHILE", value="while")
                elif token.value == 'int':
                    token = Token(type="PR_INT", value="int")
                elif token.value == 'float':
                    token = Token(type="PR_FLOAT", value="float")
                elif token.value == 'dec':
                    token = Token(type="PR_DEC", value="dec")
                elif token.value == 'endec':
                    token = Token(type="PR_ENDEC", value="endec")
                elif token.value == 'def':
                    token = Token(type="PR_DEF", value="def")
                elif token.value == 'return':
                    token = Token(type="PR_RETURN", value="return")
                elif token.value == 'string':
                    token = Token(type="PR_STRING", value="string")
                elif token.value == 'print':
                    token = Token(type="PR_PRINT", value="print")
                elif token.value == 'between':
                    token = Token(type="PR_BETWEEN", value="between")
                elif token.value == 'percent':
                    token = Token(type="PR_PERCENT", value="percent")
                elif token.value == 'else':
                    token = Token(type="PR_ELSE", value="else")
                elif token.value == 'tecla':
                    token = Token(type="PR_TECLA", value="tecla")
                elif token.value == 'break':
                    token = Token(type="PR_BREAK", value="break")
                elif token.value == 'printc':
                    token = Token(type="PR_PRINTC", value="printc")
                elif token.value == 'stdin':
                    token = Token(type="PR_STDIN", value="stdin")
                elif token.value == 'printnl':
                    token = Token(type="PR_PRINTNL", value="printnl")
                elif token.value == 'continue':
                    token = Token(type="PR_CONTINUE", value="continue")

            self.cadena = ""
            # retorno del/de los token/s
            if isinstance(token, list):
                for tk in token:
                    yield tk
            else:
                yield token


    def token(self):
        try:
            token = self.generate.next()
            print token
            return token
        except StopIteration:
            return None

    """
        Metodos de acciones ejecutadas en cada estado del automata
    """
    def acc_NADA(self, simbolo):
        pass

    def acc_RESET_NIVEL_SENTENCIA(self, simbolo):
        self.nivel_espacios_sentencia = 0

    ##########################################################
    # Cotas
    def acc_CTE_STRING(self, simbolo):
        # Ignoramos las comillas de abrir y cerrar
        self.cadena = self.cadena[1:-1]
        if len(self.cadena) > Val.MAX_CTE_STRING:
            raise TypeError("CTE_STRING muy larga. Limite %s, largo: %s" % (Val.MAX_CTE_STRING, len(self.cadena)))
    def acc_CTE_ENT(self, simbolo):
        entero = int(self.cadena[:-1])
        if entero > Val.MAX_CTE_ENT or entero < Val.MIN_CTE_ENT:
            raise TypeError("CTE_ENT fuera de rango: %s a %s" % (Val.MAX_CTE_ENT, Val.MIN_CTE_ENT))
    def acc_CTE_REAL(self, simbolo):
        real = float(self.cadena[:-1])
        # Validacion verdadera contra un flotante de C.
        if str(c_float(real).value) == 'inf':
            raise TypeError("CTE_REAL %s fuera de rango: " % real)
    ##########################################################

    def acc_FIN_LINEA(self, simbolo):
        if simbolo == " ":  # Bloque (tab)
            self.nivel_espacios_sentencia += 1
        else:
            # [-1] es el ultimo elemento de la lista
            if self.nivel_bloques[-1] < self.nivel_espacios_sentencia:
                self.nivel_bloques.append(self.nivel_espacios_sentencia),
                token = Token(type="ABRE_BLOQUE", value=" {\n")
            elif self.nivel_bloques[-1] > self.nivel_espacios_sentencia:
                bloque = self.nivel_bloques.pop()
                while bloque != self.nivel_espacios_sentencia:
                    token = Token(type="CIERRA_BLOQUE", value="}\n")
                    self.cola_tokens.append(token)
                    bloque = self.nivel_bloques.pop()
                    """ Si consumio todos, agregamos el nivel 0"""
                self.nivel_bloques.append(bloque)  # Agrego el ultimo bloque
                return "ENCOLADOS"
            else:
                token = Token(type="FIN_LINEA", value="\n")  # Se ignoran los epacios de tabulacion
                                                            # si no cambian el bloque
            self.nivel_espacios_sentencia = 0  # Reset nivel
            return token
        return None
    def acc_COMENTARIO(self, simbolo):
        return "IGNORE"
