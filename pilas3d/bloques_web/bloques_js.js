/* pilas3d bloques → JavaScript: generadores para exportar a web.
 *
 * Genera JS sobre el mini-runtime pilas3d_web.js (subset educativo
 * del motor). Lo que el runtime no soporta (glTF, IA, física,
 * texturas externas) sale como comentario en el código exportado,
 * igual que avisan los generadores Python cuando falta algo.
 *
 * Reutiliza los helpers de bloques.js (sanea, campo_nombre,
 * nombres_creados, globales no aplica: en JS son vars globales).
 */
'use strict';

var JSGEN = Blockly.JavaScript &&
            (Blockly.JavaScript.javascriptGenerator ||
             Blockly.JavaScript);

var _contador_fn_js = 0;
var _js_init_real = JSGEN.init;
if (_js_init_real) {
  JSGEN.init = function (workspace) {
    _contador_fn_js = 0;
    _js_init_real.call(JSGEN, workspace);
  };
}
function nombre_unico_js(base) {
  return base + '_' + (_contador_fn_js++);
}

function registrar_js(tipo, fn) {
  JSGEN[tipo] = fn;
  if (JSGEN.forBlock) JSGEN.forBlock[tipo] = fn;
}

// actores cuyo tipo no existe en el runtime web: se exportan como
// cubo con un comentario que explica la sustitución.
var SUSTITUTOS = {
  Robot: ['Cubo', 'el robot aún no existe en web: sale un cubo'],
  Humanoide: ['Cubo', 'el humanoide aún no existe en web: sale un cubo'],
  Mono: ['Cubo', 'el mono aún no existe en web: sale un cubo'],
  Arania: ['Cubo', 'la araña aún no existe en web: sale un cubo'],
  Espectro: ['Cubo', 'el espectro aún no existe en web: sale un cubo'],
  Cartel: ['Pared', 'el cartel aún no existe en web: sale una pared'],
};

function cuerpo_js(block) {
  return JSGEN.statementToCode(block, 'HACER') ||
         JSGEN.INDENT + '\n';
}

// -- eventos ------------------------------------------------------------

registrar_js('p3d_al_iniciar', function (block) {
  return 'function iniciar() {\n' + cuerpo_js(block) +
         '}\niniciar();\n\n';
});

registrar_js('p3d_por_siempre', function (block) {
  return 'function siempre() {\n' + cuerpo_js(block) +
         '}\npilas.tareas.siempre(0, siempre);\n\n';
});

registrar_js('p3d_al_click', function (block) {
  var fn = nombre_unico_js('al_click');
  var donde = block.getFieldValue('DONDE');
  var dentro = JSGEN.statementToCode(block, 'HACER') ||
      JSGEN.INDENT + '\n';
  if (donde !== '*') {
    dentro = JSGEN.INDENT + 'if (actor === ' + sanea(donde) + ') {\n' +
             JSGEN.prefixLines(dentro, JSGEN.INDENT) +
             JSGEN.INDENT + '}\n';
  }
  return 'function ' + fn + '(actor, punto) {\n' + dentro + '}\n' +
         'pilas.cuando_hace_click(' + fn + ');\n\n';
});

registrar_js('p3d_al_colisionar', function (block) {
  var fn = nombre_unico_js('al_chocar');
  var dentro = JSGEN.statementToCode(block, 'HACER') ||
      JSGEN.INDENT + '\n';
  var creados = nombres_creados(block);
  var a = campo_nombre(block, 'A');
  var b = campo_nombre(block, 'B');
  var reg = (creados.indexOf(a) >= 0 && creados.indexOf(b) >= 0)
    ? 'pilas.colisiones.cuando_colisionan(' + a + ', ' + b + ', ' +
      fn + ');\n'
    : '// al_chocar: falta crear alguno de los actores (' + a + ', ' +
      b + ')\n';
  return 'function ' + fn + '() {\n' + dentro + '}\n' + reg + '\n';
});

