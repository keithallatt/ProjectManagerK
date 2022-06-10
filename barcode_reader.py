from PIL import Image
import numpy as np


def get_barcode():
    img = Image.open("barcode.gif")
    img_np = np.array(img)

    third_row = list(img_np[3])

    current_value = third_row.pop(0)
    barcode = [(current_value, 1)]

    while third_row:
        last_char, quant = barcode.pop(-1)
        next_char = third_row.pop(0)

        if last_char == next_char:
            barcode.append((last_char, quant + 1))
        else:
            barcode.append((last_char, quant))
            barcode.append((next_char, 1))

    barcode = "".join([{0: ' ', 251: '#'}[t[0]] * t[1] for t in barcode])
    return barcode
