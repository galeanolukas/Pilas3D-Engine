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
  'p3d_menu': 'NOMBRE',
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

// idem pero "(nadie)" — para el objetivo opcional del cerebro.
function actores_o_nadie() {
  var ops = actores_opciones.call(this);
  if (ops.length === 1 && ops[0][1] === 'actor') ops = [];
  return [['(nadie)', '*']].concat(ops);
}

// tipos de cielo: 'estrellas'/'dia' son generados; el resto son
// texturas del paquete (pilas3d/data) que Cielo acepta como ruta.
var CIELOS = [
  ['estrellas (noche)', 'estrellas'], ['día con nubes', 'dia'],
  ['imagen mapa.png', 'mapa.png'], ['imagen piedra.png', 'piedra.png'],
];

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
    type: 'p3d_al_colisionar',
    message0: 'cuando %1 choque con %2 hacer %3',
    args0: [
      { type: 'field_dropdown', name: 'A', options: actores_opciones },
      { type: 'field_dropdown', name: 'B', options: actores_opciones },
      { type: 'input_statement', name: 'HACER' },
    ],
    colour: 45,
    tooltip: 'Corre cada vez que empiezan a tocarse',
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
  {
    type: 'p3d_al_entrar_zona',
    message0: 'cuando %1 entre a la zona %2 hacer %3',
    args0: [
      { type: 'field_dropdown', name: 'A', options: actores_opciones },
      { type: 'field_dropdown', name: 'B', options: actores_opciones },
      { type: 'input_statement', name: 'HACER' },
    ],
    colour: 45,
    tooltip: 'Corre una vez cada vez que el actor entra a la zona',
  },

  // -- juego: vida, zonas, comportamientos, partidas -----------------
  {
    type: 'p3d_vida',
    message0: 'darle %1 de vida a %2',
    args0: [
      { type: 'field_number', name: 'N', value: 100, min: 1 },
      { type: 'field_dropdown', name: 'NOMBRE',
        options: actores_opciones },
    ],
    previousStatement: null, nextStatement: null,
    colour: 80,
    tooltip: 'El actor gana vida/recibir_dano/curar/al_morir',
  },
  {
    type: 'p3d_danar',
    message0: '%1 a %2 en %3',
    args0: [
      { type: 'field_dropdown', name: 'QUE', options: [
        ['dañar', 'recibir_dano'], ['curar', 'curar'],
      ] },
      { type: 'field_dropdown', name: 'NOMBRE',
        options: actores_opciones },
      { type: 'field_number', name: 'N', value: 10 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 80,
  },
  {
    type: 'p3d_barra',
    message0: 'crear barra de vida para %1',
    args0: [{ type: 'field_dropdown', name: 'NOMBRE',
              options: actores_opciones }],
    previousStatement: null, nextStatement: null,
    colour: 80,
  },
  {
    type: 'p3d_patrullar',
    message0: 'que %1 patrulle los puntos %2 a velocidad %3',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE',
        options: actores_opciones },
      { type: 'field_input', name: 'PUNTOS', text: '(0,0),(4,0),(4,4)' },
      { type: 'field_number', name: 'VEL', value: 2, min: 0.1 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 80,
    tooltip: 'Puntos como (x,z),(x,z),… — recorre en loop',
  },
  {
    type: 'p3d_huir',
    message0: 'que %1 huya de %2 en radio %3 a velocidad %4',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE',
        options: actores_opciones },
      { type: 'field_dropdown', name: 'OBJ', options: actores_o_nadie },
      { type: 'field_number', name: 'RADIO', value: 5, min: 0.5 },
      { type: 'field_number', name: 'VEL', value: 3, min: 0.1 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 80,
  },
  {
    type: 'p3d_parpadeo',
    message0: 'que %1 parpadee intensidad %2 velocidad %3',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE',
        options: actores_opciones },
      { type: 'field_number', name: 'INT', value: 0.25, min: 0, max: 1 },
      { type: 'field_number', name: 'VEL', value: 8, min: 0.1 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 80,
    tooltip: 'Titila la luz de una lámpara como una llama',
  },
  {
    type: 'p3d_encender',
    message0: '%1 a %2',
    args0: [
      { type: 'field_dropdown', name: 'QUE', options: [
        ['encender', 'True'], ['apagar', 'False'],
      ] },
      { type: 'field_dropdown', name: 'NOMBRE',
        options: actores_opciones },
    ],
    previousStatement: null, nextStatement: null,
    colour: 80,
    tooltip: 'Enciende/apaga la luz de una lámpara',
  },
  {
    type: 'p3d_rebotar',
    message0: 'que %1 rebote entre x ±%2 z ±%3 a velocidad %4',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE',
        options: actores_opciones },
      { type: 'field_number', name: 'X', value: 6, min: 1 },
      { type: 'field_number', name: 'Z', value: 6, min: 1 },
      { type: 'field_number', name: 'VEL', value: 4, min: 0.1 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 80,
    tooltip: 'Rebota como logo de DVD dentro de esos límites',
  },
  {
    type: 'p3d_saltar',
    message0: 'que %1 pise plataformas y salte con ESPACIO (impulso %2)',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE',
        options: actores_opciones },
      { type: 'field_number', name: 'IMP', value: 9, min: 0 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 80,
    tooltip: 'Gravedad + salto con barra espaciadora',
  },
  {
    type: 'p3d_temblor',
    message0: 'sacudir la cámara intensidad %1 durante %2 s',
    args0: [
      { type: 'field_number', name: 'INT', value: 0.4, min: 0 },
      { type: 'field_number', name: 'SEG', value: 0.5, min: 0 },
    ],
    previousStatement: null, nextStatement: null,
    colour: 60,
  },
  {
    type: 'p3d_guardar',
    message0: 'guardar partida en %1',
    args0: [{ type: 'field_input', name: 'RUTA', text: 'partida.json' }],
    previousStatement: null, nextStatement: null,
    colour: 80,
  },
  {
    type: 'p3d_cargar',
    message0: 'cargar partida de %1',
    args0: [{ type: 'field_input', name: 'RUTA', text: 'partida.json' }],
    previousStatement: null, nextStatement: null,
    colour: 80,
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
        ['pared', 'Pared'], ['cartel', 'Cartel'], ['cielo', 'Cielo'],
        ['lámpara', 'Lampara'], ['zona', 'Zona'],
      ] },
      { type: 'field_input', name: 'NOMBRE', text: 'piso' },
    ],
    previousStatement: null, nextStatement: null,
    colour: 290,
    tooltip: 'Escenario: piso de grilla, ejes, plano, pared, cartel, cielo o lámpara',
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
    type: 'p3d_textura',
    message0: 'poner textura %1 a %2',
    args0: [
      { type: 'field_dropdown', name: 'TEXTURA', options: [
        ['caja', 'caja.png'], ['pasto', 'pasto.png'],
        ['piedra', 'piedra_media.png'], ['mapa', 'mapa.png'],
        ['moneda', 'moneda.png'], ['alien', 'alien.png'],
        ['fantasma', 'fantasma.png'], ['explosión', 'explosion.png'],
      ] },
      { type: 'field_dropdown', name: 'NOMBRE', options: actores_opciones },
    ],
    previousStatement: null, nextStatement: null,
    colour: 200,
    tooltip: 'Textura del paquete; en Python es actor.imagen = "x.png"',
  },
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
  // -- variables ------------------------------------------------------
  // se guardan en un dict global 'variables' — asi los callbacks no
  // necesitan 'global' para modificarlas (variables.get(k,0) no falla
  // si la variable todavia no se creo).

  {
    type: 'p3d_var_poner',
    message0: 'guardar %1 en la variable %2',
    args0: [
      { type: 'input_value', name: 'VALOR', check: 'Number' },
      { type: 'field_input', name: 'NOMBRE', text: 'puntos' },
    ],
    previousStatement: null, nextStatement: null,
    colour: 300,
    tooltip: 'Crea o pisa la variable con un valor',
  },
  {
    type: 'p3d_var_sumar',
    message0: 'sumar %1 a la variable %2',
    args0: [
      { type: 'input_value', name: 'VALOR', check: 'Number' },
      { type: 'field_input', name: 'NOMBRE', text: 'puntos' },
    ],
    previousStatement: null, nextStatement: null,
    colour: 300,
    tooltip: 'Le suma (o resta con negativos) a la variable',
  },
  {
    type: 'p3d_var',
    message0: 'variable %1',
    args0: [
      { type: 'field_input', name: 'NOMBRE', text: 'puntos' },
    ],
    output: 'Number',
    colour: 300,
    tooltip: 'El valor guardado en la variable (0 si no existe)',
  },
  {
    type: 'p3d_chat',
    message0: 'crear chat para hablar con %1 al pulsar %2',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE', options: actores_opciones },
      { type: 'field_dropdown', name: 'TECLA', options: [
        ['t', 't'], ['e', 'e'], ['q', 'q'],
        ['espacio', 'ESPACIO'], ['enter', 'ENTER'],
      ] },
    ],
    previousStatement: null, nextStatement: null,
    colour: 330,
  },
  {
    type: 'p3d_cielo',
    message0: 'poner el cielo %1 de %2',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE', options: actores_opciones },
      { type: 'field_dropdown', name: 'TIPO', options: CIELOS },
    ],
    previousStatement: null, nextStatement: null,
    colour: 200,
  },
  {
    type: 'p3d_cerebro',
    message0: 'darle cerebro a %1 que piensa cada %2 s ' +
             'con personalidad %3 y de objetivo %4',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE', options: actores_opciones },
      { type: 'field_number', name: 'CADA', value: 3, min: 0.5 },
      { type: 'field_input', name: 'PERSONA',
        text: 'sos un npc amigable' },
      { type: 'field_dropdown', name: 'OBJ', options: actores_o_nadie },
    ],
    previousStatement: null, nextStatement: null,
    colour: 330,
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
  {
    type: 'p3d_menu',
    message0: 'crear menú %1 titulado %2 con %3',
    args0: [
      { type: 'field_input', name: 'NOMBRE', text: 'menu' },
      { type: 'field_input', name: 'TITULO', text: 'MI JUEGO' },
      { type: 'input_statement', name: 'OPCIONES' },
    ],
    previousStatement: null, nextStatement: null,
    colour: 200,
    tooltip: 'Menú navegable con flechas+ENTER o mouse',
  },
  {
    type: 'p3d_menu_opcion',
    message0: 'opción %1 hacer %2',
    args0: [
      { type: 'field_input', name: 'TEXTO', text: 'Jugar' },
      { type: 'input_statement', name: 'HACER' },
    ],
    previousStatement: null, nextStatement: null,
    colour: 200,
    tooltip: 'Una opción del menú (solo dentro de "crear menú")',
  },
  {
    type: 'p3d_menu_estilo',
    message0: 'estilo: centrado %1 pantalla completa %2 sonidos %3',
    args0: [
      { type: 'field_checkbox', name: 'CENTRADO', checked: true },
      { type: 'field_checkbox', name: 'COMPLETA', checked: false },
      { type: 'field_checkbox', name: 'SONIDOS', checked: true },
    ],
    message1: 'fondo %1 transparencia %2 %% imagen %3',
    args1: [
      { type: 'field_dropdown', name: 'FONDO', options: [
        ['sin color', ''], ['negro', '0, 0, 0'],
        ['blanco', '255, 255, 255'], ['azul oscuro', '10, 20, 40'],
        ['gris', '120, 120, 120'],
      ] },
      { type: 'field_number', name: 'ALFA', value: 50,
        min: 0, max: 100 },
      { type: 'field_input', name: 'IMAGEN', text: '' },
    ],
    previousStatement: null, nextStatement: null,
    colour: 200,
    tooltip: 'Presentación del menú (dentro de "crear menú"): ' +
             'panel de color transparente, imagen de fondo, ' +
             'centrado, pantalla completa y efectos de audio',
  },

  // -- tiempo -------------------------------------------------------
  {
    type: 'p3d_interpolar',
    message0: 'llevar %1 suave a x %2 y %3 z %4 en %5 s %6',
    args0: [
      { type: 'field_dropdown', name: 'NOMBRE', options: actores_opciones },
      { type: 'field_number', name: 'X', value: 0 },
      { type: 'field_number', name: 'Y', value: 0 },
      { type: 'field_number', name: 'Z', value: 0 },
      { type: 'field_number', name: 'SEG', value: 2, min: 0 },
      { type: 'field_dropdown', name: 'TIPO', options: [
        ['normal', 'Lineal'],
        ['suave al arrancar', 'AceleracionGradual'],
        ['suave al frenar', 'DesaceleracionGradual'],
        ['con rebote al final', 'ReboteFinal'],
        ['con rebote al inicio', 'ReboteInicial'],
        ['elástica al final', 'ElasticoFinal'],
        ['elástica al inicio', 'ElasticoInicial'],
      ] },
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

registrar('p3d_al_colisionar', function (block) {
  var fn = nombre_unico('al_chocar');
  var dentro = GEN.statementToCode(block, 'HACER') ||
      GEN.INDENT + 'pass\n';
  // solo registra la vigilancia si ambos actores existen de verdad —
  // si falta alguno, la función queda pero no se conecta (avisa).
  var creados = nombres_creados(block);
  var a = campo_nombre(block, 'A');
  var b = campo_nombre(block, 'B');
  var reg = (creados.indexOf(a) >= 0 && creados.indexOf(b) >= 0)
    ? 'pilas.colisiones.cuando_colisionan(' + a + ', ' + b +
      ', ' + fn + ')\n'
    : '# al_chocar: falta crear alguno de los actores (' +
      a + ', ' + b + ')\n';
  return 'def ' + fn + '():\n' + globales(block) + dentro + reg + '\n';
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

registrar('p3d_al_entrar_zona', function (block) {
  var fn = nombre_unico('al_entrar');
  var dentro = GEN.statementToCode(block, 'HACER') ||
      GEN.INDENT + 'pass\n';
  var creados = nombres_creados(block);
  var a = campo_nombre(block, 'A');
  var b = campo_nombre(block, 'B');
  var reg = (creados.indexOf(a) >= 0 && creados.indexOf(b) >= 0)
    ? b + '.cuando_entra(' + a + ', ' + fn + ')\n'
    : '# al_entrar: falta crear alguno de los actores (' +
      a + ', ' + b + ')\n';
  return 'def ' + fn + '():\n' + globales(block) + dentro + reg + '\n';
});

// -- juego ---------------------------------------------------------------

registrar('p3d_vida', function (block) {
  return campo_nombre(block) +
         '.aprender(pilas.habilidades.Vida, vida=' +
         block.getFieldValue('N') + ')\n';
});

registrar('p3d_danar', function (block) {
  return campo_nombre(block) + '.' + block.getFieldValue('QUE') +
         '(' + block.getFieldValue('N') + ')\n';
});

registrar('p3d_barra', function (block) {
  return 'pilas.actores.Barra(de=' + campo_nombre(block) + ')\n';
});

registrar('p3d_patrullar', function (block) {
  var puntos = block.getFieldValue('PUNTOS').trim();
  return campo_nombre(block) +
         '.aprender(pilas.habilidades.Patrullar, puntos=[' +
         puntos + '], velocidad=' + block.getFieldValue('VEL') +
         ')\n';
});

registrar('p3d_huir', function (block) {
  var obj = block.getFieldValue('OBJ');
  var args = 'radio=' + block.getFieldValue('RADIO') +
             ', velocidad=' + block.getFieldValue('VEL');
  if (obj && obj !== '*' &&
      nombres_creados(block).indexOf(sanea(obj)) >= 0)
    return campo_nombre(block) +
           '.aprender(pilas.habilidades.HuirDe, ' + sanea(obj) +
           ', ' + args + ')\n';
  return '# huir: falta crear el actor objetivo\n';
});

registrar('p3d_parpadeo', function (block) {
  return campo_nombre(block) +
         '.aprender(pilas.habilidades.Parpadear, intensidad=' +
         block.getFieldValue('INT') + ', velocidad=' +
         block.getFieldValue('VEL') + ')\n';
});

registrar('p3d_encender', function (block) {
  return campo_nombre(block) + '.encendida = ' +
         block.getFieldValue('QUE') + '\n';
});

registrar('p3d_rebotar', function (block) {
  var x = block.getFieldValue('X');
  var z = block.getFieldValue('Z');
  var v = block.getFieldValue('VEL');
  return campo_nombre(block) +
         '.aprender(pilas.habilidades.RebotaEnParedes, vx=' + v +
         ', vz=' + v + ', limites=(-' + x + ', ' + x + ', -' + z +
         ', ' + z + '))\n';
});

registrar('p3d_saltar', function (block) {
  return campo_nombre(block) +
         '.aprender(pilas.habilidades.PisaPlataformas, salto=' +
         block.getFieldValue('IMP') + ')\n';
});

registrar('p3d_temblor', function (block) {
  return 'pilas.camara.temblor(' + block.getFieldValue('INT') +
         ', ' + block.getFieldValue('SEG') + ')\n';
});

registrar('p3d_guardar', function (block) {
  return 'pilas.guardar_partida(' +
         GEN.quote_(block.getFieldValue('RUTA')) + ')\n';
});

registrar('p3d_cargar', function (block) {
  return 'pilas.cargar_partida(' +
         GEN.quote_(block.getFieldValue('RUTA')) + ')\n';
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

registrar('p3d_textura', function (block) {
  return campo_nombre(block) + '.imagen = ' +
         GEN.quote_(block.getFieldValue('TEXTURA')) + '\n';
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

registrar('p3d_cerebro', function (block) {
  var obj = block.getFieldValue('OBJ');
  var args = 'cada=' + (block.getFieldValue('CADA') || 3) +
             ', personalidad=' +
             GEN.quote_(block.getFieldValue('PERSONA'));
  // el objetivo solo se emite si es un actor creado de verdad —
  // evita NameError si el XML quedó con un nombre viejo.
  if (obj && obj !== '*' &&
      nombres_creados(block).indexOf(sanea(obj)) >= 0)
    args += ', objetivo=' + sanea(obj);
  return campo_nombre(block) +
         '.aprender(pilas.habilidades.Cerebro, ' + args + ')\n';
});

function var_definicion() {
  // inyecta 'variables = {}' una sola vez al tope del programa
  GEN.definitions_['variables'] = 'variables = {}';
}

registrar('p3d_var_poner', function (block) {
  var_definicion();
  var v = GEN.valueToCode(block, 'VALOR', GEN.ORDER_NONE) || '0';
  return 'variables[' +
         GEN.quote_(sanea(block.getFieldValue('NOMBRE'))) +
         '] = ' + v + '\n';
});

registrar('p3d_var_sumar', function (block) {
  var_definicion();
  var n = sanea(block.getFieldValue('NOMBRE'));
  var v = GEN.valueToCode(block, 'VALOR', GEN.ORDER_NONE) || '0';
  return 'variables[' + GEN.quote_(n) + '] = variables.get(' +
         GEN.quote_(n) + ', 0) + ' + v + '\n';
});

registrar('p3d_var', function (block) {
  var_definicion();
  return ['variables.get(' +
          GEN.quote_(sanea(block.getFieldValue('NOMBRE'))) +
          ', 0)', GEN.ORDER_NONE];
});

registrar('p3d_chat', function (block) {
  return 'pilas.actores.Chat(' + campo_nombre(block) +
         ', tecla=pilas.simbolos.' +
         block.getFieldValue('TECLA') + ')\n';
});

registrar('p3d_cielo', function (block) {
  return campo_nombre(block) + '.tipo = ' +
         GEN.quote_(block.getFieldValue('TIPO')) + '\n';
});

registrar('p3d_sonido', function (block) {
  return 'pilas.sonidos.cargar(' +
         GEN.quote_(block.getFieldValue('RUTA')) + ').reproducir()\n';
});

// la opción sola no emite código: el menú padre la convierte en una
// función + una entrada ('texto', fn). Lo mismo el bloque de estilo.
registrar('p3d_menu_opcion', function (block) {
  return '';
});

registrar('p3d_menu_estilo', function (block) {
  return '# el bloque "estilo" va dentro de "crear menú"\n';
});

registrar('p3d_menu', function (block) {
  var fns = '';
  var ops = [];
  var b = block.getInputTargetBlock('OPCIONES');
  var extra = [];
  while (b) {
    if (b.type === 'p3d_menu_opcion') {
      var fn = nombre_unico('opcion');
      fns += 'def ' + fn + '():\n' + globales(block) +
             (GEN.statementToCode(b, 'HACER') || GEN.INDENT + 'pass\n');
      ops.push('(' + GEN.quote_(b.getFieldValue('TEXTO')) +
               ', ' + fn + ')');
    } else if (b.type === 'p3d_menu_estilo' && !extra.length) {
      if (b.getFieldValue('CENTRADO') === 'TRUE') {
        extra.push('centrado=True');
      }
      if (b.getFieldValue('COMPLETA') === 'TRUE') {
        extra.push('pantalla_completa=True');
      }
      if (b.getFieldValue('SONIDOS') === 'TRUE') {
        extra.push('sonido_mover=True', 'sonido_elegir=True');
      }
      var fondo = b.getFieldValue('FONDO');
      if (fondo) {
        var alfa = Math.round(Number(b.getFieldValue('ALFA'))
                             * 2.55);
        extra.push('fondo=(' + fondo + ', ' + alfa + ')');
      }
      var imagen = (b.getFieldValue('IMAGEN') || '').trim();
      if (imagen) {
        extra.push('fondo_imagen=' + GEN.quote_(imagen));
      }
    }
    b = b.getNextBlock();
  }
  return fns + campo_nombre(block) + ' = pilas.actores.Menu(titulo=' +
         GEN.quote_(block.getFieldValue('TITULO')) +
         ', opciones=[' + ops.join(', ') + ']' +
         (extra.length ? ', ' + extra.join(', ') : '') + ')\n';
});

registrar('p3d_interpolar', function (block) {
  var n = campo_nombre(block);
  var d = block.getFieldValue('SEG');
  var tipo = block.getFieldValue('TIPO');
  var t = tipo === 'Lineal' ? '' :
      ', tipo=pilas.interpolaciones.' + tipo;
  return 'pilas.interpolar(' + n + ", 'x', " +
         block.getFieldValue('X') + ', duracion=' + d + t + ')\n' +
         'pilas.interpolar(' + n + ", 'y', " +
         block.getFieldValue('Y') + ', duracion=' + d + t + ')\n' +
         'pilas.interpolar(' + n + ", 'z', " +
         block.getFieldValue('Z') + ', duracion=' + d + t + ')\n';
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
  return 'pilas.camara.usar_control_orbital()\n';
});

registrar('p3d_camara_seguir', function (block) {
  return 'pilas.camara.seguir_a(' +
         campo_nombre(block) + ", modo='" +
         block.getFieldValue('MODO') + "')\n";
});

registrar('p3d_camara_libre', function (block) {
  return 'pilas.camara.dejar_de_seguir()\n';
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
        { kind: 'block', type: 'p3d_al_colisionar' },
        { kind: 'block', type: 'p3d_al_entrar_zona' },
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
        { kind: 'block', type: 'p3d_textura' },
        { kind: 'block', type: 'p3d_cielo' },
        { kind: 'block', type: 'p3d_texto' },
        { kind: 'block', type: 'p3d_decir' },
        { kind: 'block', type: 'p3d_globo' },
        { kind: 'block', type: 'p3d_animar' },
        { kind: 'block', type: 'p3d_sonido' },
        { kind: 'block', type: 'p3d_menu' },
        { kind: 'block', type: 'p3d_menu_opcion' },
        { kind: 'block', type: 'p3d_menu_estilo' },
      ] },
    { kind: 'category', name: 'Tiempo', colour: '20',
      contents: [
        { kind: 'block', type: 'p3d_interpolar' },
        { kind: 'block', type: 'p3d_esperar' },
        { kind: 'block', type: 'p3d_cada' },
      ] },
    { kind: 'category', name: 'Juego', colour: '80',
      contents: [
        { kind: 'block', type: 'p3d_vida' },
        { kind: 'block', type: 'p3d_danar' },
        { kind: 'block', type: 'p3d_barra' },
        { kind: 'block', type: 'p3d_patrullar' },
        { kind: 'block', type: 'p3d_huir' },
        { kind: 'block', type: 'p3d_parpadeo' },
        { kind: 'block', type: 'p3d_encender' },
        { kind: 'block', type: 'p3d_rebotar' },
        { kind: 'block', type: 'p3d_saltar' },
        { kind: 'block', type: 'p3d_guardar' },
        { kind: 'block', type: 'p3d_cargar' },
      ] },
    { kind: 'category', name: 'Cámara', colour: '60',
      contents: [
        { kind: 'block', type: 'p3d_camara_orbital' },
        { kind: 'block', type: 'p3d_camara_seguir' },
        { kind: 'block', type: 'p3d_camara_libre' },
        { kind: 'block', type: 'p3d_temblor' },
      ] },
    { kind: 'category', name: 'IA', colour: '330',
      contents: [
        { kind: 'block', type: 'p3d_cerebro' },
        { kind: 'block', type: 'p3d_chat' },
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
    { kind: 'category', name: 'Variables', colour: '300',
      contents: [
        { kind: 'block', type: 'p3d_var_poner' },
        { kind: 'block', type: 'p3d_var_sumar' },
        { kind: 'block', type: 'p3d_var' },
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

document.getElementById('nuevo').onclick = function () {
  // el autosave pisa lo anterior al limpiar: por eso se confirma
  if (confirm('¿Empezar un proyecto nuevo? Se borran los bloques ' +
              'actuales (guardá antes si los querés conservar).')) {
    cargar_xml(INICIAL);
  }
};

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