registrar_js('p3d_al_pulsar', function (block) {
  var fn = nombre_unico_js('al_pulsar');
  var dentro = JSGEN.statementToCode(block, 'HACER') ||
      JSGEN.INDENT + '\n';
  var tecla = block.getFieldValue('TECLA');
  return 'function ' + fn + '() {\n' + dentro + '}\n' +
         'pilas.al_pulsar(pilas.simbolos.' + tecla + ', ' + fn +
         ');\n\n';
});

registrar_js('p3d_al_entrar_zona', function (block) {
  var fn = nombre_unico_js('al_entrar');
  var dentro = JSGEN.statementToCode(block, 'HACER') ||
      JSGEN.INDENT + '\n';
  var creados = nombres_creados(block);
  var a = campo_nombre(block, 'A');
  var b = campo_nombre(block, 'B');
  var reg = (creados.indexOf(a) >= 0 && creados.indexOf(b) >= 0)
    ? b + '.cuando_entra(' + a + ', ' + fn + ');\n'
    : '// al_entrar: falta crear alguno de los actores (' + a + ', ' +
      b + ')\n';
  return 'function ' + fn + '() {\n' + dentro + '}\n' + reg + '\n';
});

// -- juego ----------------------------------------------------------------

registrar_js('p3d_vida', function (block) {
  return campo_nombre(block) + ".aprender('Vida', {vida: " +
         block.getFieldValue('N') + '});\n';
});

registrar_js('p3d_danar', function (block) {
  return campo_nombre(block) + '.' +
         (block.getFieldValue('QUE') === 'curar' ? 'curar' :
          'recibir_dano') + '(' + block.getFieldValue('N') + ');\n';
});

registrar_js('p3d_barra', function (block) {
  return 'pilas.actores.Barra({de: ' + campo_nombre(block) + '});\n';
});

registrar_js('p3d_patrullar', function (block) {
  // "(0,0),(4,0)" -> [[0,0],[4,0]]
  var pts = (block.getFieldValue('PUNTOS') || '')
    .match(/\([^)]*\)/g) || [];
  var arr = pts.map(function (p) {
    return '[' + p.slice(1, -1) + ']';
  }).join(', ');
  return campo_nombre(block) + ".aprender('Patrullar', {puntos: [" +
         arr + '], velocidad: ' + block.getFieldValue('VEL') + '});\n';
});

registrar_js('p3d_huir', function (block) {
  var obj = block.getFieldValue('OBJ');
  if (obj && obj !== '*' &&
      nombres_creados(block).indexOf(sanea(obj)) >= 0)
    return campo_nombre(block) + ".aprender('HuirDe', {objetivo: " +
           sanea(obj) + ', radio: ' + block.getFieldValue('RADIO') +
           ', velocidad: ' + block.getFieldValue('VEL') + '});\n';
  return '// huir: falta crear el actor objetivo\n';
});

registrar_js('p3d_parpadeo', function (block) {
  return campo_nombre(block) + ".aprender('Parpadear', {intensidad: " +
         block.getFieldValue('INT') + ', velocidad: ' +
         block.getFieldValue('VEL') + '});\n';
});

registrar_js('p3d_encender', function (block) {
  // el dropdown trae 'True'/'False' (Python): en JS van en minúscula
  var v = block.getFieldValue('QUE') === 'True' ? 'true' : 'false';
  return campo_nombre(block) + '.encendida = ' + v + ';\n';
});

registrar_js('p3d_rebotar', function (block) {
  var x = block.getFieldValue('X'), z = block.getFieldValue('Z'),
      v = block.getFieldValue('VEL');
  return campo_nombre(block) +
         ".aprender('RebotaEnParedes', {vx: " + v + ', vz: ' + v +
         ', limites: [' + (-x) + ', ' + x + ', ' + (-z) + ', ' + z +
         ']});\n';
});

