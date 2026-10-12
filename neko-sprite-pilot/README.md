# Neko Sprite Pilot

La escena combina un gato animado por fotogramas con capas ambientales independientes: césped, flores, ramas laterales, luces lejanas, luciérnagas, neblina y estrellas fugaces. Los movimientos son lentos y están diseñados para conservar intacto el fondo original.

## Video vertical

- `exports/neko-noche-2min.mp4`: versión MP4 de 2 minutos, 720 × 1280, H.264 y sin texto.
- `render_video.py`: permite volver a generar el video y cambiar su duración o sus fotogramas por segundo.

## Colección de 20 escenas

La carpeta `collection-20` contiene veinte videos adicionales de dos minutos con paisajes, personajes y efectos ambientales diferentes. `render_collection.py` permite regenerar todo el lote.

Primer ejemplo del nuevo proyecto de animación por fotogramas.

- Fondo original independiente.
- Hoja de 8 sprites transparentes en una cuadrícula de 4 × 2.
- Animación del cuerpo, orejas y cola mediante cambio de fotogramas.
- Ciclo pausado de aproximadamente 4.5 segundos para un movimiento tranquilo.
- Césped animado con un ciclo de 8 posiciones.
- Estrellas, tres estrellas fugaces, niebla e iluminación ambiental independientes.
- Sin palabras, ondas ni deformación del fondo.

Abrir `index.html` mediante un servidor web local.
