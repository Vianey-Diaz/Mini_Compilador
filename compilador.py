# -*- coding: utf-8 -*-
"""
Mini Compilador de un Lenguaje Propio (en español)
Proyecto Final - IS913 Diseño de Compiladores - UNAH

Este módulo contiene las 4 etapas del compilador, más un pequeño
intérprete para mostrar la salida real del programa:
  1. Análisis léxico     -> tokenize()
  2. Análisis sintáctico  -> parse_and_analyze()
  3. Tabla de símbolos    -> se construye dentro de parse_and_analyze()
  4. Validación de tipos  -> se valida dentro de parse_and_analyze()
  (extra) Ejecución       -> parse_and_analyze() también calcula los
                             valores reales y captura la salida de 'imprimir'

Especificación del lenguaje
----------------------------
Palabras reservadas: entero, decimal, texto, vof,
                      si, si_no, fin_si, imprimir, verdadero, falso

Ejemplo:
    entero edad = 20;
    decimal promedio = 85.5;

    si (edad > 18) {
        imprimir("Mayor de edad");
    } fin_si
"""

import operator

KEYWORDS = {'entero', 'decimal', 'texto', 'vof',
            'si', 'si_no', 'fin_si', 'imprimir', 'verdadero', 'falso'}
TYPE_KEYWORDS = {'entero', 'decimal', 'texto', 'vof'}


# ============================================================
# 1. ANALIZADOR LÉXICO (LEXER)
# ============================================================
def tokenize(source):
    """Convierte el código fuente en una lista de tokens.
    Devuelve (tokens, errores_lexicos)."""
    tokens = []
    errors = []
    i = 0
    line = 1
    n = len(source)

    def is_digit(c):
        return c is not None and c.isdigit()

    def is_alpha(c):
        return c is not None and (c.isalpha() or c == '_')

    def is_alnum(c):
        return is_alpha(c) or is_digit(c)

    while i < n:
        c = source[i]

        if c == '\n':
            line += 1
            i += 1
            continue
        if c in ' \t\r':
            i += 1
            continue

        # comentarios //
        if c == '/' and i + 1 < n and source[i + 1] == '/':
            while i < n and source[i] != '\n':
                i += 1
            continue

        # cadenas de texto "..."
        if c == '"':
            j = i + 1
            s = ''
            while j < n and source[j] != '"' and source[j] != '\n':
                s += source[j]
                j += 1
            if j >= n or source[j] != '"':
                errors.append({'line': line, 'msg': f'Cadena de texto sin cerrar: "{s}'})
                i = j
                continue
            tokens.append({'type': 'CADENA', 'lexema': s, 'line': line})
            i = j + 1
            continue

        # números (entero o decimal)
        if is_digit(c):
            j = i
            num = ''
            while j < n and is_digit(source[j]):
                num += source[j]
                j += 1
            is_float = False
            if j < n and source[j] == '.' and j + 1 < n and is_digit(source[j + 1]):
                is_float = True
                num += '.'
                j += 1
                while j < n and is_digit(source[j]):
                    num += source[j]
                    j += 1
            tokens.append({
                'type': 'NUMERO_DECIMAL' if is_float else 'NUMERO_ENTERO',
                'lexema': num, 'line': line
            })
            i = j
            continue

        # identificadores y palabras reservadas
        if is_alpha(c):
            j = i
            word = ''
            while j < n and is_alnum(source[j]):
                word += source[j]
                j += 1
            if word in KEYWORDS:
                tokens.append({'type': 'PALABRA_RESERVADA:' + word.upper(), 'lexema': word, 'line': line})
            else:
                tokens.append({'type': 'IDENTIFICADOR', 'lexema': word, 'line': line})
            i = j
            continue

        # operadores de dos caracteres
        two = source[i:i + 2]
        if two in ('>=', '<=', '==', '!=', '&&', '||'):
            tokens.append({'type': 'OPERADOR', 'lexema': two, 'line': line})
            i += 2
            continue

        # operadores de un caracter
        if c in '+-*/><':
            tokens.append({'type': 'OPERADOR', 'lexema': c, 'line': line})
            i += 1
            continue
        if c == '=':
            tokens.append({'type': 'OPERADOR_ASIGNACION', 'lexema': c, 'line': line})
            i += 1
            continue

        # delimitadores
        if c in ';{}()':
            names = {';': 'PUNTO_Y_COMA', '{': 'LLAVE_ABRE', '}': 'LLAVE_CIERRA',
                      '(': 'PARENTESIS_ABRE', ')': 'PARENTESIS_CIERRA'}
            tokens.append({'type': names[c], 'lexema': c, 'line': line})
            i += 1
            continue

        errors.append({'line': line, 'msg': f"Carácter no reconocido: '{c}'"})
        i += 1

    tokens.append({'type': 'FIN', 'lexema': '', 'line': line})
    return tokens, errors