registrar_js('p3d_saltar', function (block) {
  return campo_nombre(block) +
         ".aprender('PisaPlataformas', {salto: " +
         block.getFieldValue('IMP') + '});\n';
});

registrar_js('p3d_temblor', function (block) {
  return 'pilas.camara.temblor(' + block.getFieldValue('INT') +
         ', ' + block.getFieldValue('SEG') + ');\n';
});

registrar_js('p3d_guardar', function (block) {
  return 'pilas.guardar_partida(' +
         JSGEN.quote_(block.getFieldValue('RUTA')) + ');\n';
});

registrar_js('p3d_cargar', function (block) {
  return 'pilas.cargar_partida(' +
         JSGEN.quote_(block.getFieldValue('RUTA')) + ');\n';
});

// -- actores --------------------------------------------------------------

registrar_js('p3d_crear_actor', function (block) {
  var tipo = block.getFieldValue('TIPO');
  var extra = '';
  if (SUSTITUTOS[tipo]) {
    extra = '// ' + SUSTITUTOS[tipo][1] + '\n';
    tipo = SUSTITUTOS[tipo][0];
  }
  return extra + campo_nombre(block) + ' = pilas.actores.' + tipo +
         '({x: ' + block.getFieldValue('X') +
         ', y: ' + block.getFieldValue('Y') +
         ', z: ' + block.getFieldValue('Z') + '});\n';
});

registrar_js('p3d_crear_modelo', function (block) {
  return '// los modelos .glb no se exportan a web todavía: ' +
         JSGEN.quote_(block.getFieldValue('RUTA')) + '\n';
});

registrar_js('p3d_crear_escenario', function (block) {
  var tipo = block.getFieldValue('TIPO');
  var extra = '';
  if (SUSTITUTOS[tipo]) {
    extra = '// ' + SUSTITUTOS[tipo][1] + '\n';
    tipo = SUSTITUTOS[tipo][0];
  }
  return extra + campo_nombre(block) + ' = pilas.actores.' + tipo +
         '();\n';
});

registrar_js('p3d_lampara', function (block) {
  // en web no hay luces puntuales: el foco se ve igual (encender la
  // atenúa), pero el "alcance" no cambia la escena
  var extra = '// en web la lámpara se ve pero no alumbra de verdad\n';
  return extra + campo_nombre(block) + ' = pilas.actores.Lampara(' +
         '{x: ' + block.getFieldValue('X') +
         ', y: ' + block.getFieldValue('Y') +
         ', z: ' + block.getFieldValue('Z') + '});\n';
});

registrar_js('p3d_terreno', function (block) {
  return campo_nombre(block) + ' = pilas.actores.Terreno({celdas: ' +
         block.getFieldValue('CELX') + '});\n';
});

registrar_js('p3d_terreno_forma', function (block) {
  var n = campo_nombre(block);
  var forma = block.getFieldValue('FORMA');
  var i = block.getFieldValue('I'), k = block.getFieldValue('K');
  var radio = block.getFieldValue('RADIO'), v = block.getFieldValue('N');
  if (forma === 'montana' || forma === 'pozo')
    return n + '.' + forma + '(' + i + ', ' + k + ', ' + radio + ', ' +
           v + ');\n';
  return n + '.' + forma + '(' + i + ', ' + k + ', ' + v + ');\n';
});

registrar_js('p3d_terreno_pintar', function (block) {
  return campo_nombre(block) + '.pintar_zona(' +
         block.getFieldValue('I') + ', ' + block.getFieldValue('K') +
         ', ' + block.getFieldValue('RADIO') + ', ' +
         JSGEN.quote_(block.getFieldValue('TIPO')) + ');\n';
});

registrar_js('p3d_terreno_agua', function (block) {
  if (block.getFieldValue('QUE') === 'sacar')
    return campo_nombre(block) + '.agua = null;\n';
  return campo_nombre(block) + '.agua = ' + block.getFieldValue('N') +
         ';\n';
});

