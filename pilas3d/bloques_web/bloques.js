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
    type: 'p3d_eliminar',
    message0: 'eliminar %1',
    args0: [{ type: 'field_input', name: 'NOMBRE', text: 'cubo' }],
    previousStatement: null, nextStatement: null,
    colour: 290,
  },

  // -- movimiento ---------------------------------------------------
  {
    type: 'p3d_mover',
    message0: 'mover %1 en %2 %3',
    args0: [
      { type: 'field_input', name: 'NOMBRE', text: 'cubo' },
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
      { type: 'field_input', name: 'NOMBRE', text: 'cubo' },
      { type: 'field_number', name: 'X', value: 0 },
      { type: 'field_number', name: 'Y', value: 0 },
      { type: 'field_number', name: 'Z', value: 0 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 160,
  },
  {
    type: 'p3d_girar',
    message0: 'girar %1 en %2 %3 grados',
    args0: [
      { type: 'field_input', name: 'NOMBRE', text: 'cubo' },
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
      { type: 'field_input', name: 'NOMBRE', text: 'cubo' },
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
      { type: 'field_input', name: 'NOMBRE', text: 'modelo' },
      { type: 'field_input', name: 'ANIM', text: 'Walk' },
    ],
    previousStatement: null, nextStatement: null,
    colour: 200,
  },

  // -- sensores -----------------------------------------------------
  {
    type: 'p3d_tecla',
    message0: 'tecla %1 pulsada',
    args0: [{ type: 'field_dropdown', name: 'TECLA', options: [
      ['izquierda', 'izquierda'], ['derecha', 'derecha'],
      ['arriba', 'arriba'], ['abajo', 'abajo'],
      ['espacio', 'ESPACIO'],
    ] }],
    output: 'Boolean', colour: 210,
  },
  {
    type: 'p3d_colisiona',
    message0: '%1 toca a %2',
    args0: [
      { type: 'field_input', name: 'A', text: 'cubo' },
      { type: 'field_input', name: 'B', text: 'esfera' },
    ],
    output: 'Boolean', colour: 210,
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

registrar('p3d_tecla', function (block) {
  var tecla = block.getFieldValue('TECLA');
  var expr = tecla === 'ESPACIO' ?
    'pilas.control.simbolo(pilas.simbolos.ESPACIO)' :
    'pilas.control.' + tecla;
  return [expr, GEN.ORDER_ATOMIC];
});

registrar('p3d_colisiona', function (block) {
  return [sanea(block.getFieldValue('A')) +
          '.colisiona_en_plano_con(' +
          sanea(block.getFieldValue('B')) + ')',
          GEN.ORDER_ATOMIC];
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
      ] },
    { kind: 'category', name: 'Actores', colour: '290',
      contents: [
        { kind: 'block', type: 'p3d_crear_actor' },
        { kind: 'block', type: 'p3d_crear_modelo' },
        { kind: 'block', type: 'p3d_eliminar' },
      ] },
    { kind: 'category', name: 'Movimiento', colour: '160',
      contents: [
        { kind: 'block', type: 'p3d_mover' },
        { kind: 'block', type: 'p3d_ir_a' },
        { kind: 'block', type: 'p3d_girar' },
      ] },
    { kind: 'category', name: 'Apariencia', colour: '200',
      contents: [
        { kind: 'block', type: 'p3d_color' },
        { kind: 'block', type: 'p3d_texto' },
        { kind: 'block', type: 'p3d_decir' },
        { kind: 'block', type: 'p3d_animar' },
      ] },
    { kind: 'category', name: 'Sensores', colour: '210',
      contents: [
        { kind: 'block', type: 'p3d_tecla' },
        { kind: 'block', type: 'p3d_colisiona' },
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

// programa inicial de ejemplo
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
Blockly.Xml.domToWorkspace(Blockly.Xml.textToDom(INICIAL), ws);

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
  var e = EJEMPLOS[parseInt(selEjemplos.value, 10)];
  ws.clear();
  Blockly.Xml.domToWorkspace(Blockly.Xml.textToDom(e.xml), ws);
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
  if (!e.isUiEvent) regenerar();
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
