# -*- coding: utf-8 -*-
"""
Servidor Flask para el Mini Compilador de un Lenguaje Propio.
Proyecto Final - IS913 Diseño de Compiladores - UNAH
"""

from flask import Flask, render_template, request, jsonify
from compilador import tokenize, parse_and_analyze

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/compilar', methods=['POST'])
def compilar():
    data = request.get_json(force=True)
    codigo = data.get('codigo', '')

    # Etapa 1: análisis léxico
    tokens, lex_errors = tokenize(codigo)

    # Etapas 2, 3, 4 + ejecución
    sem_errors, symbol_table, sintaxis_valida, salida = parse_and_analyze(tokens)

    tokens_out = [t for t in tokens if t['type'] != 'FIN']

    return jsonify({
        'tokens': tokens_out,
        'total_tokens': len(tokens_out),   # <-- nuevo: total de tokens encontrados
        'lex_errors': lex_errors,
        'sem_errors': sem_errors,
        'symbol_table': symbol_table,
        'sintaxis_valida': sintaxis_valida,
        'salida': salida,                  # <-- nuevo: lo que "imprimió" el programa
    })


if __name__ == '__main__':
    app.run(debug=True)