registrar_js('p3d_eliminar', function (block) {
  return campo_nombre(block) + '.eliminar();\n';
});

// -- movimiento -----------------------------------------------------------

registrar_js('p3d_mover', function (block) {
  return campo_nombre(block) + '.' + block.getFieldValue('EJE') +
         ' += ' + block.getFieldValue('N') + ';\n';
});

registrar_js('p3d_ir_a', function (block) {
  var n = campo_nombre(block);
  return n + '.x = ' + block.getFieldValue('X') + ';\n' +
         n + '.y = ' + block.getFieldValue('Y') + ';\n' +
         n + '.z = ' + block.getFieldValue('Z') + ';\n';
});

registrar_js('p3d_ir_al_azar', function (block) {
  var n = campo_nombre(block);
  var mn = block.getFieldValue('MIN'), mx = block.getFieldValue('MAX');
  var r = '(Math.random() * (' + mx + ' - (' + mn + ')) + (' + mn +
          '))';
  return n + '.x = ' + r + ';\n' + n + '.z = ' + r + ';\n';
});

registrar_js('p3d_girar', function (block) {
  return campo_nombre(block) + '.' + block.getFieldValue('EJE') +
         ' += ' + block.getFieldValue('N') + ';\n';
});

registrar_js('p3d_escala', function (block) {
  return campo_nombre(block) + '.escala ' +
         block.getFieldValue('QUE') + ' ' +
         block.getFieldValue('N') + ';\n';
});

// -- apariencia -----------------------------------------------------------

registrar_js('p3d_textura', function (block) {
  return '// texturas externas no viajan en el .html exportado (' +
         block.getFieldValue('TEXTURA') + ')\n';
});

registrar_js('p3d_color', function (block) {
  return campo_nombre(block) + '.color = pilas.colores.' +
         block.getFieldValue('COLOR') + ';\n';
});

registrar_js('p3d_texto', function (block) {
  return 'pilas.actores.Texto(' +
         JSGEN.quote_(block.getFieldValue('TEXTO')) +
         ', ' + block.getFieldValue('X') +
         ', ' + block.getFieldValue('Y') + ');\n';
});

registrar_js('p3d_decir', function (block) {
  return 'pilas.print(' +
         JSGEN.quote_(block.getFieldValue('TEXTO')) + ');\n';
});

registrar_js('p3d_animar', function (block) {
  return '// animar() no existe en el runtime web (' +
         JSGEN.quote_(block.getFieldValue('ANIM')) + ')\n';
});

registrar_js('p3d_globo', function (block) {
  return campo_nombre(block) + '.decir(' +
         JSGEN.quote_(block.getFieldValue('TEXTO')) +
         ', ' + block.getFieldValue('SEG') + ');\n';
});

// -- variables --------------------------------------------------------------
// el dict 'variables' de Python es un objeto JS — misma API de acceso.

function var_definicion_js() {
  JSGEN.definitions_['variables'] = 'var variables = {};';
}

registrar_js('p3d_var_poner', function (block) {
  var_definicion_js();
  var v = JSGEN.valueToCode(block, 'VALOR', JSGEN.ORDER_NONE) || '0';
  return 'variables[' +
         JSGEN.quote_(sanea(block.getFieldValue('NOMBRE'))) +
         '] = ' + v + ';\n';
});

registrar_js('p3d_var_sumar', function (block) {
  var_definicion_js();
  var n = JSGEN.quote_(sanea(block.getFieldValue('NOMBRE')));
  var v = JSGEN.valueToCode(block, 'VALOR', JSGEN.ORDER_NONE) || '0';
  return 'variables[' + n + '] = (variables[' + n + '] || 0) + ' +
         v + ';\n';
});

