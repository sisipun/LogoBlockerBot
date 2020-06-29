#!/usr/bin/python

import sys
import torch
from PIL import Image
from torchvision import transforms
from detection.logo_detector import detect_logo
from image.image_processor import process_image, ProcessMode

assert len(sys.argv) == 5

model_path = sys.argv[1]
mode = sys.argv[2]
image_from_path = sys.argv[3]
image_to_path = sys.argv[4]

assert mode in ["-bl", "-bb", "-fl"]

image = Image.open(image_from_path).convert('RGB')
boxes = detect_logo(model_path, image, ProcessMode(mode),  0.7)
processed_image = process_image(image, boxes)
processed_image.save(image_to_path, "PNG")
