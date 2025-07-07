from pyzbar.pyzbar import decode
from PIL import Image, ImageOps

# Sustituye por el nombre exacto de tu foto recortada (por ejemplo 'barcode.jpg')
IMG_PATH = 'web/barcode.jpg'

# Abre la imagen
img = Image.open(IMG_PATH)

# 1) Decodificación “cruda”
codes = decode(img)
print('Crudo:', [c.data.decode() for c in codes])

# 2) Escala de grises + autocontraste
gray = img.convert('L')
auto = ImageOps.autocontrast(gray)
codes2 = decode(auto)
print('Autocontraste:', [c.data.decode() for c in codes2])

# 3) Umbral binario (negro/blanco)
bw = gray.point(lambda x: 0 if x < 128 else 255, '1')
codes3 = decode(bw)
print('Binarizado:', [c.data.decode() for c in codes3])