# ============================================================
# 2 + 3 + 4. PARSER (recursivo descendente) + TABLA DE SÍMBOLOS
#             + VALIDACIÓN DE TIPOS + EJECUCIÓN (intérprete simple)
#
# Gramática:
#   programa      -> sentencia* FIN
#   sentencia     -> declaracion | condicional | imprimirStmt
#   declaracion   -> TIPO IDENTIFICADOR '=' expresion ';'
#   condicional   -> 'si' '(' expresion ')' '{' sentencia* '}'
#                      ('si_no' '{' sentencia* '}')? 'fin_si'
#   imprimirStmt  -> 'imprimir' '(' expresion ')' ';'
#   expresion     -> termino (('+'|'-'|comparadores) termino)*
#   termino       -> factor (('*'|'/') factor)*
#   factor        -> NUMERO_ENTERO | NUMERO_DECIMAL | CADENA
#                      | 'verdadero' | 'falso' | IDENTIFICADOR
#                      | '(' expresion ')'
# ============================================================
class ParseError(Exception):
    pass


OPERADORES_ARITMETICOS = {'+': operator.add, '-': operator.sub, '*': operator.mul, '/': operator.truediv}
OPERADORES_COMPARACION = {'>': operator.gt, '<': operator.lt, '>=': operator.ge,
                           '<=': operator.le, '==': operator.eq, '!=': operator.ne}