registrar_js('p3d_var', function (block) {
  var_definicion_js();
  return ['(variables[' +
          JSGEN.quote_(sanea(block.getFieldValue('NOMBRE'))) +
          '] || 0)', JSGEN.ORDER_ATOMIC];
});

// -- IA / red: no exportables ----------------------------------------------

registrar_js('p3d_chat', function () {
  return '// el chat con IA necesita Ollama: no corre en la web\n';
});

registrar_js('p3d_cerebro', function () {
  return '// el cerebro IA necesita Ollama: no corre en la web\n';
});

// -- varios -----------------------------------------------------------------

registrar_js('p3d_cielo', function (block) {
  var tipo = block.getFieldValue('TIPO');
  if (tipo !== 'estrellas' && tipo !== 'dia')
    return '// las imágenes de cielo no viajan en el .html (' +
           JSGEN.quote_(tipo) + ')\n';
  return campo_nombre(block) + '.tipo = ' +
         JSGEN.quote_(tipo) + ';\n';
});

registrar_js('p3d_sonido', function (block) {
  return '// el sonido suena si el archivo está junto al .html\n' +
         'pilas.sonidos.cargar(' +
         JSGEN.quote_(block.getFieldValue('RUTA')) +
         ').reproducir();\n';
});

registrar_js('p3d_menu_opcion', function () { return ''; });

registrar_js('p3d_menu_estilo', function () {
  return '// el bloque "estilo" va dentro de "crear menú"\n';
});

registrar_js('p3d_menu', function (block) {
  var fns = '', ops = [], extra = [];
  var b = block.getInputTargetBlock('OPCIONES');
  while (b) {
    if (b.type === 'p3d_menu_opcion') {
      var fn = nombre_unico_js('opcion');
      fns += 'function ' + fn + '() {\n' +
             (JSGEN.statementToCode(b, 'HACER') ||
              JSGEN.INDENT + '\n') + '}\n';
      ops.push('[' + JSGEN.quote_(b.getFieldValue('TEXTO')) +
               ', ' + fn + ']');
    } else if (b.type === 'p3d_menu_estilo' && !extra.length) {
      if (b.getFieldValue('COMPLETA') === 'TRUE') {
        extra.push('pantalla_completa: true');
      }
      var fondo = b.getFieldValue('FONDO');
      if (fondo) {
        var alfa = Math.round(Number(b.getFieldValue('ALFA')) * 2.55);
        extra.push('fondo: [' + fondo + ', ' + alfa + ']');
      }
    }
    b = b.getNextBlock();
  }
  return fns + campo_nombre(block) + ' = pilas.actores.Menu({titulo: ' +
         JSGEN.quote_(block.getFieldValue('TITULO')) +
         ', opciones: [' + ops.join(', ') + ']' +
         (extra.length ? ', ' + extra.join(', ') : '') + '});\n';
});

// -- tiempo -------------------------------------------------------------------

registrar_js('p3d_interpolar', function (block) {
  var n = campo_nombre(block);
  var d = block.getFieldValue('SEG');
  var tipo = JSGEN.quote_(block.getFieldValue('TIPO'));
  return ['x', 'y', 'z'].map(function (e) {
    return 'pilas.interpolar(' + n + ", '" + e + "', " +
           block.getFieldValue(e.toUpperCase()) + ', ' + d +
           ', ' + tipo + ');';
  }).join('\n') + '\n';
});

registrar_js('p3d_esperar', function (block) {
  var fn = nombre_unico_js('esperar');
  return 'function ' + fn + '() {\n' + cuerpo_js(block) + '}\n' +
         'pilas.tareas.una_vez(' + block.getFieldValue('SEG') +
         ', ' + fn + ');\n';
});

registrar_js('p3d_cada', function (block) {
  var fn = nombre_unico_js('repetir');
  return 'function ' + fn + '() {\n' + cuerpo_js(block) + '}\n' +
         'pilas.tareas.siempre(' + block.getFieldValue('SEG') +
         ', ' + fn + ');\n';
});

