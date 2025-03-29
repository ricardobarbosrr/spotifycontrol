import cv2
import numpy as np
import time
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import mediapipe as mp
from collections import deque
import pandas as pd
import webbrowser
import os
import speech_recognition as sr

mp_hands = mp.solutions.hands

class MotionTrainer:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.recording = False
        self.current_action = None
        self.training_data = {}
        self.current_frame = None
        self.frame_count = 0
        
        # Inicializa o MediaPipe
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Buffer para reconhecimento de ações
        self.action_buffer = deque(maxlen=15)  # Aumentado o buffer para 15 frames
        self.last_action_time = time.time()
        self.action_cooldown = 1.0  # 1 segundo de cooldown entre ações
        
        # Limite para gestos específicos
        self.finger_threshold = 0.15  # Aumentado o limite para dedos
        self.hand_threshold = 0.25    # Aumentado o limite para mão
        
        # Inicializa o reconhecimento de voz
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Carrega as credenciais do Spotify
        with open("credentials.json", "r") as f:
            credentials = json.load(f)
        
        # Configura a autenticação do Spotify
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            redirect_uri=credentials["redirect_uri"],
            scope="user-modify-playback-state user-read-playback-state user-read-currently-playing"
        ))
        
        # Verifica se está autenticado
        try:
            self.sp.current_user()
            print("\nAutenticação bem-sucedida!")
        except Exception as e:
            print("\nErro de autenticação. Por favor, autorize o aplicativo:")
            print(f"Erro: {str(e)}")
            webbrowser.open(self.sp.auth_manager.get_authorize_url())
            input("\nPressione Enter após autorizar...")
            # Tenta novamente após autorização
            try:
                self.sp.current_user()
                print("\nAutenticação bem-sucedida!")
            except Exception as e:
                print(f"Erro após tentar novamente: {str(e)}")
                exit(1)

    def detect_hands(self, frame):
        # Inverte a imagem horizontalmente para que fique natural
        frame = cv2.flip(frame, 1)
        
        # Converte a imagem para RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        
        # Processa a imagem
        results = self.hands.process(image)
        
        # Converte de volta para BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Desenha as landmarks
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )
        
        return image, results

    def extract_features(self, results):
        try:
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]  # Pega a primeira mão detectada
                features = []
                for landmark in hand_landmarks.landmark:
                    features.extend([landmark.x, landmark.y, landmark.z])
                return features
            return None
            
        except Exception as e:
            print(f"Erro ao extrair features: {str(e)}")
            return None

    def recognize_gesture(self, results):
        if not results.multi_hand_landmarks:
            return None

        # Pega os landmarks da mão
        hand_landmarks = results.multi_hand_landmarks[0]
        wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
        thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]

        # Gestos específicos
        # 1. Mão de Stop (todos os dedos fechados)
        if (abs(thumb_tip.y - wrist.y) < self.hand_threshold and
            abs(index_tip.y - wrist.y) < self.hand_threshold and
            abs(middle_tip.y - wrist.y) < self.hand_threshold and
            abs(ring_tip.y - wrist.y) < self.hand_threshold and
            abs(pinky_tip.y - wrist.y) < self.hand_threshold):
            return 'pause'

        # 2. Sinal de 'V' (polegar e indicador levantados)
        if (abs(thumb_tip.y - wrist.y) < self.hand_threshold and
            abs(index_tip.y - wrist.y) < self.hand_threshold and
            abs(middle_tip.y - wrist.y) > self.hand_threshold and
            abs(ring_tip.y - wrist.y) > self.hand_threshold and
            abs(pinky_tip.y - wrist.y) > self.hand_threshold):
            return 'play'

        # 3. Dedo apontando para a direita (pular música)
        if (abs(thumb_tip.y - wrist.y) > self.hand_threshold and
            abs(middle_tip.y - wrist.y) > self.hand_threshold and
            abs(ring_tip.y - wrist.y) > self.hand_threshold and
            abs(pinky_tip.y - wrist.y) > self.hand_threshold and
            index_tip.x > wrist.x + self.finger_threshold):
            return 'skip'

        # 4. Dedo apontando para a esquerda (voltar música)
        if (abs(thumb_tip.y - wrist.y) > self.hand_threshold and
            abs(middle_tip.y - wrist.y) > self.hand_threshold and
            abs(ring_tip.y - wrist.y) > self.hand_threshold and
            abs(pinky_tip.y - wrist.y) > self.hand_threshold and
            index_tip.x < wrist.x - self.finger_threshold):
            return 'previous'

        # 5. Dedo apontando para cima (aumentar volume)
        if (abs(thumb_tip.x - wrist.x) > self.hand_threshold and
            abs(middle_tip.x - wrist.x) > self.hand_threshold and
            abs(ring_tip.x - wrist.x) > self.hand_threshold and
            abs(pinky_tip.x - wrist.x) > self.hand_threshold and
            index_tip.y < wrist.y - self.finger_threshold):
            return 'volume_up'

        # 6. Dedo apontando para baixo (diminuir volume)
        if (abs(thumb_tip.x - wrist.x) > self.hand_threshold and
            abs(middle_tip.x - wrist.x) > self.hand_threshold and
            abs(ring_tip.x - wrist.x) > self.hand_threshold and
            abs(pinky_tip.x - wrist.x) > self.hand_threshold and
            index_tip.y > wrist.y + self.finger_threshold):
            return 'volume_down'

        return None

    def recognize_voice_command(self):
        """
        Reconhece comandos de voz em loop até o usuário decidir sair
        """
        print("\nModo de Reconhecimento de Voz")
        print("-----------------------------")
        print("(Diga 'sair' para voltar ao menu principal)")

        while True:
            try:
                with self.microphone as source:
                    print("\nAjustando nível de ruído... (1 segundo)")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    print("\nAguardando comando de voz...")
                    audio = self.recognizer.listen(source, timeout=5)

                print("\nProcessando comando...")
                command = self.recognizer.recognize_google(audio, language='pt-BR')
                print(f"Comando reconhecido: {command}")

                # Converte o comando para minúsculas e remove espaços extras
                command = command.lower().strip()

                # Verifica se o usuário quer sair
                if command in ['sair', 'voltar', 'menu']:
                    print("\nVoltando ao menu principal...")
                    return None

                # Mapeia comandos de voz para ações
                voice_commands = {
                    'pause': ['pause', 'pausar', 'stop', 'parar', 'parar música'],
                    'play': ['play', 'tocar', 'retomar', 'continuar'],
                    'skip': ['skip', 'pular', 'próxima', 'próxima música'],
                    'previous': ['previous', 'anterior', 'voltar', 'música anterior'],
                    'volume_up': ['volume up', 'aumentar volume', 'aumentar o volume', 'volume mais alto'],
                    'volume_down': ['volume down', 'diminuir volume', 'diminuir o volume', 'volume mais baixo']
                }

                # Verifica se o comando corresponde a algum dos comandos conhecidos
                for action, commands in voice_commands.items():
                    if any(cmd in command for cmd in commands):
                        self.execute_action(action)
                        break
                else:
                    print("\nComando não reconhecido!")

            except sr.WaitTimeoutError:
                print("\nTempo limite excedido. Nenhum comando detectado.")
                continue
            except sr.UnknownValueError:
                print("\nNão foi possível entender o comando.")
                continue
            except sr.RequestError as e:
                print(f"\nErro ao processar o comando: {str(e)}")
                continue

    def execute_action(self, action):
        try:
            # Verifica se o Spotify está em execução
            current_playback = self.sp.current_playback()
            if not current_playback:
                print("Spotify não está em execução ou não está conectado")
                return

            if action == 'skip':
                self.sp.next_track()
                print("Pulando música...")
            elif action == 'previous':
                self.sp.previous_track()
                print("Voltando música...")
            elif action == 'pause':
                if current_playback['is_playing']:
                    self.sp.pause_playback()
                    print("Pausando música...")
            elif action == 'play':
                if not current_playback['is_playing']:
                    self.sp.start_playback()
                    print("Retomando música...")
            elif action == 'volume_up':
                current_volume = current_playback['device']['volume_percent']
                new_volume = min(current_volume + 10, 100)
                self.sp.volume(new_volume)
                print(f"Aumentando volume para {new_volume}%")
            elif action == 'volume_down':
                current_volume = current_playback['device']['volume_percent']
                new_volume = max(current_volume - 10, 0)
                self.sp.volume(new_volume)
                print(f"Diminuindo volume para {new_volume}%")

        except Exception as e:
            print(f"Erro ao executar ação: {str(e)}")
            # Se houver erro de autenticação, tenta novamente
            if "401" in str(e):
                print("\nErro de autenticação. Por favor, autorize o aplicativo:")
                webbrowser.open(self.sp.auth_manager.get_authorize_url())
                input("\nPressione Enter após autorizar...")
            elif "403" in str(e):
                print("\nErro de permissão. Por favor, verifique se:")
                print("1. O Spotify está em execução")
                print("2. Você está conectado à uma conta")
                print("3. A conta tem uma assinatura premium")

    def capture_reference_image(self, action_name, output_dir="reference_images"):
        """
        Captura uma imagem de referência para um gesto específico
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"\nCapturando imagem de referência para '{action_name}'...")
        print("(Pressione 's' para capturar, 'q' para sair)")

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            # Inverte a imagem horizontalmente
            frame = cv2.flip(frame, 1)
            
            # Processa a imagem
            processed_frame, results = self.detect_hands(frame)

            # Mostra instruções na tela
            cv2.putText(processed_frame, f"Posicione a mão para '{action_name}'", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(processed_frame, "Pressione 's' para capturar", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow("Captura de Referência", processed_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                # Salva a imagem
                filename = os.path.join(output_dir, f"{action_name}_reference.jpg")
                cv2.imwrite(filename, processed_frame)
                print(f"Imagem salva em: {filename}")
                break
            elif key == ord('q'):
                break

        cv2.destroyAllWindows()

    def show_reference_images(self):
        """
        Mostra todas as imagens de referência disponíveis
        """
        reference_dir = "reference_images"
        if not os.path.exists(reference_dir):
            print("Nenhuma imagem de referência encontrada!")
            return

        print("\nImagens de Referência Disponíveis:")
        print("--------------------------------")
        for filename in os.listdir(reference_dir):
            if filename.endswith(".jpg"):
                print(f"- {filename}")

    def start_recognition(self):
        print("\nModo de Reconhecimento")
        print("----------------------")
        print("Monitorando movimentos...")
        print("(Pressione 'q' para sair)")

        last_wrist_pos = None

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            processed_frame, results = self.detect_hands(frame)
            recognized_action = self.recognize_gesture(results)

            # Se reconheceu uma ação, adiciona ao buffer
            if recognized_action:
                self.action_buffer.append(recognized_action)
                
                # Se a maioria do buffer concorda com a ação e não está em cooldown
                if (self.action_buffer.count(recognized_action) > len(self.action_buffer) * 0.6 and
                    time.time() - self.last_action_time > self.action_cooldown):
                    
                    # Executa a ação
                    self.execute_action(recognized_action)
                    self.last_action_time = time.time()

            # Mostra o painel de reconhecimento
            if processed_frame is not None:
                cv2.putText(processed_frame, f"Status: {'Movimento detectado' if results.multi_hand_landmarks else 'Sem movimento'}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                           (0, 255, 0) if results.multi_hand_landmarks else (0, 0, 255), 2)
                
                # Mostra as ações no buffer
                buffer_text = "Buffer: " + ", ".join(list(self.action_buffer))
                cv2.putText(processed_frame, buffer_text, 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Mostra as linhas de referência para os gestos
                # Linha para dedo apontando
                cv2.line(processed_frame, (int(0.5 * processed_frame.shape[1]), 0),
                         (int(0.5 * processed_frame.shape[1]), processed_frame.shape[0]),
                         (255, 0, 0), 2)
                
                # Linha para volume up/down
                cv2.line(processed_frame, (0, int(0.3 * processed_frame.shape[0])),
                         (processed_frame.shape[1], int(0.3 * processed_frame.shape[0])),
                         (0, 255, 0), 2)
                cv2.line(processed_frame, (0, int(0.7 * processed_frame.shape[0])),
                         (processed_frame.shape[1], int(0.7 * processed_frame.shape[0])),
                         (0, 0, 255), 2)
                
                cv2.imshow("SkipSpot - Reconhecimento", processed_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

    def run(self):
        print("\nSkipSpot - Modo Reconhecimento")
        print("-----------------------------")
        print("1. Capturar imagem de referência")
        print("2. Mostrar imagens de referência")
        print("3. Iniciar reconhecimento")
        print("4. Reconhecer comando de voz")
        print("(Pressione 'q' para sair)")
        
        while True:
            choice = input("\nSelecione uma opção (1-4): ")
            
            if choice == '1':
                print("\nGestos disponíveis para capturar:")
                print("1. Mão fechada (Stop)")
                print("2. Sinal de 'V'")
                print("3. Dedo apontando para direita")
                print("4. Dedo apontando para esquerda")
                print("5. Dedo apontando para cima")
                print("6. Dedo apontando para baixo")
                
                action_choice = input("\nSelecione o gesto (1-6): ")
                action_names = {
                    '1': 'stop',
                    '2': 'v_sign',
                    '3': 'right_point',
                    '4': 'left_point',
                    '5': 'up_point',
                    '6': 'down_point'
                }
                
                if action_choice in action_names:
                    self.capture_reference_image(action_names[action_choice])
                else:
                    print("Opção inválida!")
            
            elif choice == '2':
                self.show_reference_images()
            
            elif choice == '3':
                self.start_recognition()
                break
            
            elif choice == '4':
                self.recognize_voice_command()
            
            elif choice == 'q':
                break

if __name__ == "__main__":
    trainer = MotionTrainer()
    trainer.run()
