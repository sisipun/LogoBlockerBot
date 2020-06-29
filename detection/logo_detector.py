import torch
from torchvision import transforms


def detect_logo(model_path, image, score_filter=0):
    model = torch.load(model_path, map_location=torch.device('cpu'))
    model.eval()

    prediction = model([transforms.ToTensor()(image)])[0]
    predict_boxes = prediction['boxes']
    predict_scores = prediction['scores']
    filtered_boxes = [box for i, box in enumerate(
        predict_boxes) if predict_scores[i] > score_filter]
    return filtered_boxes