// -- cámara ---------------------------------------------------------------------

registrar_js('p3d_camara_orbital', function () {
  return 'pilas.camara.usar_control_orbital();\n';
});

registrar_js('p3d_camara_seguir', function (block) {
  return 'pilas.camara.seguir_a(' + campo_nombre(block) + ", '" +
         block.getFieldValue('MODO') + "');\n";
});

registrar_js('p3d_camara_libre', function () {
  return 'pilas.camara.dejar_de_seguir();\n';
});

// -- sensores ---------------------------------------------------------------------

registrar_js('p3d_tecla', function (block) {
  var tecla = block.getFieldValue('TECLA');
  var flechas = ['izquierda', 'derecha', 'arriba', 'abajo'];
  var expr = flechas.indexOf(tecla) >= 0 ?
    'pilas.control.' + tecla :
    'pilas.control.simbolo(' + JSGEN.quote_(tecla) + ')';
  return [expr, JSGEN.ORDER_ATOMIC];
});

registrar_js('p3d_colisiona', function (block) {
  return [sanea(block.getFieldValue('A')) +
          '.colisiona_en_plano_con(' +
          sanea(block.getFieldValue('B')) + ')',
          JSGEN.ORDER_ATOMIC];
});

registrar_js('p3d_boton_mouse', function (block) {
  return ['pilas.control.boton_' + block.getFieldValue('BOTON'),
          JSGEN.ORDER_ATOMIC];
});

registrar_js('p3d_mouse_x', function () {
  return ['pilas.control.mouse_x', JSGEN.ORDER_ATOMIC];
});

registrar_js('p3d_mouse_y', function () {
  return ['pilas.control.mouse_y', JSGEN.ORDER_ATOMIC];
});

// ------------------------------------------------------------------
// exportar: workspace JS -> .html autocontenido con el runtime
// ------------------------------------------------------------------

function generar_js() {
  // los actores creados son vars globales para que los handlers los
  // vean (en Python se usaba 'global'; acá va un var al tope)
  var nombres = ws.getAllBlocks(false)
    .filter(function (b) { return CREA_NOMBRE[b.type]; })
    .map(function (b) {
      return sanea(b.getFieldValue(CREA_NOMBRE[b.type]));
    });
  var codigo = JSGEN.workspaceToCode(ws);
  var vars = nombres.length ? 'var ' + nombres.join(', ') + ';\n' : '';
  return vars + 'function programa() {\n' + codigo + '}\n';
}

var PLANTILLA_HTML =
  '<!DOCTYPE html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n' +
  '<title>mi juego pilas3d</title>\n' +
  '</head>\n<body>\n<script>\n@@RUNTIME@@\n</script>\n<script>\n' +
  '// -- código generado por pilas3d-bloques --\n@@CODIGO@@\n' +
  '</script>\n</body>\n</html>\n';

function exportar_web() {
  var codigo;
  try {
    codigo = generar_js();
  } catch (e) {
    spanEstado.className = 'error';
    spanEstado.textContent = 'error generando: ' + e;
    return;
  }
  fetch('pilas3d_web.js').then(function (r) { return r.text(); })
    .then(function (runtime) {
      var html = PLANTILLA_HTML
        .replace('@@RUNTIME@@', runtime)
        .replace('@@CODIGO@@', codigo);
      var a = document.createElement('a');
      a.href = URL.createObjectURL(
        new Blob([html], { type: 'text/html' }));
      a.download = 'mi_juego.html';
      a.click();
      spanEstado.className = 'ok';
      spanEstado.textContent =
        'exportado: abrí mi_juego.html en cualquier navegador';
    }).catch(function () {
      spanEstado.className = 'error';
      spanEstado.textContent = 'no pude leer el runtime web';
    });
}

document.getElementById('exportar').onclick = exportar_web;
