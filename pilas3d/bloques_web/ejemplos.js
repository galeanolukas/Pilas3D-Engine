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

  // Un mini-juego completo: el mono se teletransporta cada 2
  // segundos y hay que clickearlo antes de que escape.
  {
    nombre: 'Cazá al mono',
    xml:
      '<xml>' +
      '<block type="p3d_al_iniciar" x="30" y="30">' +
      '<statement name="HACER">' +
      '<block type="p3d_crear_escenario">' +
      '<field name="TIPO">Piso</field><field name="NOMBRE">piso</field>' +
      '<next><block type="p3d_crear_actor">' +
      '<field name="TIPO">Mono</field><field name="NOMBRE">mono</field>' +
      '<next><block type="p3d_texto">' +
      '<field name="TEXTO">clickeá al mono antes de que escape</field>' +
      '<field name="X">10</field><field name="Y">30</field>' +
      '<next><block type="p3d_camara_orbital">' +
      '</block></next></block></next></block></next></block>' +
      '</statement></block>' +

      '<block type="p3d_cada" x="30" y="240">' +
      '<field name="SEG">2</field>' +
      '<statement name="HACER"><block type="p3d_ir_al_azar">' +
      '<field name="NOMBRE">mono</field>' +
      '<field name="MIN">-5</field><field name="MAX">5</field>' +
      '</block></statement></block>' +

      '<block type="p3d_al_click" x="30" y="340">' +
      '<field name="DONDE">mono</field>' +
      '<statement name="HACER"><block type="p3d_globo">' +
      '<field name="NOMBRE">mono</field>' +
      '<field name="TEXTO">¡me atrapaste!</field>' +
      '<field name="SEG">2</field>' +
      '<next><block type="p3d_sonido">' +
      '<field name="RUTA">tick.wav</field>' +
      '</block></next></block></statement></block>' +
      '</xml>',
  },

  // Otro mini-juego: mover la pelota con las flechas hasta la meta;
  // al tocarla vuelve al centro, suena y avisa con un globo.
  {
    nombre: 'Llegada a la meta',
    xml:
      '<xml>' +
      '<block type="p3d_al_iniciar" x="30" y="30">' +
      '<statement name="HACER">' +
      '<block type="p3d_crear_escenario">' +
      '<field name="TIPO">Piso</field><field name="NOMBRE">piso</field>' +
      '<next><block type="p3d_crear_actor">' +
      '<field name="TIPO">Esfera</field><field name="NOMBRE">pelota</field>' +
      '<field name="X">-6</field>' +
      '<next><block type="p3d_crear_actor">' +
      '<field name="TIPO">Cubo</field><field name="NOMBRE">meta</field>' +
      '<field name="X">6</field>' +
      '<next><block type="p3d_color">' +
      '<field name="NOMBRE">meta</field><field name="COLOR">amarillo</field>' +
      '<next><block type="p3d_camara_seguir">' +
      '<field name="NOMBRE">pelota</field>' +
      '<field name="MODO">tercera</field>' +
      '</block></next></block></next></block></next></block></next>' +
      '</block>' +
      '</statement></block>' +

      '<block type="p3d_por_siempre" x="30" y="300">' +
      '<statement name="HACER">' +
      '<block type="controls_if">' +
      '<value name="IF0"><block type="p3d_tecla">' +
      '<field name="TECLA">izquierda</field></block></value>' +
      '<statement name="DO0"><block type="p3d_mover">' +
      '<field name="NOMBRE">pelota</field><field name="EJE">x</field>' +
      '<field name="N">-0.1</field></block></statement>' +
      '<next><block type="controls_if">' +
      '<value name="IF0"><block type="p3d_tecla">' +
      '<field name="TECLA">derecha</field></block></value>' +
      '<statement name="DO0"><block type="p3d_mover">' +
      '<field name="NOMBRE">pelota</field><field name="EJE">x</field>' +
      '<field name="N">0.1</field></block></statement>' +
      '<next><block type="controls_if">' +
      '<value name="IF0"><block type="p3d_tecla">' +
      '<field name="TECLA">arriba</field></block></value>' +
      '<statement name="DO0"><block type="p3d_mover">' +
      '<field name="NOMBRE">pelota</field><field name="EJE">z</field>' +
      '<field name="N">-0.1</field></block></statement>' +
      '<next><block type="controls_if">' +
      '<value name="IF0"><block type="p3d_tecla">' +
      '<field name="TECLA">abajo</field></block></value>' +
      '<statement name="DO0"><block type="p3d_mover">' +
      '<field name="NOMBRE">pelota</field><field name="EJE">z</field>' +
      '<field name="N">0.1</field></block></statement>' +
      '<next><block type="controls_if">' +
      '<value name="IF0"><block type="p3d_colisiona">' +
      '<field name="A">pelota</field><field name="B">meta</field>' +
      '</block></value>' +
      '<statement name="DO0"><block type="p3d_ir_a">' +
      '<field name="NOMBRE">pelota</field>' +
      '<field name="X">-6</field><field name="Y">0</field>' +
      '<field name="Z">0</field>' +
      '<next><block type="p3d_sonido">' +
      '<field name="RUTA">tick.wav</field>' +
      '<next><block type="p3d_globo">' +
      '<field name="NOMBRE">pelota</field>' +
      '<field name="TEXTO">¡gol!</field><field name="SEG">2</field>' +
      '</block></next></block></next></block></statement>' +
      '</block></next></block></next></block></next></block></next>' +
      '</block></statement></block>' +
      '</xml>',
  },
  // Efectos de jugo: la moneda flota sola y al pulsar E el robot
  // hace el combo clásico — parpadeo + flash + hit-stop.
  {
    nombre: 'Efectos de jugo',
    xml:
      '<xml>' +
      '<block type="p3d_al_iniciar" x="30" y="30">' +
      '<statement name="HACER"><block type="p3d_crear_escenario">' +
      '<field name="TIPO">Piso</field><field name="NOMBRE">piso</field>' +
      '<next><block type="p3d_crear_actor">' +
      '<field name="TIPO">Robot</field><field name="NOMBRE">robi</field>' +
      '<next><block type="p3d_crear_actor">' +
      '<field name="TIPO">Esfera</field><field name="NOMBRE">moneda</field>' +
      '<field name="X">3</field><field name="Y">0.6</field>' +
      '<next><block type="p3d_color">' +
      '<field name="NOMBRE">moneda</field><field name="COLOR">amarillo</field>' +
      '<next><block type="p3d_ef_flotar">' +
      '<field name="NOMBRE">moneda</field><field name="ALT">0.4</field>' +
      '<next><block type="p3d_ef_estela">' +
      '<field name="NOMBRE">robi</field><field name="COLOR">celeste</field>' +
      '<next><block type="p3d_camara_orbital"></block>' +
      '</next></block></next></block></next></block></next></block>' +
      '</next></block></next></block></statement></block>' +

      '<block type="p3d_al_pulsar" x="30" y="260">' +
      '<field name="TECLA">e</field>' +
      '<statement name="HACER"><block type="p3d_ef_parpadear">' +
      '<field name="NOMBRE">robi</field>' +
      '<field name="VEC">6</field><field name="SEG">0.12</field>' +
      '<next><block type="p3d_ef_flash">' +
      '<field name="NOMBRE">robi</field><field name="COLOR">rojo</field>' +
      '<field name="SEG">0.15</field>' +
      '<next><block type="p3d_ef_hitstop">' +
      '<field name="SEG">0.08</field>' +
      '</block></next></block></next></block></statement></block>' +
      '</xml>',
  },

  {
    nombre: 'NPC con cerebro (IA)',
    xml:
      '<xml><block type="p3d_al_iniciar" x="30" y="30"><statement name="HACER"><block type="p3d_c' +
      'rear_escenario"><field name="TIPO">Piso</field><field name="NOMBRE">piso</field><next><blo' +
      'ck type="p3d_crear_escenario"><field name="TIPO">Cielo</field><field name="NOMBRE">cielo</' +
      'field><next><block type="p3d_cielo"><field name="NOMBRE">cielo</field><field name="TIPO">d' +
      'ia</field><next><block type="p3d_crear_actor"><field name="TIPO">Mono</field><field name="' +
      'NOMBRE">mono</field><field name="X">4</field><field name="Y">0</field><field name="Z">0</f' +
      'ield><next><block type="p3d_crear_actor"><field name="TIPO">Robot</field><field name="NOMB' +
      'RE">robi</field><field name="X">0</field><field name="Y">0</field><field name="Z">3</field' +
      '><next><block type="p3d_cerebro"><field name="NOMBRE">mono</field><field name="CADA">3</fi' +
      'eld><field name="PERSONA">sos un mono charlatan y jugueton; te gusta saludar y acercarte</' +
      'field><field name="OBJ">robi</field><next><block type="p3d_chat"><field name="NOMBRE">mono' +
      '</field><field name="TECLA">t</field><next><block type="p3d_texto"><field name="TEXTO">pul' +
      'sa T y hablale al mono</field><field name="X">10</field><field name="Y">30</field><next><b' +
      'lock type="p3d_camara_orbital"></block></next></block></next></block></next></block></next' +
      '></block></next></block></next></block></next></block></next></block></statement></block><' +
      '/xml>',
  },
];
