/* pilas3d — cliente Three.js del puente web.
 *
 * Recibe por WebSocket snapshots del motor Python (actores con
 * transformación + geometrías b64 la primera vez) y los dibuja con
 * WebGL: MeshStandardMaterial, sombras reales, niebla, luces.
 * Las teclas y el mouse viajan de vuelta al motor -> pilas.control.
 */
import * as THREE from './three.module.min.js';

const estado = document.getElementById('estado');
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(devicePixelRatio);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

const escena3 = new THREE.Scene();
escena3.background = new THREE.Color(0x101418);
const camara = new THREE.PerspectiveCamera(60, innerWidth / innerHeight,
                                           0.1, 2000);

// luces por defecto; el snapshot las reemplaza por las del motor
const luzAmb = new THREE.AmbientLight(0xffffff, 0.45);
const luzDir = new THREE.DirectionalLight(0xffffff, 1.0);
luzDir.castShadow = true;
luzDir.shadow.mapSize.set(2048, 2048);
luzDir.shadow.camera.left = luzDir.shadow.camera.bottom = -60;
luzDir.shadow.camera.right = luzDir.shadow.camera.top = 60;
luzDir.shadow.camera.far = 500;
escena3.add(luzAmb, luzDir, luzDir.target);
const puntuales = new Map();   // índice -> PointLight

// -- decodificación b64 -> typed arrays -------------------------------
function bytes(b64) {
  const s = atob(b64), a = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i);
  return a;
}
const f32 = b64 => new Float32Array(bytes(b64).buffer);
const u32 = b64 => new Uint32Array(bytes(b64).buffer);

// -- HUD 2D (overlays como elementos DOM) --------------------------------
const hudEl = document.getElementById('hud');
const hudDivs = [];
const V = new THREE.Vector3();
const rgb = c => 'rgb(' + c[0] + ',' + c[1] + ',' + c[2] + ')';

function proyectar(p) {          // mundo -> px de pantalla (desde arriba)
  V.copy(p).project(camara);
  return [(V.x * 0.5 + 0.5) * innerWidth,
          (-V.y * 0.5 + 0.5) * innerHeight];
}

function hud(msg) {
  const vw = msg.v ? msg.v[0] : 800, vh = msg.v ? msg.v[1] : 600;
  const sx = innerWidth / vw, sy = innerHeight / vh;
  const items = msg.hud || [];
  while (hudDivs.length < items.length) {
    const d = document.createElement('div');
    hudEl.appendChild(d);
    hudDivs.push(d);
  }
  while (hudDivs.length > items.length) hudDivs.pop().remove();
  items.forEach((it, i) => {
    const d = hudDivs[i];
    d.className = 'hud-' + it.k;
    d._ancla = undefined;
    if (it.x !== undefined) d.style.left = (it.x * sx) + 'px';
    if (it.y !== undefined) d.style.bottom = (it.y * sy) + 'px';
    if (it.k === 't') {
      d.textContent = it.s;
      d.style.fontSize = Math.round(it.z * sy) + 'px';
      d.style.color = rgb(it.c);
      d.style.width = it.w ? (it.w * sx) + 'px' : '';
    } else if (it.k === 'p') {
      d.style.width = (it.w * sx) + 'px';
      d.style.height = (it.h * sy) + 'px';
      d.style.background = rgb(it.c);
    } else if (it.k === 'b') {
      d.style.width = (it.w * sx) + 'px';
      d.style.height = (it.h * sy) + 'px';
      let fill = d.firstChild;
      if (!fill) {
        fill = document.createElement('i');
        d.appendChild(fill);
      }
      fill.style.width = Math.round(it.f * 100) + '%';
      fill.style.background = it.c ? rgb(it.c)
        : it.f > 0.5 ? '#4c4' : it.f > 0.25 ? '#cc4' : '#c44';
    } else if (it.k === 'g') {
      d.textContent = it.s;
      d.style.fontSize = Math.round((it.z || 15) * sy) + 'px';
      d._ancla = it.a;                       // actor id o undefined
      d._alto = it.h || 0.4;
      if (it.a === undefined && it.x !== undefined) {
        d.style.left = (it.x * sx) + 'px';
        d.style.top = (vh - it.y) * sy + 'px';
        d.style.bottom = '';
      }
    }
  });
}

// los globos anclados persiguen a su actor cada frame render
function reanclarGlobos() {
  for (const d of hudDivs) {
    if (d._ancla === undefined) continue;
    const e = actores.get(d._ancla);
    if (!e) { d.style.display = 'none'; continue; }
    d.style.display = '';
    V.copy(e.mesh.position);
    V.y += d._alto;
    const p = proyectar(V);
    d.style.left = p[0] + 'px';
    d.style.top = p[1] + 'px';
    d.style.bottom = '';
  }
}

