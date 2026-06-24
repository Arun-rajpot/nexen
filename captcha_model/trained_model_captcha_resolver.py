# import tensorflow as tf
# from tensorflow.keras import layers, models
# import numpy as np
# import cv2
# import os
# from sklearn.model_selection import train_test_split
# from datetime import datetime
#
# CAPTCHA_LENGTH = 5
# CHARACTERS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
#
# def encode_label(text):
#     return [CHARACTERS.index(c) for c in text]
#
# def decode_label(label):
#     return ''.join(CHARACTERS[c] for c in label)
#
# def load_data(folder):
#     X, y = [], []
#     for filename in os.listdir(folder):
#         if filename.endswith('.png'):
#             label = filename.split('.')[0]
#             img = cv2.imread(os.path.join(folder, filename), cv2.IMREAD_GRAYSCALE)
#             img = cv2.resize(img, (200, 50)) / 255.0
#             X.append(img.reshape(50, 200, 1))
#             y.append(encode_label(label))
#     return np.array(X), np.array(y)
#
# # Load data
# X, y = load_data(r'D:\\DistictCaptcha\\captcha_downloads\\')
# y = tf.keras.utils.to_categorical(y, num_classes=len(CHARACTERS))
# X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.1)
#
# # Define model
# def build_model():
#     inputs = layers.Input(shape=(50, 200, 1))
#     x = layers.Conv2D(32, (3, 3), activation='relu', padding='same')(inputs)
#     x = layers.MaxPooling2D((2, 2))(x)
#     x = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(x)
#     x = layers.MaxPooling2D((2, 2))(x)
#     x = layers.Flatten()(x)
#     x = layers.Dense(1024, activation='relu')(x)
#
#     outputs = [layers.Dense(len(CHARACTERS), activation='softmax')(x) for _ in range(CAPTCHA_LENGTH)]
#     model = models.Model(inputs=inputs, outputs=outputs)
#     model.compile(
#         optimizer='adam',
#         loss=['categorical_crossentropy'] * CAPTCHA_LENGTH,
#         metrics=['accuracy'] * CAPTCHA_LENGTH
#     )
#     return model
#
#
# model = build_model()
# model.fit(X_train, [y_train[:, i] for i in range(CAPTCHA_LENGTH)],
#           validation_data=(X_val, [y_val[:, i] for i in range(CAPTCHA_LENGTH)]),
#           epochs=20, batch_size=32)
# timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# model.save(f'captcha_model_updated_{timestamp}.h5')
import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np
import cv2
import os
from sklearn.model_selection import train_test_split

# ================= CONFIG =================
CAPTCHA_LENGTH = 5
CHARACTERS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
IMG_WIDTH = 200
IMG_HEIGHT = 50
DATASET_PATH = r'D:\DistictCaptcha\captcha_downloads\\'
MODEL_PATH = "captcha_model.keras"
# ==========================================

# ================= ENCODE =================
def encode_label(text):
    encoded = []
    for c in text:
        if c not in CHARACTERS:
            return None
        encoded.append(CHARACTERS.index(c))
    return encoded

# ================= PREPROCESS =================
def preprocess(img):
    img = cv2.resize(img, (IMG_WIDTH, IMG_HEIGHT))
    img = cv2.GaussianBlur(img, (5,5), 0)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((2,2), np.uint8)
    img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    img = img / 255.0
    return img.reshape(IMG_HEIGHT, IMG_WIDTH, 1)

# ================= LOAD =================
def load_data(folder):
    X, y = [], []

    for file in os.listdir(folder):
        if not file.endswith(".png"):
            continue

        label = file.split(".")[0]
        if len(label) != CAPTCHA_LENGTH:
            continue

        encoded = encode_label(label)
        if encoded is None:
            continue

        img = cv2.imread(os.path.join(folder, file), cv2.IMREAD_GRAYSCALE)
        img = preprocess(img)

        X.append(img)
        y.append(encoded)

    return np.array(X), np.array(y)

# ================= MODEL =================
def build_model():
    inputs = layers.Input(shape=(IMG_HEIGHT, IMG_WIDTH, 1))

    x = layers.Conv2D(32, 3, activation='relu', padding='same')(inputs)
    x = layers.MaxPooling2D(2)(x)

    x = layers.Conv2D(64, 3, activation='relu', padding='same')(x)
    x = layers.MaxPooling2D(2)(x)

    x = layers.Flatten()(x)
    x = layers.Dense(512, activation='relu')(x)

    # 🔥 NO slicing, direct 5 outputs
    outputs = []
    for _ in range(CAPTCHA_LENGTH):
        outputs.append(
            layers.Dense(len(CHARACTERS), activation='softmax')(x)
        )

    model = models.Model(inputs, outputs)

    model.compile(
        optimizer='adam',
        loss=['categorical_crossentropy'] * CAPTCHA_LENGTH,
        metrics=['accuracy'] * CAPTCHA_LENGTH
    )

    return model

# ================= TRAIN =================
def train():
    X, y = load_data(DATASET_PATH)

    X_train, X_val, y_train_raw, y_val_raw = train_test_split(X, y, test_size=0.1)

    y_train, y_val = [], []

    for i in range(CAPTCHA_LENGTH):
        y_train.append(tf.keras.utils.to_categorical(y_train_raw[:, i], len(CHARACTERS)))
        y_val.append(tf.keras.utils.to_categorical(y_val_raw[:, i], len(CHARACTERS)))

    model = build_model()

    model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=30,
        batch_size=32
    )

    model.save(MODEL_PATH)
    print("✅ Model saved")

if __name__ == "__main__":
    train()