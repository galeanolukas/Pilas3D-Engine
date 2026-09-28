/* Ejemplos precargados para pilas3d-bloques.
 *
 * Cada entrada es un workspace de Blockly en XML: al elegirla del
 * menú se carga en el editor, se ve el armado en bloques y el
 * código Python que genera, listo para ejecutar con "Ejecutar".
 */

'use strict';

var EJEMPLOS = [

  {
    nombre: 'Hola cubo',
    xml:
      '<xml>' +
      '<block type="p3d_al_iniciar" x="30" y="30">' +
      '<statement name="HACER">' +
      '<block type="p3d_crear_actor">' +
      '<field name="TIPO">Cubo</field>' +
      '<field name="NOMBRE">cubo</field>' +
      '<next>' +
      '<block type="p3d_color">' +
      '<field name="NOMBRE">cubo</field>' +
      '<field name="COLOR">rojo</field>' +
      '<next>' +
      '<block type="p3d_texto">' +
      '<field name="TEXTO">hola, soy un cubo</field>' +
      '<field name="X">10</field><field name="Y">30</field>' +
      '</block></next>' +
      '</block></next>' +
      '</block></statement></block>' +
      '</xml>',
  },

  {
    nombre: 'Cubo girando',
    xml:
      '<xml>' +
      '<block type="p3d_al_iniciar" x="30" y="30">' +
      '<statement name="HACER">' +
      '<block type="p3d_crear_actor">' +
      '<field name="TIPO">Cubo</field>' +
      '<field name="NOMBRE">cubo</field>' +
      '</block></statement></block>' +
      '<block type="p3d_por_siempre" x="30" y="140">' +
      '<statement name="HACER">' +
      '<block type="p3d_girar">' +
      '<field name="NOMBRE">cubo</field>' +
      '<field name="EJE">rotacion_y</field>' +
      '<field name="N">3</field>' +
      '</block></statement></block>' +
      '</xml>',
  },

  {
    nombre: 'Mover con flechas',
    xml:
      '<xml>' +
      '<block type="p3d_al_iniciar" x="30" y="30">' +
      '<statement name="HACER">' +
      '<block type="p3d_crear_actor">' +
      '<field name="TIPO">Robot</field>' +
      '<field name="NOMBRE">robi</field>' +
      '</block></statement></block>' +

      '<block type="p3d_por_siempre" x="30" y="140">' +
      '<statement name="HACER">' +
      '<block type="controls_if">' +
      '<value name="IF0"><block type="p3d_tecla">' +
      '<field name="TECLA">izquierda</field></block></value>' +
      '<statement name="DO0"><block type="p3d_mover">' +
      '<field name="NOMBRE">robi</field>' +
      '<field name="EJE">x</field>' +
      '<field name="N">-0.08</field>' +
      '</block></statement>' +
      '<next>' +
      '<block type="controls_if">' +
      '<value name="IF0"><block type="p3d_tecla">' +
      '<field name="TECLA">derecha</field></block></value>' +
      '<statement name="DO0"><block type="p3d_mover">' +
      '<field name="NOMBRE">robi</field>' +
      '<field name="EJE">x</field>' +
      '<field name="N">0.08</field>' +
      '</block></statement>' +
      '<next>' +
      '<block type="controls_if">' +
      '<value name="IF0"><block type="p3d_tecla">' +
      '<field name="TECLA">arriba</field></block></value>' +
      '<statement name="DO0"><block type="p3d_mover">' +
      '<field name="NOMBRE">robi</field>' +
      '<field name="EJE">z</field>' +
      '<field name="N">-0.08</field>' +
      '</block></statement>' +
      '<next>' +
      '<block type="controls_if">' +
      '<value name="IF0"><block type="p3d_tecla">' +
      '<field name="TECLA">abajo</field></block></value>' +
      '<statement name="DO0"><block type="p3d_mover">' +
      '<field name="NOMBRE">robi</field>' +
      '<field name="EJE">z</field>' +
      '<field name="N">0.08</field>' +
      '</block></statement>' +
      '</block></next>' +
      '</block></next>' +
      '</block></next>' +
      '</block></statement></block>' +
      '</xml>',
  },

  {
    nombre: 'Choque entre actores',
    xml:
      '<xml>' +
      '<block type="p3d_al_iniciar" x="30" y="30">' +
      '<statement name="HACER">' +
      '<block type="p3d_crear_actor">' +
      '<field name="TIPO">Cubo</field>' +
      '<field name="NOMBRE">pelota</field>' +
      '<field name="X">-4</field>' +
      '<next>' +
      '<block type="p3d_crear_actor">' +
      '<field name="TIPO">Esfera</field>' +
      '<field name="NOMBRE">meta</field>' +
      '<field name="X">3</field>' +
      '<next>' +
      '<block type="p3d_color">' +
      '<field name="NOMBRE">meta</field>' +
      '<field name="COLOR">amarillo</field>' +
      '</block></next>' +
      '</block></next>' +
      '</block></statement></block>' +

      '<block type="p3d_por_siempre" x="30" y="200">' +
      '<statement name="HACER">' +
      '<block type="p3d_mover">' +
      '<field name="NOMBRE">pelota</field>' +
      '<field name="EJE">x</field>' +
      '<field name="N">0.05</field>' +
      '<next>' +
      '<block type="controls_if">' +
      '<value name="IF0"><block type="p3d_colisiona">' +
      '<field name="A">pelota</field><field name="B">meta</field>' +
      '</block></value>' +
      '<statement name="DO0"><block type="p3d_decir">' +
      '<field name="TEXTO">¡choqué con la meta!</field>' +
      '</block></statement>' +
      '</block></next>' +
      '</block></statement></block>' +
      '</xml>',
  },
];
