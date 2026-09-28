/* pilas3d bloques: definiciones de bloques + generadores Python.
 *
 * Los bloques generan código pilas3d real — el chico ve a la derecha
 * el Python que produce su programa de bloques.
 */

'use strict';

// ------------------------------------------------------------------
// utilidades
// ------------------------------------------------------------------

// Blockly 9: el generador es pythonGenerator; los bloques se
// registran como funciones asignadas directamente sobre él.
var GEN = Blockly.Python.pythonGenerator || Blockly.Python;

// contador para nombres de funciones auxiliares (esperar, al_click…)
// — se resetea al inicio de cada workspaceToCode (GEN.init).
var _contador_fn = 0;
var _gen_init_real = GEN.init;
if (_gen_init_real) {
  GEN.init = function (workspace) {
    _contador_fn = 0;
    _gen_init_real.call(GEN, workspace);
  };
}
function nombre_unico(base) {
  return base + '_' + (_contador_fn++);
}

function registrar(tipo, fn) {
  GEN[tipo] = fn;
}

function sanea(nombre) {
  var s = (nombre || '').trim().replace(/\W/g, '_');
  if (!s) s = 'actor';
  if (/^\d/.test(s)) s = 'a_' + s;
  return s;
}

// tipos de bloque que "crean" un nombre en la escena
var CREA_NOMBRE = {
  'p3d_crear_actor': 'NOMBRE',
  'p3d_crear_modelo': 'NOMBRE',
  'p3d_crear_escenario': 'NOMBRE',
};

function nombres_creados(block) {
  return block.workspace.getAllBlocks(false)
    .filter(function (b) { return CREA_NOMBRE[b.type]; })
    .map(function (b) {
      return sanea(b.getFieldValue(CREA_NOMBRE[b.type]));
    });
}

function globales(block) {
  var ns = nombres_creados(block);
  return ns.length ? GEN.INDENT + 'global ' + ns.join(', ') + '\n' : '';
}

function campo_nombre(block, campo) {
  return sanea(block.getFieldValue(campo || 'NOMBRE'));
}

var COLORES = [
  ['rojo', 'rojo'], ['verde', 'verde'], ['azul', 'azul'],
  ['amarillo', 'amarillo'], ['celeste', 'celeste'],
  ['naranja', 'naranja'], ['rosa', 'rosa'], ['violeta', 'violeta'],
  ['blanco', 'blanco'], ['gris', 'gris'], ['negro', 'negro'],
];

// menú dinámico con los actores ya creados en el workspace — así los
// bloques no piden tipear el nombre (un error típico de los chicos).
function actores_opciones() {
  var campo = this;
  var bloque = campo && campo.getSourceBlock ?
      campo.getSourceBlock() : null;
  var nombres = bloque ? nombres_creados(bloque) : [];
  if (!nombres.length) return [['(creá un actor primero)', 'actor']];
  return nombres.map(function (n) { return [n, n]; });
}

// igual que actores_opciones pero con "(cualquier lugar)" arriba —
// para el bloque de click.
function actores_o_cualquiera() {
  var ops = actores_opciones.call(this);
  if (ops.length === 1 && ops[0][1] === 'actor') ops = [];
  return [['(cualquier lugar)', '*']].concat(ops);
}

// teclas para "al pulsar la tecla": valor = atributo de pilas.simbolos
var TECLAS = [
  ['espacio', 'ESPACIO'], ['enter', 'ENTER'], ['escape', 'ESCAPE'],
  ['izquierda', 'IZQUIERDA'], ['derecha', 'DERECHA'],
  ['arriba', 'ARRIBA'], ['abajo', 'ABAJO'],
].concat('abcdefghijklmnopqrstuvwxyz'.split('').map(function (l) {
  return [l, l];
}));

// ------------------------------------------------------------------
// definición de bloques
// ------------------------------------------------------------------