def parse_and_analyze(tokens):
    """Analiza sintáctica y semánticamente la lista de tokens, y de paso
    EJECUTA el programa (calcula valores reales y captura la salida de 'imprimir').
    Devuelve (errores, tabla_de_simbolos, sintaxis_valida, salida)."""
    pos = 0
    errors = []
    symbol_table = []
    salida = []
    scope_stack = [{}]

    def peek():
        return tokens[pos]

    def advance():
        nonlocal pos
        t = tokens[pos]
        pos += 1
        return t

    def check(type_):
        return peek()['type'] == type_

    def check_prefix(prefix):
        return peek()['type'].startswith(prefix)

    def error(msg):
        errors.append({'line': peek()['line'], 'msg': msg})
        raise ParseError()

    def expect(type_, human):
        if peek()['type'] != type_:
            error(f"Se esperaba {human} pero se encontró '{peek()['lexema'] or peek()['type']}'")
        return advance()

    def declared(name):
        for scope in reversed(scope_stack):
            if name in scope:
                return scope[name]
        return None

    def categoria_de(tipo):
        if tipo in ('entero', 'decimal'):
            return 'Numérico'
        if tipo == 'texto':
            return 'Texto'
        if tipo == 'vof':
            return 'Lógico'
        return '—'

    def formatear_valor(tipo, valor):
        if tipo == 'vof':
            return 'verdadero' if valor else 'falso'
        return valor

    def infer_literal(tok):
        if tok['type'] == 'NUMERO_ENTERO':
            return 'entero', int(tok['lexema'])
        if tok['type'] == 'NUMERO_DECIMAL':
            return 'decimal', float(tok['lexema'])
        if tok['type'] == 'CADENA':
            return 'texto', tok['lexema']
        if tok['type'] == 'PALABRA_RESERVADA:VERDADERO':
            return 'vof', True
        if tok['type'] == 'PALABRA_RESERVADA:FALSO':
            return 'vof', False
        return None, None

    def factor():
        t = peek()
        if t['type'] in ('NUMERO_ENTERO', 'NUMERO_DECIMAL', 'CADENA',
                         'PALABRA_RESERVADA:VERDADERO', 'PALABRA_RESERVADA:FALSO'):
            advance()
            tipo, valor = infer_literal(t)
            return {'tipo': tipo, 'valor': valor}
        if t['type'] == 'IDENTIFICADOR':
            advance()
            info = declared(t['lexema'])
            if info is None:
                errors.append({'line': t['line'], 'msg': f"Variable no declarada: '{t['lexema']}'"})
                return {'tipo': 'error', 'valor': None}
            return {'tipo': info['tipo'], 'valor': info['valor']}
        if t['type'] == 'PARENTESIS_ABRE':
            advance()
            e = expresion()
            expect('PARENTESIS_CIERRA', "')'")
            return e
        error(f"Valor inválido: '{t['lexema'] or t['type']}'")

    def termino():
        left = factor()
        while peek()['type'] == 'OPERADOR' and peek()['lexema'] in ('*', '/'):
            op = advance()['lexema']
            right = factor()
            left = combine(left, right, op)
        return left

    def expresion():
        left = termino()
        while peek()['type'] == 'OPERADOR' and peek()['lexema'] in ('+', '-', '>', '<', '>=', '<=', '==', '!='):
            op = advance()['lexema']
            right = termino()
            left = combine(left, right, op)
        return left

    def combine(left, right, op):
        if left['tipo'] == 'error' or right['tipo'] == 'error':
            return {'tipo': 'error', 'valor': None}

        if op in OPERADORES_COMPARACION:
            # Se permite comparar dos valores del mismo tipo, o dos valores
            # numéricos (entero y decimal) aunque no sean del mismo tipo exacto
            tipos_numericos = ('entero', 'decimal')
            mismo_tipo = left['tipo'] == right['tipo']
            ambos_numericos = left['tipo'] in tipos_numericos and right['tipo'] in tipos_numericos
            if not (mismo_tipo or ambos_numericos):
                errors.append({'line': peek()['line'],
                                'msg': f"Error semántico: no se puede comparar '{left['tipo']}' con '{right['tipo']}'"})
                return {'tipo': 'error', 'valor': None}
            valor = OPERADORES_COMPARACION[op](left['valor'], right['valor'])
            return {'tipo': 'vof', 'valor': valor}

        if left['tipo'] == 'texto' or right['tipo'] == 'texto':
            if op != '+' or left['tipo'] != right['tipo']:
                errors.append({'line': peek()['line'],
                                'msg': f"Error semántico: operación '{op}' inválida entre '{left['tipo']}' y '{right['tipo']}'"})
                return {'tipo': 'error', 'valor': None}
            return {'tipo': 'texto', 'valor': left['valor'] + right['valor']}

        if left['tipo'] in ('entero', 'decimal') and right['tipo'] in ('entero', 'decimal'):
            tipo_res = 'decimal' if (left['tipo'] == 'decimal' or right['tipo'] == 'decimal') else 'entero'
            valor = OPERADORES_ARITMETICOS[op](left['valor'], right['valor'])
            if tipo_res == 'entero':
                valor = int(valor)
            return {'tipo': tipo_res, 'valor': valor}

        errors.append({'line': peek()['line'],
                        'msg': f"Error semántico: operación '{op}' inválida entre '{left['tipo']}' y '{right['tipo']}'"})
        return {'tipo': 'error', 'valor': None}

    def declaracion():
        tipo_tok = advance()  # ya sabemos que es TIPO
        tipo = tipo_tok['lexema']
        id_tok = expect('IDENTIFICADOR', 'un identificador')
        expect('OPERADOR_ASIGNACION', "'='")
        valor_expr = expresion()
        expect('PUNTO_Y_COMA', "';'")

        if id_tok['lexema'] in scope_stack[-1]:
            errors.append({'line': id_tok['line'], 'msg': f"Variable ya declarada: '{id_tok['lexema']}'"})
        else:
            scope_stack[-1][id_tok['lexema']] = {'tipo': tipo, 'valor': valor_expr['valor']}

        if valor_expr['tipo'] != 'error' and valor_expr['tipo'] != tipo:
            errors.append({'line': id_tok['line'],
                            'msg': f"Error semántico: no se puede asignar '{valor_expr['tipo']}' a '{tipo}' (variable '{id_tok['lexema']}')"})

        valor_mostrado = '(error)' if valor_expr['tipo'] == 'error' else formatear_valor(tipo, valor_expr['valor'])

        symbol_table.append({
            'nombre': id_tok['lexema'],
            'tipo': tipo,
            'categoria': categoria_de(tipo),
            'valor_inicial': valor_mostrado,
            'modificado': 'No',
        })

    def bloque(ejecutar=True):
        expect('LLAVE_ABRE', "'{'")
        scope_stack.append({})
        while not check('LLAVE_CIERRA') and not check('FIN'):
            sentencia(ejecutar)
        scope_stack.pop()
        expect('LLAVE_CIERRA', "'}'")

    def condicional():
        advance()  # 'si'
        expect('PARENTESIS_ABRE', "'('")
        cond = expresion()
        if cond['tipo'] != 'error' and cond['tipo'] != 'vof':
            errors.append({'line': peek()['line'],
                            'msg': f"Error semántico: la condición de 'si' debe ser vof, se obtuvo '{cond['tipo']}'"})
        expect('PARENTESIS_CIERRA', "')'")

        ejecutar_si = (cond['tipo'] == 'vof' and cond['valor'] is True)
        bloque(ejecutar=ejecutar_si)

        hay_si_no = check_prefix('PALABRA_RESERVADA:SI_NO')
        if hay_si_no:
            advance()
            ejecutar_si_no = (cond['tipo'] == 'vof' and cond['valor'] is False)
            bloque(ejecutar=ejecutar_si_no)
        expect('PALABRA_RESERVADA:FIN_SI', "'fin_si'")

    def imprimir_stmt(ejecutar):
        imp_tok = advance()  # 'imprimir'
        expect('PARENTESIS_ABRE', "'('")
        valor_expr = expresion()
        expect('PARENTESIS_CIERRA', "')'")
        expect('PUNTO_Y_COMA', "';'")
        if valor_expr['tipo'] != 'error' and ejecutar:
            texto = formatear_valor(valor_expr['tipo'], valor_expr['valor'])
            salida.append({'line': imp_tok['line'], 'texto': str(texto)})

    def sentencia(ejecutar=True):
        t = peek()
        if t['lexema'] in TYPE_KEYWORDS and t['type'].startswith('PALABRA_RESERVADA:'):
            declaracion()
        elif t['type'] == 'PALABRA_RESERVADA:SI':
            condicional()
        elif t['type'] == 'PALABRA_RESERVADA:IMPRIMIR':
            imprimir_stmt(ejecutar)
        else:
            error(f"Sentencia inválida, no se esperaba '{t['lexema'] or t['type']}'")

    def programa():
        while not check('FIN'):
            sentencia()

    sintaxis_valida = True
    try:
        programa()
    except ParseError:
        sintaxis_valida = False

    return errors, symbol_table, sintaxis_valida, salida


