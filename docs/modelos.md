# Guía: cómo ordenar `modelos/`

`modelos/` está en `.gitignore`: es **tu biblioteca local** — los
assets no se publican (licencias y peso). Aun así, ordenarla rinde:
el editor descubre `.glb` recursivamente, y encontrar qué se puede
usar de un vistazo ahorra tiempo.

## Regla de oro

**Separar lo que el motor CARGA de lo que EDITA.**

El motor lee `.glb`/`.gltf` (riggeados) y `.obj` (estáticos). Todo lo
demás — `.blend`, `.fbx`, `.c4d`, `.ma`, `.max`, `.lxo`, `.ztl` — es
formato de autoría: no se carga, solo sirve para re-exportar.

## Estructura propuesta

```
modelos/
├── personajes/            # riggeados (.glb con skin)
│   ├── wolf/
│   │   ├── Wolf.glb
│   │   └── texturas/      # imágenes sueltas que usa el .gltf
│   ├── fox/Fox.glb
│   ├── cesium_man/CesiumMan.glb
│   ├── brainstem/BrainStem.glb
│   ├── mousylon/039_Mousylon_Art.glb
│   └── polypug/060_Polypug_Art.glb
├── props/                 # estáticos (.glb/.obj, sin skin)
│   ├── avatar_logo/TheAvatarShow_Logo_Background.glb
│   ├── streetlight/
│   │   ├── Streetlight_LowRes.obj + .mtl
│   │   └── texturas/
│   ├── low_poly_tree/Lowpoly_tree_sample.obj
│   └── moon/Moon 2K.obj + .mtl + Diffuse_2K.png
├── fuentes/               # archivos de autoría, por si hay que
│   │                      # re-exportar: .blend .fbx .obj .c4d...
│   ├── moon/
│   ├── low_poly_tree/
│   └── streetlight/
└── docs/                  # readmes, licencias, pdfs, renders
```

## Reglas concretas

1. **Una carpeta por modelo**, con nombre claro y sin espacios
   (`cesium_man`, no `Supporting Files`). Los espacios funcionan,
   pero complican scripts y consolas.
2. **Preferí `.glb`**: un solo archivo autocontenido (malla +
   texturas + skin + animaciones). Guardá el `.gltf`+`.bin` suelto
   solo si necesitás inspeccionar el JSON.
3. **Formatos por uso**:
   | Qué querés | Formato |
   |---|---|
   | Personaje animado | `.glb` con skin + clips |
   | Prop estático | `.glb` u `.obj`+`.mtl` |
   | Re-exportar/editar en Blender | `.blend`/`.fbx` → carpeta `fuentes/` |
   | Referencia visual | renders/jpgs → `docs/` |
4. **Texturas sueltas** van en `texturas/` dentro de la carpeta del
   modelo (el `.gltf` las referencia por ruta relativa).
5. **Deduplicar**: el wolf trae 6 texturas con nombres tipo
   `Material__wolf_col_tga_diffuse.jpeg` y `..._jpeg.jpg` duplicadas —
   quedate las que el `.gltf` referencia y mové el resto a `fuentes/`.
6. **Documentá la fuente**: un `docs/FUENTES.md` con origen y
   licencia de cada pack (Khronos CC0, Mixamo, Quaternius CC0...).
   Si mañana publicás algo, evitás sustos.

## Bonus: cómo lo ve el editor

`editor_personaje.py` hace `glob('modelos/**/*.glb')` — **solo los
`.glb` aparecen** en la tecla N. Entonces: `.glb` en `personajes/` y
`props/` se cargan solos; los `.obj` estáticos quedan disponibles por
ruta para los ejemplos (`actores.Modelo('modelos/props/moon/Moon 2K.obj')`).

## Migración rápida del estado actual

```
33-gltf-wolf/gltf/          → personajes/wolf/
khronos/*.glb               → personajes/{fox,cesium_man,brainstem}/
Supporting Files/*.glb      → personajes/ (mousylon, polypug, robot)
                              + props/avatar_logo/
                              + docs/README.pdf
SpiderAnimate/              → props/spider/ (obj+mtl+texturas)
Streetlight/{Obj,Fbx,Render}→ props/streetlight/ (obj) + fuentes/ (fbx)
                              + docs/ (renders)
low_poly_tree/*.obj         → props/low_poly_tree/ ; resto → fuentes/
Moon 2K.* (raíz, sueltos)   → props/moon/ (obj+mtl+textures)
                              ; blend/c4d/fbx/ma/max → fuentes/moon/
Textures/*.png              → props/moon/texturas/
```
