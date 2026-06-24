from tensorflow.keras.models import load_model
import cv2
import numpy as np

CAPTCHA_LENGTH = 5
CHARACTERS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

model = load_model("captcha_model.keras")

def preprocess(img):
    img = cv2.resize(img, (200, 50))
    img = cv2.GaussianBlur(img, (5,5), 0)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    img = img / 255.0
    return img.reshape(50, 200, 1)

def predict(path):
    img = cv2.imread(path, 0)
    img = preprocess(img)
    img = np.expand_dims(img, 0)

    preds = model.predict(img)

    result = ""
    for i in range(CAPTCHA_LENGTH):
        result += CHARACTERS[np.argmax(preds[i][0])]

    return result

print(predict(r"D:\DistictCaptcha\resolved_captchaset\dc7e128c8c2ed1e3edfd4233d215240c.png"))