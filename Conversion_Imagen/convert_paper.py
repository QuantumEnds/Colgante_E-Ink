import sys
from PIL import Image, ImageOps

# 1. Paleta estándar de E-Paper de 6 colores (RGB)
# El índice coincide con el valor de 4 bits (0x0 a 0x6)
EPAPER_PALETTE = [
    [0, 0, 0],       # 0x0: Negro
    [255, 255, 255], # 0x1: Blanco
    [255, 243, 56],  # 0x2: Amarillo
    [220, 0, 0],     # 0x3: Rojo
    [255, 128, 0],   # 0x4: Naranja
    [0, 0, 255],     # 0x5: Azul
    [0, 128, 0],     # 0x6: Verde
]

def create_palette_image():
    """Crea una imagen de paleta de 256 colores para cuantización con Pillow."""
    palette_data = []
    for rgb in EPAPER_PALETTE:
        palette_data.extend(rgb)
    # Rellenar hasta los 256 colores requeridos por la paleta de Pillow
    palette_data.extend([0] * (768 - len(palette_data)))
    
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette(palette_data)
    return pal_img

def convert_image_to_epaper(input_path, output_c_path="image_data.h", output_preview_path="preview.png", use_dithering=True):
    """
    1. Ajusta la imagen a 400x400 y aplica la paleta e-Paper.
    2. Guarda una imagen PNG de vista previa.
    3. Genera el array empaquetado de 4 bits en un archivo C (.h).
    """
    # Cargar la imagen y encuadrar centrada a 400x400
    img = Image.open(input_path).convert("RGB")
    img = ImageOps.fit(img, (400, 400), Image.Resampling.LANCZOS)
    
    # Reducir colores a los 6 de tinta electrónica mediante tramado (dithering)
    pal_img = create_palette_image()
    dither_mode = Image.Dither.FLOYDSTEINBERG if use_dithering else Image.Dither.NONE
    quantized_img = img.quantize(palette=pal_img, dither=dither_mode)
    
    # --- VISTA PREVIA ---
    # Convertimos de nuevo a RGB utilizando la paleta para guardar la imagen simulada
    preview_img = quantized_img.convert("RGB")
    preview_img.save(output_preview_path)
    
    # --- GENERACIÓN DEL ARRAY C ---
    pixels = list(quantized_img.getdata())
    packed_bytes = bytearray()
    
    # Empaquetar 2 píxeles por byte (nibble alto / nibble bajo)
    for i in range(0, len(pixels), 2):
        p1 = pixels[i] & 0x0F     # Píxel izquierdo
        p2 = pixels[i + 1] & 0x0F # Píxel derecho
        packed_bytes.append((p1 << 4) | p2)
        
    with open(output_c_path, "w", encoding="utf-8") as f:
        f.write("// Imagen 400x400 convertida para E-Paper (4 bits/píxel -> 80,000 bytes)\n")
        f.write(f"const unsigned char gImage1[{len(packed_bytes)}] = {{\n")
        
        # Formato de 16 bytes por línea
        for i in range(0, len(packed_bytes), 16):
            chunk = packed_bytes[i:i + 16]
            hex_str = ", ".join([f"0x{b:02X}" for b in chunk])
            f.write(f"    {hex_str},\n")
            
        f.write("};\n")
        
    print("¡Proceso completado!")
    print(f" -> Vista previa guardada en: {output_preview_path}")
    print(f" -> Array C/C++ guardado en:   {output_c_path}")
    print(f" -> Tamaño final:              {len(packed_bytes)} bytes")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python convert_epaper.py  [salida.h] [preview.png]")
        sys.exit(1)
        
    input_image = sys.argv[1]
    output_header = sys.argv[2] if len(sys.argv) > 2 else "image_data.h"
    output_preview = sys.argv[3] if len(sys.argv) > 3 else "preview.png"
    
    convert_image_to_epaper(input_image, output_header, output_preview, use_dithering=True)