# ============================================================
# Modo consola (opcional): permite correr "python compilador.py archivo.txt"
# ============================================================
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Uso: python compilador.py <archivo.txt>")
        sys.exit(1)

    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        codigo = f.read()

    tokens, lex_errors = tokenize(codigo)

    print("TOKENS ENCONTRADOS:\n")
    for t in tokens:
        if t['type'] != 'FIN':
            print(f"{t['type']} -> {t['lexema']}")
    print(f"\nTotal de tokens: {len(tokens) - 1}")

    sem_errors, symbol_table, sintaxis_valida, salida = parse_and_analyze(tokens)

    print("\nTABLA DE SIMBOLOS:\n")
    for s in symbol_table:
        print(f"{s['nombre']} -> {s['tipo']} ({s['categoria']}) -> {s['valor_inicial']} -> ¿modificado? {s['modificado']}")

    print("\nSALIDA DEL PROGRAMA:\n")
    if salida:
        for linea in salida:
            print(linea['texto'])
    else:
        print("(sin salida)")

    print("\nRESULTADO:\n")
    todos_errores = lex_errors + sem_errors
    if not todos_errores and sintaxis_valida:
        print("Compilación exitosa")
    else:
        for e in todos_errores:
            print(f"Línea {e['line']}: {e['msg']}")
        if not sintaxis_valida and not todos_errores:
            print("Error sintáctico detuvo el análisis.")