// -- actores -----------------------------------------------------------
// id -> {mesh, pos, rot, esc} con pos/rot/esc = objetivos para el lerp
const actores = new Map();
const geos = new Map();        // id -> BufferGeometry
const texturas = new Map();    // nombre -> THREE.Texture
const cargador = new THREE.TextureLoader();

function textura(nombre) {
  if (!texturas.has(nombre)) {
    const t = cargador.load('/' + nombre);
    t.colorSpace = THREE.SRGBColorSpace;
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    texturas.set(nombre, t);
  }
  return texturas.get(nombre);
}

function geometria(g) {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position',
                   new THREE.BufferAttribute(f32(g.v), 3));
  // puntos y líneas no usan normales
  if (g.n && g.m !== 0 && g.m !== 1)
    geo.setAttribute('normal',
                     new THREE.BufferAttribute(f32(g.n), 3));
  else if (g.m !== 0 && g.m !== 1) geo.computeVertexNormals();
  if (g.c) geo.setAttribute('color',
                          new THREE.BufferAttribute(f32(g.c), 4));
  if (g.u) geo.setAttribute('uv', new THREE.BufferAttribute(f32(g.u), 2));
  if (g.x) geo.setIndex(new THREE.BufferAttribute(u32(g.x), 1));
  geo._modo = g.m === undefined ? 4 : g.m;
  return geo;
}

function crearMesh(a) {
  const geo = geos.get(a.i);
  if (!geo) return null;                       // la geo llega en 'g'
  const colores = !!geo.hasAttribute('color');
  // GL_POINTS / GL_LINES del motor -> Points / LineSegments
  if (geo._modo === 0) {
    const m = new THREE.PointsMaterial({
      vertexColors: colores, size: a.pt || 2.0,
      sizeAttenuation: false, transparent: true });
    const pts = new THREE.Points(geo, m);
    escena3.add(pts);
    return pts;
  }
  if (geo._modo === 1) {
    const ls = new THREE.LineSegments(
      geo, new THREE.LineBasicMaterial({ vertexColors: colores }));
    escena3.add(ls);
    return ls;
  }
  const mat = a.l
    ? new THREE.MeshBasicMaterial({ vertexColors: colores })
    : new THREE.MeshStandardMaterial({
        vertexColors: colores,
        roughness: 0.9, metalness: 0.0 });
  if (a.t) mat.map = textura(a.t);
  const mesh = new THREE.Mesh(geo, mat);
  mesh.castShadow = mesh.receiveShadow = true;
  escena3.add(mesh);
  return mesh;
}

function actualizarMesh(e, a) {
  e.pos = a.p; e.rot = a.r; e.esc = a.e;
  const m = e.mesh.material;
  if (a.c) m.color.setRGB(a.c[0] / 255, a.c[1] / 255, a.c[2] / 255);
  else m.color.setRGB(1, 1, 1);
  const op = a.o === undefined ? 1 : a.o;
  m.transparent = op < 1;
  m.opacity = op;
  if (a.t && !m.map) { m.map = textura(a.t); m.needsUpdate = true; }
}

