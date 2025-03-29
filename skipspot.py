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
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Limites ajustados para melhor reconhecimento
        self.hand_threshold = 0.25  # Para reconhecer mãos mais abertas
        self.finger_threshold = 0.15  # Para melhor reconhecimento de dedos
        self.angle_threshold = 15  # Ângulo em graus para considerar um dedo levantado
        
        # Buffer para confirmar gestos
        self.gesture_buffer = []
        self.buffer_size = 10  # Reduzido para respostas mais rápidas
        self.cooldown = 0
        self.cooldown_frames = 30  # 1 segundo a 30 FPS
        
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
                self.mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS
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

    def calculate_angle(self, point1, point2, point3):
        """
        Calcula o ângulo entre três pontos
        """
        a = np.array([point1.x, point1.y])
        b = np.array([point2.x, point2.y])
        c = np.array([point3.x, point3.y])
        
        ba = a - b
        bc = c - b
        
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.degrees(np.arccos(cosine_angle))
        
        return angle

    def is_finger_straight(self, finger_tip, finger_dip, finger_pip, finger_mcp):
        """
        Verifica se um dedo está esticado usando ângulos
        """
        angle1 = self.calculate_angle(finger_tip, finger_dip, finger_pip)
        angle2 = self.calculate_angle(finger_dip, finger_pip, finger_mcp)
        
        return angle1 < self.angle_threshold and angle2 < self.angle_threshold

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

        # Verifica se estamos em cooldown
        if self.cooldown > 0:
            self.cooldown -= 1
            return None

        # Função auxiliar para verificar se um dedo está levantado
        def is_finger_up(finger_tip, wrist):
            return finger_tip.y < wrist.y - self.hand_threshold

        # Função auxiliar para verificar se um dedo está fechado
        def is_finger_down(finger_tip, wrist):
            return finger_tip.y > wrist.y + self.hand_threshold

        # Verifica a posição dos dedos
        thumb_up = is_finger_up(thumb_tip, wrist)
        index_up = is_finger_up(index_tip, wrist)
        pinky_up = is_finger_up(pinky_tip, wrist)
        ring_up = is_finger_up(ring_tip, wrist)

        # 1. Dedão levantado (play)
        if thumb_up and not index_up and not pinky_up and not ring_up:
            self.gesture_buffer.append('play')

        # 2. Indicador levantado (pause)
        elif not thumb_up and index_up and not pinky_up and not ring_up:
            self.gesture_buffer.append('pause')

        # 3. Mínimo levantado (aumentar volume)
        elif not thumb_up and not index_up and not pinky_up and ring_up:
            self.gesture_buffer.append('volume_up')

        # 4. Dedo do lado do mínimo levantado (diminuir volume)
        elif not thumb_up and not index_up and pinky_up and not ring_up:
            self.gesture_buffer.append('volume_down')

        # Se o buffer estiver cheio, verifica a maioria
        if len(self.gesture_buffer) >= self.buffer_size:
            most_common = max(set(self.gesture_buffer), key=self.gesture_buffer.count)
            if self.gesture_buffer.count(most_common) >= self.buffer_size * 0.6:  # 60% de confiança
                self.gesture_buffer = []  # Limpa o buffer
                self.cooldown = self.cooldown_frames  # Inicia cooldown
                return most_common
            else:
                self.gesture_buffer.pop(0)  # Remove o mais antigo

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

    def start_recognition(self):
        """
        Inicia o reconhecimento de gestos e voz
        """
        print("\nModo de Reconhecimento de Gestos")
        print("--------------------------------")
        print("(Diga 'sair' para voltar ao menu principal)")

        while True:
            # Captura o frame da câmera
            ret, frame = self.cap.read()
            if not ret:
                print("Erro ao capturar frame")
                break

            # Converte para RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Detecta mãos
            results = self.hands.process(image)

            # Desenha os landmarks
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        image,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS
                    )

            # Reconhece gesto
            gesture = self.recognize_gesture(results)
            if gesture:
                print(f"Gesto reconhecido: {gesture}")
                self.execute_action(gesture)

            # Mostra a imagem
            cv2.imshow('SkipSpot - Controle de Música', image)

            # Verifica se o usuário quer sair
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Limpa recursos
        self.cap.release()
        cv2.destroyAllWindows()

    def run(self):
        """
        Inicia o programa principal
        """
        print("\nSkipSpot - Controle de Música")
        print("------------------------------")
        print("1. Iniciar reconhecimento de gestos")
        print("2. Reconhecer comando de voz")
        print("'q' - Sair")

        while True:
            choice = input("\nEscolha uma opção: ")

            if choice == '1':
                self.start_recognition()
            elif choice == '2':
                self.recognize_voice_command()
            elif choice.lower() == 'q':
                break
            else:
                print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    trainer = MotionTrainer()
    trainer.run()
