# Mini Compilador de un Lenguaje Propio

Proyecto Final — IS913 Diseño de Compiladores  
Universidad Nacional Autónoma de Honduras (UNAH)

## Descripción

Mini compilador para un lenguaje de programación propio, escrito en español,
que implementa las 4 etapas principales de un compilador:

1. Análisis léxico (tokenización)
2. Análisis sintáctico (parser recursivo descendente)
3. Tabla de símbolos
4. Validación de tipos

El backend está hecho en Python puro (`compilador.py`) y se expone a través
de una interfaz web con Flask (`app.py` + `templates/index.html`).

## Estructura del proyecto
ProyectoFinal_Compilador/
├── app.py # Servidor Flask
├── compilador.py # Lógica del compilador (lexer, parser, tipos)
├── requirements.txt # Dependencias
├── README.md
├── templates/
│ └── index.html # Interfaz web
├── static/
│ └── style.css # Estilos de la interfaz
└── ejemplos/
├── ejemplo_exitoso.txt
├── ejemplo_error_sintactico.txt
└── ejemplo_error_semantico.txt
## Cómo correrlo

1. Abre una terminal dentro de la carpeta `ProyectoFinal_Compilador`.
2. Instala las dependencias:
pip install -r requirements.txt
3. Levanta el servidor:
python app.py
4. Abre el navegador en:
http://127.0.0.1:5000
También se puede correr sin interfaz web, en modo consola:
python compilador.py ejemplos/ejemplo_exitoso.txt
## Especificación del lenguaje

**Palabras reservadas:**

| Palabra      | Uso                          |
|--------------|-------------------------------|
| `entero`     | Tipo de dato numérico entero |
| `decimal`    | Tipo de dato numérico decimal |
| `texto`      | Tipo de dato cadena de texto |
| `booleano`   | Tipo de dato lógico          |
| `verdadero` / `falso` | Valores booleanos   |
| `si` / `si_no` / `fin_si` | Condicional       |
| `imprimir`   | Muestra un valor en pantalla |

**Ejemplo de código:**
entero edad = 20;
decimal promedio = 85.5;
texto nombre = "Maria";

si (edad > 18) {
imprimir("Mayor de edad");
} si_no {
imprimir("Menor de edad");
} fin_si

imprimir(nombre);
## Casos de prueba incluidos

| Archivo | Qué demuestra |
|---|---|
| `ejemplos/ejemplo_exitoso.txt` | Compilación exitosa, sin errores |
| `ejemplos/ejemplo_error_sintactico.txt` | Error sintáctico (`entero edad = ;`) |
| `ejemplos/ejemplo_error_semantico.txt` | Error semántico de tipos (`entero edad = "hola";`) |

## Guía rápida para la defensa

Según los criterios de evaluación del proyecto, hay que poder explicar:

- **Cómo identifiqué cada token** → función `tokenize()` en `compilador.py`,
  recorre el código carácter por carácter y clasifica cada uno (número,
  palabra reservada, identificador, operador, delimitador, cadena).
- **Cómo valido la gramática** → `parse_and_analyze()`, un parser recursivo
  descendente: cada regla de la gramática (declaración, condicional,
  impresión, expresión) es una función que llama a las siguientes.
- **Dónde guardo las variables** → `scope_stack`, una pila de diccionarios
  (nombre → tipo); cada bloque `{ }` agrega un nuevo diccionario y lo
  elimina al cerrar, así las variables respetan su ámbito.
- **Cómo comparo tipos** → función `combine_types()`, valida que las
  operaciones (`+`, `-`, comparaciones, etc.) se hagan entre tipos
  compatibles, y `declaracion()` valida que el valor asignado coincida
  con el tipo declarado.
- **Cómo detecto errores** → cada etapa (léxica, sintáctica, semántica)
  acumula sus propios errores en una lista con número de línea, y se
  muestran todos juntos en el resultado final.