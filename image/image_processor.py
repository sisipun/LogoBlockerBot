from PIL import ImageDraw
from PIL import ImageFilter
from enum import Enum


class ProcessMode(Enum):
    BLUR = '-bbl'
    BOUNDING_BOX = '-bb'
    FILL = '-fl'


def process_image(image, boxes, mode=ProcessMode.BLUR, color=(255, 0, 0), blur_force=20):
    processed_image = image.copy()
    draw = ImageDraw.Draw(processed_image)

    for box in boxes:
        if mode == ProcessMode.BLUR:
            ib = (int(box[0]), int(box[1]), int(box[2]), int(box[3]))
            ic = processed_image.crop(ib)
            for _ in range(blur_force):
                ic = ic.filter(ImageFilter.GaussianBlur())
            processed_image.paste(ic, ib)
        elif mode == ProcessMode.BOUNDING_BOX:
            draw.rectangle([(box[0], box[1]), (box[2], box[3])],
                           outline=color)
            draw.rectangle([(box[0] - 1, box[1] - 1), (box[2] + 1, box[3] + 1)],
                           outline=color)
            draw.rectangle([(box[0] + 1, box[1] + 1), (box[2] - 1, box[3] - 1)],
                           outline=color)
        elif mode == ProcessMode.FILL:
            draw.rectangle(
                [(box[0], box[1]), (box[2], box[3])], fill=color)

    del draw
    return processed_image
