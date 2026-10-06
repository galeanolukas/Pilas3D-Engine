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
  if (g.n) geo.setAttribute('normal',
                          new THREE.BufferAttribute(f32(g.n), 3));
  else geo.computeVertexNormals();
  if (g.c) geo.setAttribute('color',
                          new THREE.BufferAttribute(f32(g.c), 4));
  if (g.u) geo.setAttribute('uv', new THREE.BufferAttribute(f32(g.u), 2));
  if (g.x) geo.setIndex(new THREE.BufferAttribute(u32(g.x), 1));
  return geo;
}

function crearMesh(a) {
  const geo = geos.get(a.i);
  if (!geo) return null;                       // la geo llega en 'g'
  const mat = a.l
    ? new THREE.MeshBasicMaterial({ vertexColors: !!geo.hasAttribute('color') })
    : new THREE.MeshStandardMaterial({
        vertexColors: !!geo.hasAttribute('color'),
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

function snapshot(msg) {
  if (msg.g) for (const g of msg.g) geos.set(g.i, geometria(g));
  const vistos = new Set();
  for (const a of msg.a) {
    vistos.add(a.i);
    let e = actores.get(a.i);
    if (!e) {
      const mesh = crearMesh(a);
      if (!mesh) continue;
      e = { mesh, pos: a.p.slice(), rot: a.r.slice(),
            esc: a.e.slice() };
      mesh.position.set(...a.p);
      mesh.rotation.set(...a.r.map(THREE.MathUtils.degToRad), 'YXZ');
      mesh.scale.set(...a.e);
      actores.set(a.i, e);
    }
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
  if (msg.fondo) {
    escena3.background = new THREE.Color(msg.fondo[0] / 255,
                                         msg.fondo[1] / 255,
                                         msg.fondo[2] / 255);
  }
  estado.textContent = 'actores: ' + msg.a.length +
    '   (WASD/flechas se envían al motor)';
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
    m.rotation.set(e.rot[0] * DEG, e.rot[1] * DEG, e.rot[2] * DEG,
                   'YXZ');
    m.scale.set(e.esc[0], e.esc[1], e.esc[2]);
  }
  renderer.render(escena3, camara);
}
render();

addEventListener('resize', () => {
  camara.aspect = innerWidth / innerHeight;
  camara.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});