Blockly.defineBlocksWithJsonArray([

  // -- eventos ------------------------------------------------------
  {
    type: 'p3d_al_iniciar',
    message0: 'al iniciar %1',
    args0: [{ type: 'input_statement', name: 'HACER' }],
    colour: 45,
    tooltip: 'Corre una vez al apretar Ejecutar',
  },
  {
    type: 'p3d_por_siempre',
    message0: 'por siempre %1',
    args0: [{ type: 'input_statement', name: 'HACER' }],
    colour: 45,
    tooltip: 'Corre en cada frame, una y otra vez',
  },
  {
    type: 'p3d_al_click',
    message0: 'al hacer click en %1 hacer %2',
    args0: [
      { type: 'field_dropdown', name: 'DONDE',
        options: actores_o_cualquiera },
      { type: 'input_statement', name: 'HACER' },
    ],
    colour: 45,
    tooltip: 'Corre una vez al hacer click con el mouse',
  },
  {
    type: 'p3d_al_pulsar',
    message0: 'al pulsar la tecla %1 hacer %2',
    args0: [
      { type: 'field_dropdown', name: 'TECLA', options: TECLAS },
      { type: 'input_statement', name: 'HACER' },
    ],
    colour: 45,
    tooltip: 'Corre una vez al pulsar esa tecla',
  },

  // -- actores ------------------------------------------------------
  {
    type: 'p3d_crear_actor',
    message0: 'crear %1 llamado %2 en x %3 y %4 z %5',
    args0: [
      { type: 'field_dropdown', name: 'TIPO', options: [
        ['cubo', 'Cubo'], ['esfera', 'Esfera'],
        ['robot', 'Robot'], ['humanoide', 'Humanoide'],
        ['mono', 'Mono'], ['araña', 'Arania'],
        ['espectro', 'Espectro'],
      ] },
      { type: 'field_input', name: 'NOMBRE', text: 'cubo' },
      { type: 'field_number', name: 'X', value: 0 },
      { type: 'field_number', name: 'Y', value: 0 },
      { type: 'field_number', name: 'Z', value: 0 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 290,
    tooltip: 'Crea un actor en la escena',
  },
  {
    type: 'p3d_crear_modelo',
    message0: 'crear modelo %1 llamado %2',
    args0: [
      { type: 'field_input', name: 'RUTA',
        text: 'modelos/personajes/fox/Fox.glb' },
      { type: 'field_input', name: 'NOMBRE', text: 'modelo' },
    ],
    previousStatement: null, nextStatement: null,
    colour: 290,
  },
  {
    type: 'p3d_crear_escenario',
    message0: 'crear %1 llamado %2',
    args0: [
      { type: 'field_dropdown', name: 'TIPO', options: [
        ['piso', 'Piso'], ['ejes', 'Ejes'], ['plano', 'Plano'],
        ['pared', 'Pared'], ['cartel', 'Cartel'],
      ] },
      { type: 'field_input', name: 'NOMBRE', text: 'piso' },
    ],
    previousStatement: null, nextStatement: null,
    colour: 290,
    tooltip: 'Escenario: piso de grilla, ejes, plano, pared o cartel',
  },
  {
    type: 'p3d_eliminar',
    message0: 'eliminar %1',
    args0: [{ type: 'field_dropdown', name: 'NOMBRE',
              options: actores_opciones }],
    previousStatement: null, nextStatement: null,
    colour: 290,
  },

  // -- movimiento ---------------------------------------------------
  {
    type: 'p3d_mover',
    message0: 'mover %1 en %2 %3',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE', options: actores_opciones },
      { type: 'field_dropdown', name: 'EJE', options: [
        ['x', 'x'], ['y', 'y'], ['z', 'z']] },
      { type: 'field_number', name: 'N', value: 0.05 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 160,
  },
  {
    type: 'p3d_ir_a',
    message0: 'llevar %1 a x %2 y %3 z %4',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE', options: actores_opciones },
      { type: 'field_number', name: 'X', value: 0 },
      { type: 'field_number', name: 'Y', value: 0 },
      { type: 'field_number', name: 'Z', value: 0 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 160,
  },
  {
    type: 'p3d_ir_al_azar',
    message0: 'llevar %1 a un lugar al azar entre %2 y %3',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE', options: actores_opciones },
      { type: 'field_number', name: 'MIN', value: -5 },
      { type: 'field_number', name: 'MAX', value: 5 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 160,
    tooltip: 'Teletransporta al actor a un punto al azar del piso',
  },
  {
    type: 'p3d_girar',
    message0: 'girar %1 en %2 %3 grados',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE', options: actores_opciones },
      { type: 'field_dropdown', name: 'EJE', options: [
        ['eje x', 'rotacion_x'], ['eje y', 'rotacion_y'],
        ['eje z', 'rotacion_z']] },
      { type: 'field_number', name: 'N', value: 2 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 160,
  },

  // -- apariencia ---------------------------------------------------
  {
    type: 'p3d_color',
    message0: 'poner %1 de color %2',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE', options: actores_opciones },
      { type: 'field_dropdown', name: 'COLOR', options: COLORES },
    ],
    previousStatement: null, nextStatement: null,
    colour: 200,
  },
  {
    type: 'p3d_texto',
    message0: 'mostrar texto %1 en x %2 y %3',
    args0: [
      { type: 'field_input', name: 'TEXTO', text: 'hola' },
      { type: 'field_number', name: 'X', value: 10 },
      { type: 'field_number', name: 'Y', value: 30 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 200,
  },
  {
    type: 'p3d_decir',
    message0: 'escribir en consola %1',
    args0: [{ type: 'field_input', name: 'TEXTO', text: 'hola' }],
    previousStatement: null, nextStatement: null,
    colour: 200,
  },
  {
    type: 'p3d_animar',
    message0: 'animar %1 con %2',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE', options: actores_opciones },
      { type: 'field_input', name: 'ANIM', text: 'Walk' },
    ],
    previousStatement: null, nextStatement: null,
    colour: 200,
  },
  {
    type: 'p3d_globo',
    message0: 'hacer que %1 diga %2 durante %3 s',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE', options: actores_opciones },
      { type: 'field_input', name: 'TEXTO', text: 'hola!' },
      { type: 'field_number', name: 'SEG', value: 3, min: 0 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 200,
  },
  {
    type: 'p3d_sonido',
    message0: 'reproducir sonido %1',
    args0: [
      { type: 'field_input', name: 'RUTA', text: 'tick.wav' },
    ],
    previousStatement: null, nextStatement: null,
    colour: 200,
  },

  // -- tiempo -------------------------------------------------------
  {
    type: 'p3d_interpolar',
    message0: 'llevar %1 suave a x %2 y %3 z %4 en %5 s',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE', options: actores_opciones },
      { type: 'field_number', name: 'X', value: 0 },
      { type: 'field_number', name: 'Y', value: 0 },
      { type: 'field_number', name: 'Z', value: 0 },
      { type: 'field_number', name: 'SEG', value: 2, min: 0 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 20,
  },
  {
    type: 'p3d_esperar',
    message0: 'esperar %1 s y hacer %2',
    args0: [
      { type: 'field_number', name: 'SEG', value: 2, min: 0 },
      { type: 'input_statement', name: 'HACER' },
    ],
    previousStatement: null, nextStatement: null,
    colour: 20,
  },
  {
    type: 'p3d_cada',
    message0: 'cada %1 s hacer %2',
    args0: [
      { type: 'field_number', name: 'SEG', value: 2, min: 0 },
      { type: 'input_statement', name: 'HACER' },
    ],
    previousStatement: null, nextStatement: null,
    colour: 20,
  },

  // -- cámara -------------------------------------------------------
  {
    type: 'p3d_camara_orbital',
    message0: 'cámara orbital con el mouse',
    previousStatement: null, nextStatement: null,
    colour: 60,
    tooltip: 'El mouse gira alrededor de la escena, la rueda acerca',
  },
  {
    type: 'p3d_camara_seguir',
    message0: 'la cámara sigue a %1 en %2',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE', options: actores_opciones },
      { type: 'field_dropdown', name: 'MODO', options: [
        ['primera persona', 'primera'],
        ['de frente', 'segunda'],
        ['tercera persona', 'tercera'],
      ] },
    ],
    previousStatement: null, nextStatement: null,
    colour: 60,
  },
  {
    type: 'p3d_camara_libre',
    message0: 'soltar la cámara',
    previousStatement: null, nextStatement: null,
    colour: 60,
    tooltip: 'La cámara deja de seguir al actor',
  },

  // -- sensores -----------------------------------------------------
  {
    type: 'p3d_tecla',
    message0: 'tecla %1 pulsada',
    args0: [{ type: 'field_dropdown', name: 'TECLA', options: [
      ['izquierda', 'izquierda'], ['derecha', 'derecha'],
      ['arriba', 'arriba'], ['abajo', 'abajo'],
      ['espacio', 'ESPACIO'], ['enter', 'ENTER'],
    ].concat('abcdefghijklmnopqrstuvwxyz'.split('').map(function (l) {
      return [l, l];
    })) }],
    output: 'Boolean', colour: 210,
  },
  {
    type: 'p3d_colisiona',
    message0: '%1 toca a %2',
    args0: [
      { type: 'field_dropdown', name: 'A', options: actores_opciones },
      { type: 'field_dropdown', name: 'B', options: actores_opciones },
    ],
    output: 'Boolean', colour: 210,
  },
  {
    type: 'p3d_boton_mouse',
    message0: 'botón %1 del mouse pulsado',
    args0: [{ type: 'field_dropdown', name: 'BOTON', options: [
      ['izquierdo', 'izquierdo'], ['derecho', 'derecho'],
      ['medio', 'medio'],
    ] }],
    output: 'Boolean', colour: 210,
  },
  {
    type: 'p3d_mouse_x',
    message0: 'posición x del mouse',
    output: 'Number', colour: 210,
  },
  {
    type: 'p3d_mouse_y',
    message0: 'posición y del mouse',
    output: 'Number', colour: 210,
  },
]);

// ------------------------------------------------------------------
// generadores Python
// ------------------------------------------------------------------

function cuerpo(block) {
  return GEN.statementToCode(block, 'HACER') || GEN.INDENT + 'pass\n';
}

registrar('p3d_al_iniciar', function (block) {
  var nom = 'iniciar';
  return 'def ' + nom + '():\n' + globales(block) + cuerpo(block) +
         nom + '()\n\n';
});

registrar('p3d_por_siempre', function (block) {
  return 'def siempre():\n' + globales(block) + cuerpo(block) +
         'pilas.tareas.siempre(0, siempre)\n\n';
});

registrar('p3d_al_click', function (block) {
  var fn = nombre_unico('al_click');
  var donde = block.getFieldValue('DONDE');
  var dentro = GEN.statementToCode(block, 'HACER') ||
      GEN.INDENT + 'pass\n';
  if (donde !== '*') {
    dentro = GEN.INDENT + 'if actor is ' + sanea(donde) + ':\n' +
             GEN.prefixLines(dentro, GEN.INDENT);
  }
  return 'def ' + fn + '(actor, punto):\n' + globales(block) +
         dentro + 'pilas.cuando_hace_click(' + fn + ')\n\n';
});

registrar('p3d_al_pulsar', function (block) {
  var fn = nombre_unico('al_pulsar');
  var dentro = GEN.statementToCode(block, 'HACER') ||
      GEN.INDENT + 'pass\n';
  return 'def ' + fn + '(simbolo):\n' + globales(block) +
         GEN.INDENT + 'if simbolo == pilas.simbolos.' +
         block.getFieldValue('TECLA') + ':\n' +
         GEN.prefixLines(dentro, GEN.INDENT) +
         'pilas.escena_actual().cuando_pulsa_tecla = ' + fn + '\n\n';
});

registrar('p3d_crear_actor', function (block) {
  var tipo = block.getFieldValue('TIPO');
  var nom = campo_nombre(block);
  return nom + ' = pilas.actores.' + tipo +
         '(x=' + block.getFieldValue('X') +
         ', y=' + block.getFieldValue('Y') +
         ', z=' + block.getFieldValue('Z') + ')\n';
});

registrar('p3d_crear_modelo', function (block) {
  return campo_nombre(block) + ' = pilas.actores.ModeloGLTF(' +
         GEN.quote_(block.getFieldValue('RUTA')) + ')\n';
});

registrar('p3d_crear_escenario', function (block) {
  return campo_nombre(block) + ' = pilas.actores.' +
         block.getFieldValue('TIPO') + '()\n';
});

registrar('p3d_eliminar', function (block) {
  return campo_nombre(block) + '.eliminar()\n';
});

registrar('p3d_mover', function (block) {
  return campo_nombre(block) + '.' + block.getFieldValue('EJE') +
         ' += ' + block.getFieldValue('N') + '\n';
});

registrar('p3d_ir_a', function (block) {
  var n = campo_nombre(block);
  return n + '.x = ' + block.getFieldValue('X') + '\n' +
         n + '.y = ' + block.getFieldValue('Y') + '\n' +
         n + '.z = ' + block.getFieldValue('Z') + '\n';
});

registrar('p3d_ir_al_azar', function (block) {
  GEN.definitions_['import random'] = 'import random';
  var n = campo_nombre(block);
  var mn = block.getFieldValue('MIN');
  var mx = block.getFieldValue('MAX');
  return n + '.x = random.uniform(' + mn + ', ' + mx + ')\n' +
         n + '.z = random.uniform(' + mn + ', ' + mx + ')\n';
});

registrar('p3d_girar', function (block) {
  return campo_nombre(block) + '.' + block.getFieldValue('EJE') +
         ' += ' + block.getFieldValue('N') + '\n';
});

registrar('p3d_color', function (block) {
  return campo_nombre(block) + '.color = pilas.colores.' +
         block.getFieldValue('COLOR') + '\n';
});

registrar('p3d_texto', function (block) {
  return 'pilas.actores.Texto(' +
         GEN.quote_(block.getFieldValue('TEXTO')) +
         ', x=' + block.getFieldValue('X') +
         ', y=' + block.getFieldValue('Y') + ')\n';
});

registrar('p3d_decir', function (block) {
  return 'print(' +
         GEN.quote_(block.getFieldValue('TEXTO')) + ')\n';
});

registrar('p3d_animar', function (block) {
  return campo_nombre(block) + '.animar(' +
         GEN.quote_(block.getFieldValue('ANIM')) +
         ', ciclica=True)\n';
});

registrar('p3d_globo', function (block) {
  return campo_nombre(block) + '.decir(' +
         GEN.quote_(block.getFieldValue('TEXTO')) +
         ', duracion=' + block.getFieldValue('SEG') + ')\n';
});

registrar('p3d_sonido', function (block) {
  return 'pilas.sonidos.cargar(' +
         GEN.quote_(block.getFieldValue('RUTA')) + ').reproducir()\n';
});

registrar('p3d_interpolar', function (block) {
  var n = campo_nombre(block);
  var d = block.getFieldValue('SEG');
  return 'pilas.interpolar(' + n + ", 'x', " +
         block.getFieldValue('X') + ', duracion=' + d + ')\n' +
         'pilas.interpolar(' + n + ", 'y', " +
         block.getFieldValue('Y') + ', duracion=' + d + ')\n' +
         'pilas.interpolar(' + n + ", 'z', " +
         block.getFieldValue('Z') + ', duracion=' + d + ')\n';
});

registrar('p3d_esperar', function (block) {
  var fn = nombre_unico('esperar');
  return 'def ' + fn + '():\n' + globales(block) + cuerpo(block) +
         'pilas.tareas.una_vez(' + block.getFieldValue('SEG') +
         ', ' + fn + ')\n';
});

registrar('p3d_cada', function (block) {
  var fn = nombre_unico('repetir');
  return 'def ' + fn + '():\n' + globales(block) + cuerpo(block) +
         'pilas.tareas.siempre(' + block.getFieldValue('SEG') +
         ', ' + fn + ')\n';
});

registrar('p3d_camara_orbital', function (block) {
  return 'pilas.escena_actual().camara.usar_control_orbital()\n';
});

registrar('p3d_camara_seguir', function (block) {
  return 'pilas.escena_actual().camara.seguir_a(' +
         campo_nombre(block) + ", modo='" +
         block.getFieldValue('MODO') + "')\n";
});

registrar('p3d_camara_libre', function (block) {
  return 'pilas.escena_actual().camara.dejar_de_seguir()\n';
});

registrar('p3d_tecla', function (block) {
  var tecla = block.getFieldValue('TECLA');
  var flechas = ['izquierda', 'derecha', 'arriba', 'abajo'];
  var expr = flechas.indexOf(tecla) >= 0 ?
    'pilas.control.' + tecla :
    'pilas.control.simbolo(pilas.simbolos.' + tecla + ')';
  return [expr, GEN.ORDER_ATOMIC];
});

registrar('p3d_colisiona', function (block) {
  return [sanea(block.getFieldValue('A')) +
          '.colisiona_en_plano_con(' +
          sanea(block.getFieldValue('B')) + ')',
          GEN.ORDER_ATOMIC];
});

registrar('p3d_boton_mouse', function (block) {
  return ['pilas.control.boton_' + block.getFieldValue('BOTON'),
          GEN.ORDER_ATOMIC];
});

registrar('p3d_mouse_x', function (block) {
  return ['pilas.control.mouse_x', GEN.ORDER_ATOMIC];
});

registrar('p3d_mouse_y', function (block) {
  return ['pilas.control.mouse_y', GEN.ORDER_ATOMIC];
});

// ------------------------------------------------------------------
// toolbox + arranque
// ------------------------------------------------------------------

var TOOLBOX = {
  kind: 'categoryToolbox',
  contents: [
    { kind: 'category', name: 'Eventos', colour: '45',
      contents: [
        { kind: 'block', type: 'p3d_al_iniciar' },
        { kind: 'block', type: 'p3d_por_siempre' },
        { kind: 'block', type: 'p3d_al_click' },
        { kind: 'block', type: 'p3d_al_pulsar' },
      ] },
    { kind: 'category', name: 'Actores', colour: '290',
      contents: [
        { kind: 'block', type: 'p3d_crear_actor' },
        { kind: 'block', type: 'p3d_crear_modelo' },
        { kind: 'block', type: 'p3d_crear_escenario' },
        { kind: 'block', type: 'p3d_eliminar' },
      ] },
    { kind: 'category', name: 'Movimiento', colour: '160',
      contents: [
        { kind: 'block', type: 'p3d_mover' },
        { kind: 'block', type: 'p3d_ir_a' },
        { kind: 'block', type: 'p3d_ir_al_azar' },
        { kind: 'block', type: 'p3d_girar' },
      ] },
    { kind: 'category', name: 'Apariencia', colour: '200',
      contents: [
        { kind: 'block', type: 'p3d_color' },
        { kind: 'block', type: 'p3d_texto' },
        { kind: 'block', type: 'p3d_decir' },
        { kind: 'block', type: 'p3d_globo' },
        { kind: 'block', type: 'p3d_animar' },
        { kind: 'block', type: 'p3d_sonido' },
      ] },
    { kind: 'category', name: 'Tiempo', colour: '20',
      contents: [
        { kind: 'block', type: 'p3d_interpolar' },
        { kind: 'block', type: 'p3d_esperar' },
        { kind: 'block', type: 'p3d_cada' },
      ] },
    { kind: 'category', name: 'Cámara', colour: '60',
      contents: [
        { kind: 'block', type: 'p3d_camara_orbital' },
        { kind: 'block', type: 'p3d_camara_seguir' },
        { kind: 'block', type: 'p3d_camara_libre' },
      ] },
    { kind: 'category', name: 'Sensores', colour: '210',
      contents: [
        { kind: 'block', type: 'p3d_tecla' },
        { kind: 'block', type: 'p3d_boton_mouse' },
        { kind: 'block', type: 'p3d_colisiona' },
        { kind: 'block', type: 'p3d_mouse_x' },
        { kind: 'block', type: 'p3d_mouse_y' },
        { kind: 'block', type: 'logic_compare' },
        { kind: 'block', type: 'logic_operation' },
        { kind: 'block', type: 'logic_negate' },
      ] },
    { kind: 'category', name: 'Control', colour: '120',
      contents: [
        { kind: 'block', type: 'controls_if' },
        { kind: 'block', type: 'controls_repeat_ext' },
        { kind: 'block', type: 'math_number' },
      ] },
    { kind: 'category', name: 'Matemática', colour: '230',
      contents: [
        { kind: 'block', type: 'math_number' },
        { kind: 'block', type: 'math_arithmetic' },
        { kind: 'block', type: 'math_random_int' },
        { kind: 'block', type: 'math_random_float' },
      ] },
  ],
};

var ws = Blockly.inject('blockly', {
  toolbox: TOOLBOX,
  renderer: 'zelos',              // look tipo Scratch
  trashcan: true,
  scrollbars: true,
  zoom: { controls: true, wheel: true, startScale: 0.9 },
});

// -- guardar / abrir proyectos -----------------------------------------
// autosave en localStorage a cada cambio + botones para exportar el
// workspace a un archivo .bloques.xml y volver a abrirlo.

var CLAVE_GUARDADO = 'pilas3d_bloques_workspace';

function xml_del_workspace() {
  return Blockly.Xml.domToText(Blockly.Xml.workspaceToDom(ws));
}

function cargar_xml(xml) {
  ws.clear();
  Blockly.Xml.domToWorkspace(Blockly.Xml.textToDom(xml), ws);
}

// programa inicial de ejemplo (solo si no hay nada guardado)
var INICIAL =
  '<xml><block type="p3d_al_iniciar" x="30" y="30">' +
  '<statement name="HACER">' +
  '<block type="p3d_crear_actor">' +
  '<field name="TIPO">Cubo</field><field name="NOMBRE">cubo</field>' +
  '</block></statement></block>' +
  '<block type="p3d_por_siempre" x="30" y="140">' +
  '<statement name="HACER">' +
  '<block type="p3d_girar">' +
  '<field name="NOMBRE">cubo</field>' +
  '<field name="EJE">rotacion_y</field><field name="N">3</field>' +
  '</block></statement></block></xml>';

var guardado = null;
try { guardado = localStorage.getItem(CLAVE_GUARDADO); } catch (e) {}
try {
  cargar_xml(guardado || INICIAL);
} catch (e) {
  cargar_xml(INICIAL);              // XML guardado corrupto -> default
}

document.getElementById('guardar').onclick = function () {
  var a = document.createElement('a');
  a.href = URL.createObjectURL(
      new Blob([xml_del_workspace()], { type: 'text/xml' }));
  a.download = 'mi_programa.bloques.xml';
  a.click();
};

var inputAbrir = document.getElementById('abrir_archivo');
document.getElementById('abrir').onclick = function () {
  inputAbrir.click();
};
inputAbrir.onchange = function () {
  var archivo = inputAbrir.files[0];
  if (!archivo) return;
  var lector = new FileReader();
  lector.onload = function () {
    try {
      cargar_xml(lector.result);
    } catch (e) {
      spanEstado.className = 'error';
      spanEstado.textContent = 'ese archivo no es un programa de bloques';
    }
  };
  lector.readAsText(archivo);
  inputAbrir.value = '';
};

// -- cargador de ejemplos ---------------------------------------------
// cada ejemplo es un workspace XML (ver ejemplos.js): se limpia el
// editor y se cargan sus bloques, listos para mirar y ejecutar.

var selEjemplos = document.getElementById('ejemplos');
if (typeof EJEMPLOS !== 'undefined') {
  EJEMPLOS.forEach(function (e, i) {
    var op = document.createElement('option');
    op.value = i;
    op.textContent = e.nombre;
    selEjemplos.appendChild(op);
  });
}
selEjemplos.onchange = function () {
  if (selEjemplos.value === '') return;
  cargar_xml(EJEMPLOS[parseInt(selEjemplos.value, 10)].xml);
  selEjemplos.value = '';
};

// -- vista de código + ejecución --------------------------------------

var divCodigo = document.getElementById('codigo');
var divSalida = document.getElementById('salida');
var spanEstado = document.getElementById('estado');

function regenerar() {
  try {
    divCodigo.textContent = GEN.workspaceToCode(ws);
  } catch (e) {
    divCodigo.textContent = '# error generando: ' + e;
  }
}
ws.addChangeListener(function (e) {
  if (!e.isUiEvent) {
    regenerar();
    try {
      localStorage.setItem(CLAVE_GUARDADO, xml_del_workspace());
    } catch (err) {}
  }
});
regenerar();

var boton = document.getElementById('ejecutar');
var corriendo = false;

function pintar_boton() {
  if (corriendo) {
    boton.textContent = '■ Detener';
    boton.style.background = '#c0392b';
  } else {
    boton.textContent = '▶ Ejecutar';
    boton.style.background = '';
  }
}

boton.onclick = function () {
  if (corriendo) {
    fetch('/detener', { method: 'POST' }).then(consultar_resultado);
    return;
  }
  var codigo = GEN.workspaceToCode(ws);
  spanEstado.className = '';
  spanEstado.textContent = 'abriendo la ventana…';
  fetch('/codigo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ codigo: codigo }),
  }).then(function () {
    setTimeout(consultar_resultado, 600);
  }).catch(function () {
    spanEstado.className = 'error';
    spanEstado.textContent = 'no llega al servidor';
  });
};

var ultimo_resultado = null;
function consultar_resultado() {
  fetch('/resultado').then(function (r) { return r.json(); })
    .then(function (r) {
      corriendo = (r.estado === 'ejecutando');
      pintar_boton();
      if (r === ultimo_resultado) return;
      ultimo_resultado = r;
      if (r.estado === 'ejecutando') {
        spanEstado.className = 'ok';
        spanEstado.textContent = 'corriendo — la ventana está abierta';
        divSalida.textContent = r.salida || '(sin salida todavía)';
      } else if (r.estado === 'ok') {
        spanEstado.className = 'ok';
        spanEstado.textContent = 'terminó bien';
        divSalida.textContent = r.salida || '(sin salida)';
      } else if (r.estado === 'error') {
        spanEstado.className = 'error';
        spanEstado.textContent = 'error en el código';
        divSalida.textContent = r.salida;
      } else if (r.estado === 'detenido') {
        spanEstado.className = '';
        spanEstado.textContent = 'detenido';
        divSalida.textContent = r.salida || '(sin salida)';
      }
    }).catch(function () {
      corriendo = false;
      pintar_boton();
    });
}
setInterval(consultar_resultado, 900);
