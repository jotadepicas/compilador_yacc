from os import system
from collections import OrderedDict
from tabla_sim import Simbolo
from asm_template import Asm

class TraductorAsm:
    id_etiqueta = 0

    def __init__(self, tercetos, tabla_sim):
        self.tercetos = tercetos
        self.tabla_sim = tabla_sim
        self.asm = Asm.base

    def traducir(self, filename):
        """ Traduce la notacion intermedia a texto assembler """

        # declaraciones de tabla de simbolos
        self.declaraciones_main()

        self.asm_terceto = OrderedDict()

        for terceto in self.tercetos:
            if terceto.tipo == "programa":
                asm = self.asm_terceto[terceto.items[0].id]
                # Print hola mundo
                # asm = asm + "\n" + Asm.print_.replace("%string", "str")
                # asm = asm.replace("%len", "str_len")
                self.asm = self.asm.replace('%_start', asm)
            elif terceto.tipo == "condicion":
                asm = ""
                if terceto.items[0] in ["<", "<=", ">", ">="]:
                    izq = self.representar_operando(terceto.items[1])
                    der = self.representar_operando(terceto.items[2])
                    asm = "cmp %s, %s" % (izq, der)
                self.asm_terceto[terceto.id] = asm
            elif terceto.tipo == "while":
                pass
            elif terceto.tipo == "if":
                condicion = terceto.items[0]
                tipo_condicion = condicion.items[0]
                bloque = self.asm_terceto[terceto.items[1].id]
                if tipo_condicion == '&':
                    # condicion compleja: a > b & b < c
                    izq = condicion.items[1]
                    der = condicion.items[2]

                    asm_condicion = self.obtener_asm_condicion_and_or(condicion_izq=izq, condicion_der=der)

                    asm = Asm.if_and_or
                    asm = asm.replace("%condicion_and_or", asm_condicion)
                    asm = asm.replace('%etiqueta_end', self.inventar_etiqueta(prefijo='ENDIF'))
                else:
                    # condicion simple: a > b
                    asm_tipo = self.obtener_jump(tipo_condicion)
                    asm_condicion = Asm.condicion_simple
                    asm_condicion = asm_condicion.replace('%condicion', self.asm_terceto[terceto.items[0].id])
                    asm_condicion = asm_condicion.replace('%tipo_condicion', asm_tipo)
                    asm = Asm.if_
                    asm = asm.replace('%condicion_simple', asm_condicion)
                    asm = asm.replace('%etiqueta_end', self.inventar_etiqueta(prefijo='ENDIF'))


                asm = asm.replace('%bloque', bloque)
                self.asm_terceto[terceto.id] = asm
            elif terceto.tipo == "bloque":
                asm = ""
                for item in terceto.items:
                    asm = asm + self.asm_terceto[item.id]
                self.asm_terceto[terceto.id] = asm
            elif terceto.tipo == "expresion":
                asm = ""
                if terceto.items[0] == '+':
                    sumando1 = self.representar_operando(terceto.items[1])
                    sumando2 = self.representar_operando(terceto.items[2])
                    asm = asm + "\n;suma\n"
                    asm = asm + "        fld    dword %s.0\n" % sumando1
                    asm = asm + "        fld    dword %s\n" % sumando2
                    asm = asm + "        faddp\n"
                    asm = asm + "        fstp    eax\n"
                self.asm_terceto[terceto.id] = asm
            elif terceto.tipo == "sentencia":
                asm = ""
                for item in terceto.items:
                    try:  # TODO: hardcode, hay que soportar todas las sentencias
                        asm = asm + self.asm_terceto[item.id]
                    except:
                        pass
                self.asm_terceto[terceto.id] = asm
            elif terceto.tipo == "asig":
                asm = ""
                if isinstance(terceto.items[1], terceto.__class__):
                    # Un terceto, ej el resultado de una suma
                    # TODO: hardcode, por ahora todos los resultados a eax
                    # asm = asm + self.asm_terceto[terceto.items[1].id]
                    valor = 'eax'
                else:
                    # Valor literal, ej "123"
                    valor = terceto.items[1]
                asm = asm + "        mov    DWORD [ebp-%s], %s ; asig\n" % (terceto.items[0].offset, valor)
                self.asm_terceto[terceto.id] = asm
            elif terceto.tipo == "print":
                asm = Asm.print_
                simbolo = terceto.items[0]
                asm = asm.replace('%string', 'str')  # TODO: hardcode string
                asm = asm.replace('%len', 'str_len')  # TODO: hardcode len
                self.asm_terceto[terceto.id] = asm
            elif terceto.tipo == 'funcion':
                simbolo = terceto.items[0]

                asm = Asm.funcion
                declaraciones = self.declaraciones_funcion(simbolo_funcion=simbolo)

                asm = asm.replace('%declaraciones', declaraciones)
                asm = asm.replace('%nombre', simbolo.nombre)

                # cuerpo de la funcion
                terceto_id = terceto.items[2].id

                # TODO: hardcode. Deberia siempre encontrarse el ASM expandido
                #        para el cuerpo de la funcion
                try:
                    asm = asm.replace('%bloque', self.asm_terceto[terceto_id])
                except KeyError:
                    asm = asm.replace('%bloque', '')

                self.asm_terceto[terceto.id] = asm
                self.asm = self.asm.replace('%funciones', asm)


        # Limpiamos las marcas sin usar que pudieron haber quedado
        self.limpiar_marcas()

        with open(filename, "w") as out:
            out.write(self.asm)

    def compilar(self, asm, ejecutable):
        system("/bin/nasm -f elf -F stabs -o programa.o %s" % asm)
        system("ld -m elf_i386 -o %s programa.o" % ejecutable)

    def ejecutar(self, ejecutable):
        system("./%s" % ejecutable)

    def obtener_asm_condicion_and_or(self, condicion_izq, condicion_der):
        asm_tipo_izq = self.obtener_jump(condicion_izq.items[0])
        asm_tipo_der = self.obtener_jump(condicion_der.items[0])
        asm_condicion = Asm.condicion_and_or
        asm_condicion = asm_condicion.replace('%condicion_izq', self.asm_terceto[condicion_izq.id])
        asm_condicion = asm_condicion.replace('%tipo_condicion_izq', asm_tipo_izq)
        asm_condicion = asm_condicion.replace('%condicion_der', self.asm_terceto[condicion_der.id])
        asm_condicion = asm_condicion.replace('%tipo_condicion_der', asm_tipo_der)
        return asm_condicion
    def obtener_jump(self, tipo_condicion):
        if tipo_condicion == '==':
            asm_tipo = 'jne'
        elif tipo_condicion == '<':
            asm_tipo = 'jge'
        elif tipo_condicion == '<=':
            asm_tipo = 'jg'
        elif tipo_condicion == '>':
            asm_tipo = 'jle'
        elif tipo_condicion == '>=':
            asm_tipo = 'jl'
        return asm_tipo

    def declaraciones_main(self):
        offset = {}

        for simbolo in self.tabla_sim:
            try:
                offset[simbolo.ambito] = offset[simbolo.ambito] + 4
            except KeyError:
                offset[simbolo.ambito] = 4
            simbolo.offset = offset[simbolo.ambito]
        declaraciones_main = ("; declaraciones\n"
                             + "        sub    esp, %s\n" % offset['main'])
        self.asm = self.asm.replace("%declaraciones_start", declaraciones_main)

    def declaraciones_funcion(self, simbolo_funcion):
        offset = 0
        for simbolo in self.tabla_sim:
            if simbolo.ambito == simbolo_funcion.nombre and simbolo.offset > offset:
                offset = simbolo.offset
        declaraciones = "mov    esp, %s\n" % offset
        return declaraciones

    def representar_operando(self, operando):
        if isinstance(operando, Simbolo):
            if operando.offset > 0:
                return "   DWORD [ebp-%s]" % operando.offset
            else:
                return "   ebp"
        elif isinstance(operando, str):
            return operando

    def limpiar_marcas(self):
        self.asm = self.asm.replace('%funciones', '')

    def inventar_etiqueta(self, prefijo):
        TraductorAsm.id_etiqueta = TraductorAsm.id_etiqueta + 1
        return ".%s_%s" % (prefijo, TraductorAsm.id_etiqueta)
