# Spotify Control - Controle de Música com Gestos e Voz

![SkipSpot em Ação](https://github.com/username/skipspot/raw/main/assets/skipspot-demo.gif)

SkipSpot é uma aplicação inovadora que combina reconhecimento de gestos e voz para controlar o Spotify. Com apenas movimentos da mão e comandos de voz, você pode controlar sua música sem precisar tocar no computador.

## 🚀 Funcionalidades

- 🙏 **Gestos com a Mão**:
  - Mão fechada: Pausar música
  - Sinal de 'V': Retomar música
  - Dedo apontando para direita: Pular música
  - Dedo apontando para esquerda: Voltar música
  - Dedo apontando para cima: Aumentar volume
  - Dedo apontando para baixo: Diminuir volume

- 🎤 **Comandos de Voz**:
  - "Pausar música"
  - "Tocar música"
  - "Pular música"
  - "Música anterior"
  - "Aumentar volume"
  - "Diminuir volume"

## 📋 Pré-requisitos

- Python 3.11 ou superior
- Spotify Premium instalado e em execução
- Web browser (Chrome, Firefox, etc.)
- Microfone para comandos de voz

## 📦 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/ricardobarbosrr/skipspot.git
cd skipspot
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure o Spotify:
   - Acesse o [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Clique em "Create an App"
   - Preencha os campos:
     - App Name: SkipSpot
     - Description: Controle de música com gestos e voz
     - Website: (opcional)
   - Clique em "Create"
   - Na aba "Settings":
     - Adicione "http://localhost:8080" em "Redirect URIs"
     - Copie o "Client ID" e "Client Secret"

4. Crie o arquivo `credentials.json`:
```json
{
    "client_id": "SEU_CLIENT_ID",
    "client_secret": "SEU_CLIENT_SECRET",
    "redirect_uri": "http://localhost:8080"
}
```

## 🎮 Como Usar

1. Execute o programa:
```bash
python skipspot.py
```

2. Selecione uma das opções:
   - 1: Capturar imagem de referência (para treinar novos gestos)
   - 2: Mostrar imagens de referência
   - 3: Iniciar reconhecimento de gestos
   - 4: Reconhecer comando de voz
   - 'q': Sair

3. Para comandos de voz:
   - Diga "sair", "voltar" ou "menu" para retornar ao menu principal
   - O sistema continuará ouvindo até você decidir sair

## 🛠️ Configurações

- **Limite de Gestos**:
  - `finger_threshold`: 0.15 (sensibilidade dos dedos)
  - `hand_threshold`: 0.25 (sensibilidade da mão)

- **Buffer de Reconhecimento**:
  - 15 frames para confirmar um gesto
  - 1 segundo de cooldown entre ações

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🙏 Agradecimentos

- [MediaPipe](https://google.github.io/mediapipe/) - Para detecção de mãos
- [Spotipy](https://spotipy.readthedocs.io/) - Para integração com o Spotify
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) - Para reconhecimento de voz
