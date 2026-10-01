/* pilas3d web runtime v1 — subset educativo del motor sobre WebGL.
 *
 * Se embebe entero dentro del .html exportado: un programa de bloques
 * corre en cualquier navegador sin instalar nada.
 *
 * Cubre: primitivas (cubo/esfera/cilindro/cono/plano/pared/piso/ejes/
 * zona), color, movimiento/rotación/escala, tareas, teclas, mouse,
 * colisiones en plano, interpolaciones, cámara (orbital/seguir/temblor),
 * vida+barra, texto/globos/menú por DOM, sonido por <audio> si el
 * archivo existe junto al html. Lo que no existe (glTF, IA, física)
 * lo avisa el generador con un comentario en el código.
 */
'use strict';

var pilas = (function () {

  // -- mat4 mínimas (column-major como WebGL) -----------------------
  function mIdent() {
    return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  }
  function mMul(a, b) {
    var r = new Array(16);
    for (var c = 0; c < 4; c++)
      for (var f = 0; f < 4; f++) {
        var s = 0;
        for (var k = 0; k < 4; k++) s += a[k * 4 + f] * b[c * 4 + k];
        r[c * 4 + f] = s;
      }
    return r;
  }
  function mPerspectiva(fov, aspecto, cerca, lejos) {
    var t = 1 / Math.tan(fov / 2), d = 1 / (cerca - lejos);
    return [t / aspecto, 0, 0, 0,
            0, t, 0, 0,
            0, 0, (lejos + cerca) * d, -1,
            0, 0, 2 * lejos * cerca * d, 0];
  }
  function mLookAt(o, c, up) {
    var zx = o[0] - c[0], zy = o[1] - c[1], zz = o[2] - c[2];
    var l = Math.hypot(zx, zy, zz) || 1;
    zx /= l; zy /= l; zz /= l;
    var xx = up[1] * zz - up[2] * zy, xy = up[2] * zx - up[0] * zz,
        xz = up[0] * zy - up[1] * zx;
    l = Math.hypot(xx, xy, xz) || 1;
    xx /= l; xy /= l; xz /= l;
    var yx = zy * xz - zz * xy, yy = zz * xx - zx * xz,
        yz = zx * xy - zy * xx;
    return [xx, yx, zx, 0,
            xy, yy, zy, 0,
            xz, yz, zz, 0,
            -(xx * o[0] + xy * o[1] + xz * o[2]),
            -(yx * o[0] + yy * o[1] + yz * o[2]),
            -(zx * o[0] + zy * o[1] + zz * o[2]), 1];
  }
  function mModelo(a) {
    var rx = a.rotacion_x * Math.PI / 180, ry = a.rotacion_y * Math.PI / 180,
        rz = a.rotacion_z * Math.PI / 180, e = a.escala;
    var cx = Math.cos(rx), sx = Math.sin(rx),
        cy = Math.cos(ry), sy = Math.sin(ry),
        cz = Math.cos(rz), sz = Math.sin(rz);
    // R = Ry * Rx * Rz con escala, y traslación — suficiente para el
    // uso educativo (coincide con Actor.matriz_modelo del motor)
    var m = mMul(
      [cy, 0, -sy, 0, 0, 1, 0, 0, sy, 0, cy, 0, 0, 0, 0, 1],
      mMul(
        [1, 0, 0, 0, 0, cx, sx, 0, 0, -sx, cx, 0, 0, 0, 0, 1],
        [cz, sz, 0, 0, -sz, cz, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]));
    for (var i = 0; i < 12; i++) m[i] *= e;
    m[12] = a.x; m[13] = a.y; m[14] = a.z;
    return m;
  }
  function mPunto(m, p) {
    var w = m[3] * p[0] + m[7] * p[1] + m[11] * p[2] + m[15] || 1e-9;
    return [(m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12]) / w,
            (m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13]) / w,
            (m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14]) / w];
  }

  // -- mallas procedurales ------------------------------------------
  function cuboMalla() {
    var c = 0.5, p = [], n = [];
    function cara(u, v, norm) {
      var a = [-c, -c], b = [c, -c], d = [c, c], e = [-c, c];
      [[a, b, d], [a, d, e]].forEach(function (tri) {
        tri.forEach(function (t) {
          var q = [0, 0, 0];
          q[u[0]] = t[0]; q[u[1]] = t[1]; q[u[2]] = v;
          p.push(q[0], q[1], q[2]);
          n.push(norm[0], norm[1], norm[2]);
        });
      });
    }
    cara([0, 1, 2], c, [0, 0, 1]); cara([0, 1, 2], -c, [0, 0, -1]);
    cara([1, 2, 0], c, [1, 0, 0]); cara([1, 2, 0], -c, [-1, 0, 0]);
    cara([2, 0, 1], c, [0, 1, 0]); cara([2, 0, 1], -c, [0, -1, 0]);
    return { p: p, n: n };
  }
  function latlon(seg) {
    var p = [], n = [], r = 0.5;
    for (var i = 0; i < seg; i++)
      for (var j = 0; j < seg; j++) {
        var t0 = i / seg * Math.PI - Math.PI / 2,
            t1 = (i + 1) / seg * Math.PI - Math.PI / 2,
            f0 = j / seg * Math.PI * 2, f1 = (j + 1) / seg * Math.PI * 2;
        function v(t, f) {
          return [r * Math.cos(t) * Math.cos(f),
                  r * Math.sin(t),
                  r * Math.cos(t) * Math.sin(f)];
        }
        [[v(t0, f0), v(t1, f0), v(t1, f1)],
         [v(t0, f0), v(t1, f1), v(t0, f1)]].forEach(function (tri) {
          tri.forEach(function (q) {
            p.push(q[0], q[1], q[2]);
            var l = Math.hypot(q[0], q[1], q[2]) || 1;
            n.push(q[0] / l, q[1] / l, q[2] / l);
          });
        });
      }
    return { p: p, n: n };
  }
  function tubo(seg, tapas, cono) {
    var p = [], n = [], r = 0.5, h = 0.5;
    for (var j = 0; j < seg; j++) {
      var a0 = j / seg * Math.PI * 2, a1 = (j + 1) / seg * Math.PI * 2;
      var x0 = Math.cos(a0) * r, z0 = Math.sin(a0) * r,
          x1 = Math.cos(a1) * r, z1 = Math.sin(a1) * r;
      var r1 = cono ? 0.001 : r;               // cono: radio 0 arriba
      [[x0, -h, z0, x1, -h, z1, x1 * r1 / r, h, z1 * r1 / r],
       [x0, -h, z0, x1 * r1 / r, h, z1 * r1 / r, x0 * r1 / r, h, z0 * r1 / r]
      ].forEach(function (tri) {
        for (var v = 0; v < 3; v++) {
          p.push(tri[v * 3], tri[v * 3 + 1], tri[v * 3 + 2]);
          var nx = tri[v * 3], nz = tri[v * 3 + 2];
          var l = Math.hypot(nx, nz) || 1;
          n.push(nx / l, cono ? 0.5 : 0, nz / l);
        }
      });
      if (tapas) {
        [[x0, z0, x1, z1, 0, 0, -h], [x0, z0, 0, 0, x1, z1, h]
        ].forEach(function (t) {
          p.push(t[0], t[6], t[1], t[2], t[6], t[3], t[4], t[6], t[5]);
          for (var k = 0; k < 3; k++) n.push(0, t[6] > 0 ? 1 : -1, 0);
        });
      }
    }
    return { p: p, n: n };
  }
  function planoMalla() {
    var p = [], n = [], s = 0.5;
    [[-s, 0, -s], [s, 0, -s], [s, 0, s],
     [-s, 0, -s], [s, 0, s], [-s, 0, s]].forEach(function (q) {
      p.push(q[0], q[1], q[2]); n.push(0, 1, 0);
    });
    return { p: p, n: n };
  }

  // -- escena --------------------------------------------------------
  var canvas, gl, prog, uMVP, uColor, uAlfa, uLuz;
  var actores = [], tareas = [], colisiones = [], clicks = [];
  var dt = 0, tAhora = 0, fondo = [0.05, 0.07, 0.1];
  var HUD;                               // div para Texto/globos/menú
  var cam = { yaw: -35, pitch: 28, dist: 14, centro: [0, 0, 0],
              siguiendo: null, modo: 'tercera', temblor: 0, temblor_t: 0 };

  function iniciarGL() {
    canvas = document.createElement('canvas');
    canvas.style.cssText = 'position:fixed;inset:0;width:100%;height:100%';
    document.body.style.margin = '0';
    document.body.appendChild(canvas);
    HUD = document.createElement('div');
    HUD.style.cssText = 'position:fixed;inset:0;pointer-events:none;' +
      'font-family:sans-serif;overflow:hidden';
    document.body.appendChild(HUD);
    gl = canvas.getContext('webgl');
    var vs = 'attribute vec3 pos; attribute vec3 norm;' +
      'uniform mat4 mvp; varying vec3 vnorm;' +
      'void main(){ gl_Position = mvp * vec4(pos,1.0); vnorm = norm; }';
    var fs = 'precision mediump float; varying vec3 vnorm;' +
      'uniform vec3 color; uniform float alfa; uniform float luz;' +
      'void main(){ vec3 n = normalize(vnorm);' +
      ' float d = max(dot(n, normalize(vec3(0.45,0.8,0.4))), 0.0);' +
      ' vec3 c = color * (luz * (0.35 + 0.65 * d) + (1.0 - luz));' +
      ' gl_FragColor = vec4(c, alfa); }';
    function shader(t, src) {
      var s = gl.createShader(t);
      gl.shaderSource(s, src); gl.compileShader(s);
      return s;
    }
    prog = gl.createProgram();
    gl.attachShader(prog, shader(gl.VERTEX_SHADER, vs));
    gl.attachShader(prog, shader(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(prog); gl.useProgram(prog);
    uMVP = gl.getUniformLocation(prog, 'mvp');
    uColor = gl.getUniformLocation(prog, 'color');
    uAlfa = gl.getUniformLocation(prog, 'alfa');
    uLuz = gl.getUniformLocation(prog, 'luz');
    gl.enable(gl.DEPTH_TEST);
    gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  }

  function aWebGL(malla) {
    var bp = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, bp);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(malla.p),
                  gl.STATIC_DRAW);
    var bn = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, bn);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(malla.n),
                  gl.STATIC_DRAW);
    return { p: bp, n: bn, count: malla.p.length / 3 };
  }

  var MALLAS = {};
  function malla(tipo) {
    if (!MALLAS[tipo]) {
      var m = tipo === 'cubo' ? cuboMalla() :
              tipo === 'esfera' ? latlon(18) :
              tipo === 'cilindro' ? tubo(20, true, false) :
              tipo === 'cono' ? tubo(20, true, true) :
              planoMalla();
      MALLAS[tipo] = aWebGL(m);
    }
    return MALLAS[tipo];
  }

  // -- Actor ----------------------------------------------------------
  function Actor(tipo, ops) {
    ops = ops || {};
    this.tipo = tipo;
    this.x = ops.x || 0; this.y = ops.y || 0; this.z = ops.z || 0;
    this.rotacion_x = this.rotacion_y = this.rotacion_z = 0;
    this.escala = ops.escala || 1;
    this.color = ops.color || [0.8, 0.8, 0.8];
    this.alfa = 1; this.sin_luz = false;
    this.radio = ops.radio || 0.7;
    this.frente = ops.frente || [0, 1];
    this.vivo = true;
    this._habs = [];
    this._malla = malla(ops.malla || 'cubo');
    if (tipo === 'Zona') { this.alfa = 0.15; this.sin_luz = true; }
    if (tipo === 'Piso') { this.escala = 60; this.color = [0.35, 0.4, 0.35]; }
    actores.push(this);
  }
  Actor.prototype.eliminar = function () {
    this.vivo = false;
    if (this._globo) { this._globo.remove(); this._globo = null; }
  };
  Actor.prototype.esta_en_escena = function () { return this.vivo; };
  Actor.prototype.colisiona_en_plano_con = function (b) {
    return Math.hypot(this.x - b.x, this.z - b.z) <
           this.radio + b.radio;
  };
  Actor.prototype.mirar_hacia = function (x, z) {
    var dx = x - this.x, dz = z - this.z;
    if (!dx && !dz) return;
    var f = Math.atan2(this.frente[0], this.frente[1]) * 180 / Math.PI;
    this.rotacion_y = Math.atan2(dx, dz) * 180 / Math.PI - f;
  };
  Actor.prototype.decir = function (texto, duracion) {
    if (!this._globo) {
      var d = document.createElement('div');
      d.style.cssText = 'position:absolute;transform:translate(-50%,-100%);' +
        'background:#fff;color:#222;padding:4px 10px;border-radius:10px;' +
        'font-size:14px;white-space:nowrap';
      HUD.appendChild(d);
      this._globo = d;
    }
    this._globo.textContent = texto;
    var yo = this;
    setTimeout(function () {
      if (yo._globo) { yo._globo.remove(); yo._globo = null; }
    }, (duracion || 3) * 1000);
  };
  Actor.prototype.animar = function () {};
  Actor.prototype.aprender = function (nombre, ops) {
    HABILIDADES[nombre] && HABILIDADES[nombre](this, ops || {});
  };
  Actor.prototype.actualizar = function () {};

  // -- habilidades ------------------------------------------------------
  var HABILIDADES = {
    Patrullar: function (a, o) {
      var pts = o.puntos || [[0, 0]], i = 0, vel = o.velocidad || 2;
      a._habs.push(function () {
        var dx = pts[i][0] - a.x, dz = pts[i][1] - a.z;
        var d = Math.hypot(dx, dz);
        if (d < 0.15) { i = (i + 1) % pts.length; return; }
        a.mirar_hacia(pts[i][0], pts[i][1]);
        a.x += dx / d * vel * dt; a.z += dz / d * vel * dt;
      });
    },
    HuirDe: function (a, o) {
      var obj = o.objetivo, radio = o.radio || 5,
          vel = o.velocidad || 3;
      a._habs.push(function () {
        var dx = a.x - obj.x, dz = a.z - obj.z;
        var d = Math.hypot(dx, dz);
        if (d > radio || !d) return;
        a.mirar_hacia(a.x + dx, a.z + dz);
        a.x += dx / d * vel * dt; a.z += dz / d * vel * dt;
      });
    },
    RebotaEnParedes: function (a, o) {
      var vx = o.vx || 4, vz = o.vz || 4;
      var lim = o.limites || [-6, 6, -6, 6];
      a._habs.push(function () {
        a.x += vx * dt; a.z += vz * dt;
        if (a.x < lim[0] || a.x > lim[1]) vx = -vx;
        if (a.z < lim[2] || a.z > lim[3]) vz = -vz;
        a.mirar_hacia(a.x + vx, a.z + vz);
      });
    },
    PisaPlataformas: function (a, o) {
      var vy = 0, salto = o.salto || 9;
      a._habs.push(function () {
        var suelo = 0;
        actores.forEach(function (b) {
          if (b === a || !b.vivo || b.tipo === 'Zona') return;
          if (Math.abs(a.x - b.x) < b.escala * 0.5 + 0.4 &&
              Math.abs(a.z - b.z) < b.escala * 0.5 + 0.4) {
            var top = b.y + b.escala * 0.5;
            if (top > suelo && a.y >= top - 0.3) suelo = top;
          }
        });
        vy -= 20 * dt;
        a.y += vy * dt;
        if (a.y <= suelo) {
          a.y = suelo; vy = 0;
          if (control.ESPACIO || control[' ']) vy = salto;
        }
      });
    },
    Vida: function (a, o) {
      a.vida = o.vida || 100;
      a._vida_max = a.vida;
      a.recibir_dano = function (n) {
        a.vida -= n;
        if (a.vida <= 0) a.eliminar();
      };
      a.curar = function (n) {
        a.vida = Math.min(a.vida + n, a._vida_max);
      };
    },
    Parpadear: function (a, o) {
      var t = 0;
      a._habs.push(function () {
        t += dt * (o.velocidad || 8);
        a.alfa = 1 - (o.intensidad || 0.25) * (0.5 + 0.5 * Math.sin(t));
      });
    },
  };

  // -- input ------------------------------------------------------------
  var control = {}, mouse = { x: 0, y: 0 }, botones = [false, false, false];
  window.addEventListener('keydown', function (e) {
    control[normaliza(e.key)] = true;
    control[e.key] = true;
  });
  window.addEventListener('keyup', function (e) {
    control[normaliza(e.key)] = false;
    control[e.key] = false;
  });
  function normaliza(k) {
    return { ArrowLeft: 'izquierda', ArrowRight: 'derecha',
             ArrowUp: 'arriba', ArrowDown: 'abajo',
             ' ': 'ESPACIO', Enter: 'ENTER', Escape: 'ESCAPE' }[k] || k;
  }
  window.addEventListener('mousemove', function (e) {
    mouse.x = e.clientX; mouse.y = e.clientY;
    if (arrastrando) {
      cam.yaw += (e.clientX - arrastrando[0]) * 0.4;
      cam.pitch = Math.max(-89, Math.min(89,
        cam.pitch + (e.clientY - arrastrando[1]) * 0.3));
      arrastrando = [e.clientX, e.clientY];
    }
  });
  var arrastrando = null;
  window.addEventListener('mousedown', function (e) {
    botones[e.button] = true;
    if (e.button === 2) arrastrando = [e.clientX, e.clientY];
    if (e.button === 0) dispararClick();
  });
  window.addEventListener('mouseup', function (e) {
    botones[e.button] = false;
    arrastrando = null;
  });
  window.addEventListener('contextmenu', function (e) {
    e.preventDefault();
  });
  window.addEventListener('wheel', function (e) {
    cam.dist = Math.max(2, cam.dist + e.deltaY * 0.01);
  });

  var VP = mIdent();                     // view*proj del frame actual
  function dispararClick() {
    // rayo del mouse al plano y=0 + actor más cercano bajo el cursor
    var ndc = [(mouse.x / canvas.width) * 2 - 1,
               1 - (mouse.y / canvas.height) * 2];
    var mejor = null, mejorD = 1e9, punto = null;
    actores.forEach(function (a) {
      if (!a.vivo || a.tipo === 'Zona' || a.tipo === 'Piso') return;
      var s = mPunto(VP, [a.x, a.y, a.z]);
      var d = Math.hypot(s[0] - ndc[0], (s[1] - ndc[1]) *
                         canvas.height / canvas.width);
      if (d < 0.08 * a.escala + 0.03 && s[2] < mejorD) {
        mejor = a; mejorD = s[2]; punto = s;
      }
    });
    clicks.forEach(function (fn) { fn(mejor, punto); });
  }

  // -- HUD --------------------------------------------------------------
  function textoDOM(txt, x, y, css) {
    var d = document.createElement('div');
    d.style.cssText = 'position:absolute;left:' + x + 'px;top:' + y +
      'px;color:#fff;font-size:20px;text-shadow:1px 1px 2px #000;' +
      (css || '');
    d.textContent = txt;
    HUD.appendChild(d);
    return d;
  }
  function consola(txt) {
    var d = document.getElementById('_consola');
    if (!d) {
      d = textoDOM('', 10, 10, 'font-family:monospace;font-size:14px;' +
                   'color:#7ee787;white-space:pre');
      d.id = '_consola';
    }
    d.textContent += txt + '\n';
  }
  function menuDOM(titulo, opciones, ops) {
    ops = ops || {};
    var caja = document.createElement('div');
    caja.style.cssText = 'position:absolute;pointer-events:auto;' +
      'background:rgba(0,0,0,' + ((ops.fondo ? ops.fondo[3] : 150) /
      255) + ');padding:24px 48px;border-radius:8px;text-align:center;' +
      (ops.completa ? 'inset:0;display:flex;flex-direction:column;' +
        'justify-content:center;align-items:center' :
        'left:50%;top:50%;transform:translate(-50%,-50%)');
    var h = document.createElement('div');
    h.style.cssText = 'color:#ffd23f;font-size:28px;margin-bottom:14px';
    h.textContent = titulo;
    caja.appendChild(h);
    var sel = 0, items = [];
    opciones.forEach(function (par, i) {
      var b = document.createElement('div');
      b.style.cssText = 'color:#eee;font-size:20px;padding:8px;' +
        'cursor:pointer';
      b.textContent = par[0];
      b.onclick = function () { par[1](); };
      b.onmouseenter = function () { marcar(i); };
      caja.appendChild(b);
      items.push(b);
    });
    function marcar(i) {
      sel = i;
      items.forEach(function (b, j) {
        b.style.color = j === i ? '#ffd23f' : '#eee';
      });
    }
    marcar(0);
    window.addEventListener('keydown', function (e) {
      if (!caja.parentNode) return;
      if (e.key === 'ArrowDown') marcar((sel + 1) % items.length);
      if (e.key === 'ArrowUp')
        marcar((sel + items.length - 1) % items.length);
      if (e.key === 'Enter') opciones[sel][1]();
    });
    HUD.appendChild(caja);
    return { cerrar: function () { caja.remove(); } };
  }
  function barraDOM(actor) {
    var caja = document.createElement('div');
    caja.style.cssText = 'position:absolute;width:50px;height:6px;' +
      'background:#333;border-radius:3px;transform:translate(-50%,0)';
    var fill = document.createElement('div');
    fill.style.cssText = 'height:100%;background:#e74c3c;' +
      'border-radius:3px;width:100%';
    caja.appendChild(fill);
    HUD.appendChild(caja);
    tareas.push({ seg: 0, t: 0, fn: function () {
      if (!actor.vivo) { caja.remove(); return true; }
      var s = mPunto(VP, [actor.x, actor.y + 1.2 * actor.escala,
                          actor.z]);
      caja.style.left = (s[0] * 0.5 + 0.5) * canvas.width + 'px';
      caja.style.top = (0.5 - s[1] * 0.5) * canvas.height + 'px';
      fill.style.width = Math.max(0, actor.vida / actor._vida_max *
                                  100) + '%';
    } });
  }

  // -- api pública (la que usa el código generado) ----------------------
  var api = {};

  api.actores = {};
  ['Cubo', 'Esfera', 'Cilindro', 'Cono'].forEach(function (t) {
    api.actores[t] = function (ops) {
      return new Actor(t, Object.assign({ malla: t.toLowerCase() },
                                        ops));
    };
  });
  api.actores.Plano = function (ops) {
    return new Actor('Plano', Object.assign({ malla: 'plano' }, ops));
  };
  api.actores.Piso = function (ops) {
    return new Actor('Piso', Object.assign({ malla: 'cubo' },
      { escala: 60, color: [0.4, 0.45, 0.4] }, ops, { y: -0.5 }));
  };
  api.actores.Pared = function (ops) {
    return new Actor('Pared', Object.assign({ malla: 'cubo' }, ops));
  };
  api.actores.Zona = function (ops) {
    var z = new Actor('Zona', Object.assign({ malla: 'cubo' }, ops));
    z.escala = (ops && ops.escala) || 2;
    z.cuando_entra = function (a, fn) {
      var dentro = false;
      tareas.push({ seg: 0, t: 0, fn: function () {
        var d = Math.abs(a.x - z.x) < z.escala &&
                Math.abs(a.z - z.z) < z.escala;
        if (d && !dentro) fn();
        dentro = d;
      } });
    };
    return z;
  };
  api.actores.Ejes = function () {
    var a = new Actor('Ejes', { malla: 'cubo' });
    a.dibujar = function () {};          // se dibuja aparte (líneas)
    return a;
  };
  api.actores.Cielo = function (tipo) {
    var a = new Actor('Cielo', { malla: 'cubo' });
    a.dibujar = function () {};
    a.tipo = tipo || 'dia';
    Object.defineProperty(a, 'tipo', {
      get: function () { return a._tipo; },
      set: function (v) {
        a._tipo = v;
        fondo = v === 'estrellas' ? [0.02, 0.03, 0.1] :
                [0.5, 0.7, 0.95];
      },
    });
    a.tipo = tipo || 'dia';
    return a;
  };
  // personajes/modelos: el subset web los sustituye por primitivas —
  // el generador deja el comentario correspondiente en el código.
  api.actores.Texto = function (txt, x, y) {
    var d = textoDOM(txt, x || 10, y || 30);
    return { fijar_texto: function (t) { d.textContent = t; },
             elemento: d };
  };
  api.actores.Menu = function (ops) {
    return menuDOM(ops.titulo || 'MENU', ops.opciones || [],
      { fondo: ops.fondo, completa: ops.pantalla_completa });
  };
  api.actores.Barra = function (ops) {
    if (ops && ops.de) barraDOM(ops.de);
    return {};
  };
  api.actores.Lampara = function (ops) {
    var l = api.actores.Esfera(ops);
    l.color = [1, 0.9, 0.5]; l.sin_luz = true; l.escala = 0.3;
    var enc = true;
    Object.defineProperty(l, 'encendida', {
      get: function () { return enc; },
      set: function (v) { enc = v; l.alfa = v ? 1 : 0.25; },
    });
    return l;
  };

  api.colores = {
    rojo: [0.9, 0.15, 0.15], verde: [0.2, 0.8, 0.25],
    azul: [0.2, 0.35, 0.9], amarillo: [0.95, 0.85, 0.1],
    celeste: [0.35, 0.75, 0.95], naranja: [0.95, 0.5, 0.1],
    rosa: [0.95, 0.4, 0.65], violeta: [0.55, 0.3, 0.85],
    blanco: [1, 1, 1], gris: [0.5, 0.5, 0.5], negro: [0.05, 0.05, 0.05],
  };

  api.simbolos = { ESPACIO: 'ESPACIO', ENTER: 'ENTER', ESCAPE: 'ESCAPE',
                   IZQUIERDA: 'izquierda', DERECHA: 'derecha',
                   ARRIBA: 'arriba', ABAJO: 'abajo' };
  'abcdefghijklmnopqrstuvwxyz'.split('').forEach(function (l) {
    api.simbolos[l] = l;
  });

  api.control = {};
  Object.defineProperties(api.control, {
    izquierda: { get: function () { return !!control.izquierda; } },
    derecha: { get: function () { return !!control.derecha; } },
    arriba: { get: function () { return !!control.arriba; } },
    abajo: { get: function () { return !!control.abajo; } },
    ESPACIO: { get: function () { return !!control.ESPACIO; } },
    ENTER: { get: function () { return !!control.ENTER; } },
    mouse_x: { get: function () { return mouse.x; } },
    mouse_y: { get: function () { return mouse.y; } },
    boton_izquierdo: { get: function () { return botones[0]; } },
    boton_medio: { get: function () { return botones[1]; } },
    boton_derecho: { get: function () { return botones[2]; } },
  });
  api.control.simbolo = function (k) { return !!control[k]; };

  api.tareas = {
    siempre: function (seg, fn) { tareas.push({ seg: seg, t: 0, fn: fn }); },
    una_vez: function (seg, fn) {
      tareas.push({ seg: seg, t: 0, una: true, fn: fn });
    },
  };

  api.colisiones = {
    cuando_colisionan: function (a, b, fn) {
      colisiones.push({ a: a, b: b, fn: fn, tocando: false });
    },
  };
  api.cuando_hace_click = function (fn) { clicks.push(fn); };

  // corre fn() una vez cada vez que se pulsa la tecla (flanco)
  api.al_pulsar = function (tecla, fn) {
    var antes = false;
    tareas.push({ seg: 0, t: 0, fn: function () {
      var ahora = !!control[tecla];
      if (ahora && !antes) fn();
      antes = ahora;
    } });
  };

  var EASING = {
    Lineal: function (t) { return t; },
    AceleracionGradual: function (t) { return t * t; },
    DesaceleracionGradual: function (t) { return 1 - (1 - t) * (1 - t); },
    ReboteFinal: function (t) {
      var s = 2.75;
      if (t < 1 / s) return s * s * t * t;
      if (t < 2 / s) return s * s * (t -= 1.5 / s) * t + 0.75;
      if (t < 2.5 / s) return s * s * (t -= 2.25 / s) * t + 0.9375;
      return s * s * (t -= 2.625 / s) * t + 0.984375;
    },
    ElasticoFinal: function (t) {
      return t === 0 || t === 1 ? t :
        Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * 2.09) + 1;
    },
  };
  EASING.ReboteInicial = function (t) {
    return 1 - EASING.ReboteFinal(1 - t);
  };
  EASING.ElasticoInicial = function (t) {
    return 1 - EASING.ElasticoFinal(1 - t);
  };
  api.interpolaciones = EASING;
  api.interpolar = function (actor, campo, valor, duracion, tipo) {
    var desde = actor[campo], ease = EASING[tipo || 'Lineal'];
    var d = duracion || 1, t = 0;
    tareas.push({ seg: 0, t: 0, fn: function () {
      t += dt;
      var p = Math.min(1, t / d);
      actor[campo] = desde + (valor - desde) * ease(p);
      return p >= 1;
    } });
  };

  api.camara = {
    seguir_a: function (actor, modo) {
      cam.siguiendo = actor; cam.modo = modo || 'tercera';
    },
    dejar_de_seguir: function () { cam.siguiendo = null; },
    usar_control_orbital: function () {
      cam.siguiendo = null;   // arrastrar con botón derecho ya funciona
    },
    temblor: function (intensidad, seg) {
      cam.temblor = intensidad || 0.4; cam.temblor_t = seg || 0.5;
    },
  };

  api.sonidos = {
    cargar: function (ruta) {
      return { reproducir: function () {
        try { new Audio(ruta).play(); } catch (e) {}
      } };
    },
  };

  api.guardar_partida = function (ruta) {
    var datos = actores.filter(function (a) { return a.vivo; })
      .map(function (a) {
        return { x: a.x, y: a.y, z: a.z, vida: a.vida };
      });
    try { localStorage.setItem('pilas3d_' + (ruta || 'partida'),
                               JSON.stringify(datos)); } catch (e) {}
  };
  api.cargar_partida = function (ruta) {
    try {
      var datos = JSON.parse(localStorage.getItem(
        'pilas3d_' + (ruta || 'partida')) || '[]');
      actores.forEach(function (a, i) {
        if (datos[i]) { a.x = datos[i].x; a.y = datos[i].y;
                        a.z = datos[i].z; a.vida = datos[i].vida; }
      });
    } catch (e) {}
  };

  api.print = consola;
  api.decir = consola;

  // -- bucle --------------------------------------------------------------
  function ojoCamara() {
    var a = cam.siguiendo;
    if (a && a.vivo) {
      var rad = a.rotacion_y * Math.PI / 180;
      var fx = Math.sin(rad) * a.frente[1] +
               Math.cos(rad) * a.frente[0];
      var fz = Math.cos(rad) * a.frente[1] -
               Math.sin(rad) * a.frente[0];
      if (cam.modo === 'primera')
        return [[a.x, a.y + 1.4, a.z],
                [a.x + fx * 4, a.y + 1.2, a.z + fz * 4]];
      if (cam.modo === 'segunda')
        return [[a.x + fx * 6, a.y + 2.5, a.z + fz * 6],
                [a.x, a.y + 1, a.z]];
      return [[a.x - fx * 6, a.y + 3.5, a.z - fz * 6],
              [a.x, a.y + 1, a.z]];
    }
    var yr = cam.yaw * Math.PI / 180, pr = cam.pitch * Math.PI / 180;
    var cx = cam.centro[0] + cam.dist * Math.cos(pr) * Math.sin(yr);
    var cy = cam.centro[1] + cam.dist * Math.sin(pr);
    var cz = cam.centro[2] + cam.dist * Math.cos(pr) * Math.cos(yr);
    return [[cx, cy, cz], cam.centro];
  }

  function frame(tMs) {
    requestAnimationFrame(frame);
    var nuevo = tMs / 1000;
    dt = Math.min(0.05, nuevo - tAhora || 0.016);
    tAhora = nuevo;

    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;

    // tareas (fn puede devolver true para terminar)
    for (var i = tareas.length - 1; i >= 0; i--) {
      var t = tareas[i];
      t.t -= dt;
      if (t.t <= 0) {
        var fin = t.fn();
        if (fin || t.una) tareas.splice(i, 1);
        else t.t = t.seg;
      }
    }
    // habilidades + update de actores
    actores.forEach(function (a) {
      if (!a.vivo) return;
      a._habs.forEach(function (h) { h(); });
      a.actualizar();
    });
    // colisiones edge-triggered
    colisiones.forEach(function (c) {
      var toca = c.a.vivo && c.b.vivo &&
                 c.a.colisiona_en_plano_con(c.b);
      if (toca && !c.tocando) c.fn();
      c.tocando = toca;
    });

    // cámara + render
    var oc = ojoCamara();
    if (cam.temblor_t > 0) {
      cam.temblor_t -= dt;
      var k = cam.temblor * cam.temblor_t;
      oc[0] = [oc[0][0] + (Math.random() - 0.5) * k,
               oc[0][1] + (Math.random() - 0.5) * k, oc[0][2]];
    }
    var proj = mPerspectiva(1.1, canvas.width / canvas.height,
                            0.1, 300);
    var vista = mLookAt(oc[0], oc[1], [0, 1, 0]);
    VP = mMul(proj, vista);

    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clearColor(fondo[0], fondo[1], fondo[2], 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.useProgram(prog);

    var aPos = gl.getAttribLocation(prog, 'pos');
    var aNorm = gl.getAttribLocation(prog, 'norm');
    actores.forEach(function (a) {
      if (!a.vivo) return;
      var mvp = mMul(VP, mModelo(a));
      gl.uniformMatrix4fv(uMVP, false, new Float32Array(mvp));
      gl.uniform3fv(uColor, new Float32Array(a.color));
      gl.uniform1f(uAlfa, a.alfa);
      gl.uniform1f(uLuz, a.sin_luz ? 0 : 1);
      gl.bindBuffer(gl.ARRAY_BUFFER, a._malla.p);
      gl.enableVertexAttribArray(aPos);
      gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 0, 0);
      gl.bindBuffer(gl.ARRAY_BUFFER, a._malla.n);
      gl.enableVertexAttribArray(aNorm);
      gl.vertexAttribPointer(aNorm, 3, gl.FLOAT, false, 0, 0);
      gl.drawArrays(gl.TRIANGLES, 0, a._malla.count);
    });

    // globos de diálogo siguen a su actor en pantalla
    actores.forEach(function (a) {
      if (a._globo && a.vivo) {
        var s = mPunto(VP, [a.x, a.y + 1.3 * a.escala, a.z]);
        a._globo.style.left = (s[0] * 0.5 + 0.5) * canvas.width + 'px';
        a._globo.style.top = (0.5 - s[1] * 0.5) * canvas.height + 'px';
      }
    });
  }

  window.addEventListener('load', function () {
    iniciarGL();
    requestAnimationFrame(function (t) {
      tAhora = t / 1000;
      requestAnimationFrame(frame);
    });
    if (typeof programa === 'function') programa();
  });

  return api;
})();
