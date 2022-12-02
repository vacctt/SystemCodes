import torch
import cv2
import time
from torch.nn.functional import softmax
from torchvision import transforms
from torchvision.models import mobilenet_v2

class FaceClassification():
    
    def __init__(self,
                 camera_frame_rate = 20,
                 camera_capture_size=[224,224],
                 model_ouput_size=2,
                 model_to_load_path="/home/pi/Desktop/pytorch_models/model-prueba-v0.0.2.pth",
                 categories_output = {0 : 'drowsiness', 1 : 'no-drowsiness'}
                 ):    
        self.video_frame_capture = cv2.VideoCapture(0)
        self.video_frame_capture.set(cv2.CAP_PROP_FRAME_WIDTH, camera_capture_size[0])#Establecemos el ancho
        self.video_frame_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_capture_size[1])#Establecemos el alto
        self.video_frame_capture.set(cv2.CAP_PROP_FPS, camera_frame_rate)#Establecemos los frames/seg

        time.sleep(0.1)
        
        self.process_image = None
        self.model_trained = None
        self.model_output_size = model_ouput_size
        self.model_to_load_path = model_to_load_path
        self.categories = categories_output
        
    def initialize_model(self):
        
        self.process_image = transforms.Compose([
            transforms.ToTensor(),# Cada imagen la hacemos un tensor
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            # Normalizamos la imagen para que el modelo la acepte
        ])

        self.model_trained = mobilenet_v2(pretrained=True)
        self.model_trained.classifier=torch.nn.Sequential(
                torch.nn.Dropout(p=0.2, inplace=False),
                torch.nn.Linear(in_features=1280, out_features=self.model_output_size),
        )
        self.model_trained.load_state_dict(torch.load(self.model_to_load_path))
        self.model_trained.eval()
        torch.set_num_threads(3)
        
    def predict(self):
        model_predictions = []
        #Deshabilitamos el calculo de gradiente, para eficiencia de memoria    
        with torch.no_grad():
            with torch.inference_mode():
                while True:
                    model_predictions = []
                    isFrameOk, imageCapture = self.video_frame_capture.read()

                    if not isFrameOk:
                        raise("Error al inicializar la camara")


                    imageCaptureGray = cv2.cvtColor(imageCapture, cv2.COLOR_RGBA2GRAY)
                    imageCaptureRGB = cv2.cvtColor(imageCaptureGray, cv2.COLOR_GRAY2RGB)

                    imageTensorTransformed = self.process_image(imageCaptureRGB)#Transformamos la imagen
                    imageInputModel = imageTensorTransformed.unsqueeze(0)#Agregamos un mini-batch al principio

                    t = time.time()
                    modelOutput = self.model_trained(imageInputModel)
                    #print(time.time()-t)
                    probabilities = softmax(modelOutput[0], dim=0)

                    top_prob, top_id = torch.topk(probabilities, 1)
                    
                    model_predictions.append(self.categories[top_id[0].item()])
                    model_predictions.append(top_prob[0].item()*100)
                    
                    cv2.putText(imageCaptureRGB,
                                f"{self.categories[top_id[0].item()]}:{top_prob[0].item()*100:.2f}",
                                (20,20),
                                cv2.FONT_HERSHEY_PLAIN,
                                1,
                                (0,0,0)
                                ,1)
                    cv2.imshow("PREDICCIONES",cv2.resize(imageCaptureRGB,(720,480)))
                    cv2.waitKey(1)
                    return model_predictions