const _euler = new THREE.Euler();
function snapshot(msg) {
  if (msg.g) for (const g of msg.g) {
    const geo = geometria(g);
    geos.set(g.i, geo);
    // geometría re-enviada (partículas, skinning): se la cambia al
    // mesh vivo que referenciaba la versión vieja
    const e = actores.get(g.i);
    if (e) { e.mesh.geometry.dispose(); e.mesh.geometry = geo; }
  }
  const vistos = new Set();
  for (const a of msg.a) {
    vistos.add(a.i);
    let e = actores.get(a.i);
    if (!e) {
      const mesh = crearMesh(a);
      if (!mesh) continue;
      e = { mesh, pos: a.p.slice(), esc: a.e.slice(),
            quat: new THREE.Quaternion(), nuevo: true };
      mesh.position.set(...a.p);
      mesh.scale.set(...a.e);
      actores.set(a.i, e);
    }
    // objetivo de rotación como quaternion: el render hace slerp
    _euler.set(a.r[0] * Math.PI / 180, a.r[1] * Math.PI / 180,
               a.r[2] * Math.PI / 180, 'YXZ');
    e.quat.setFromEuler(_euler);
    if (e.nuevo) { e.mesh.quaternion.copy(e.quat); e.nuevo = false; }
    actualizarMesh(e, a);
  }
  for (const [i, e] of actores) {
    if (!vistos.has(i)) { escena3.remove(e.mesh); actores.delete(i); }
  }
  if (msg.cam) {
    camara.position.set(...msg.cam.p);
    camara.lookAt(...msg.cam.o);
  }
  if (msg.luz) {
    const l = msg.luz;
    luzDir.color.setRGB(l.c[0] / 255, l.c[1] / 255, l.c[2] / 255);
    // el motor guarda una dirección; three quiere posición + target
    luzDir.position.set(-l.d[0] * 80, -l.d[1] * 80, -l.d[2] * 80);
    luzDir.target.position.set(0, 0, 0);
    luzAmb.color.setRGB(l.ambc[0] / 255, l.ambc[1] / 255,
                        l.ambc[2] / 255);
    luzAmb.intensity = l.amb;
    l.p.forEach((p, i) => {
      let pl = puntuales.get(i);
      if (!pl) {
        pl = new THREE.PointLight();
        pl.castShadow = false;
        escena3.add(pl);
        puntuales.set(i, pl);
      }
      pl.position.set(p[0], p[1], p[2]);
      pl.color.setRGB(p[3][0] / 255, p[3][1] / 255, p[3][2] / 255);
      pl.distance = p[4];
      pl.intensity = 2.0;
    });
    for (const [i, pl] of puntuales) {
      if (i >= l.p.length) { escena3.remove(pl); puntuales.delete(i); }
    }
  }
  if (msg.nie) {
    const [c, ini, fin] = msg.nie;
    escena3.fog = new THREE.Fog(
      new THREE.Color(c[0] / 255, c[1] / 255, c[2] / 255), ini, fin);
  } else escena3.fog = null;
  if (msg.cielo) {
    // .hdr del motor ya tonemapeado a PNG: fondo equirect + IBL
    const t = textura(msg.cielo);
    if (escena3.background !== t) {
      t.mapping = THREE.EquirectangularReflectionMapping;
      escena3.background = t;
      escena3.environment = t;          // iluminación basada en imagen
    }
  } else if (msg.fondo) {
    escena3.background = new THREE.Color(msg.fondo[0] / 255,
                                         msg.fondo[1] / 255,
                                         msg.fondo[2] / 255);
    escena3.environment = null;
  }
  estado.textContent = 'actores: ' + msg.a.length +
    '   (WASD/flechas se envían al motor)';
  hud(msg);
}

// -- WebSocket ----------------------------------------------------------
let ws;
function conectar() {
  ws = new WebSocket('ws://' + location.host + '/ws');
  ws.onopen = () => { estado.textContent = 'conectado'; };
  ws.onmessage = ev => {
    const msg = JSON.parse(ev.data);
    if (msg.t === 'e') snapshot(msg);
  };
  ws.onclose = () => {
    estado.textContent = 'desconectado — reintentando…';
    setTimeout(conectar, 1500);
  };
}
conectar();

// -- input hacia el motor ------------------------------------------------
addEventListener('keydown', ev => {
  if (ev.repeat) return;
  ws?.send(JSON.stringify({ t: 'k', k: ev.code, v: 1 }));
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight',
       'Space'].includes(ev.code)) ev.preventDefault();
});
addEventListener('keyup', ev =>
  ws?.send(JSON.stringify({ t: 'k', k: ev.code, v: 0 })));
addEventListener('pointermove', ev =>
  ws?.send(JSON.stringify({ t: 'm', x: ev.clientX,
                            y: innerHeight - ev.clientY,
                            b: ev.buttons })));
addEventListener('pointerdown', ev =>
  ws?.send(JSON.stringify({ t: 'm', x: ev.clientX,
                            y: innerHeight - ev.clientY,
                            b: ev.buttons })));
addEventListener('pointerup', ev =>
  ws?.send(JSON.stringify({ t: 'm', x: ev.clientX,
                            y: innerHeight - ev.clientY,
                            b: ev.buttons })));

// -- loop de render: lerp exponencial hacia los objetivos -----------------
const DEG = Math.PI / 180;
function render() {
  requestAnimationFrame(render);
  for (const e of actores.values()) {
    const m = e.mesh;
    m.position.x += (e.pos[0] - m.position.x) * 0.3;
    m.position.y += (e.pos[1] - m.position.y) * 0.3;
    m.position.z += (e.pos[2] - m.position.z) * 0.3;
    m.quaternion.slerp(e.quat, 0.3);        // giros suaves
    m.scale.set(e.esc[0], e.esc[1], e.esc[2]);
  }
  reanclarGlobos();
  renderer.render(escena3, camara);
}
render();

addEventListener('resize', () => {
  camara.aspect = innerWidth / innerHeight;
  camara.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});
