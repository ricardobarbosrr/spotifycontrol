# SkipSpot - Controle de Música por Gestos

O SkipSpot é uma aplicação que permite controlar o Spotify usando gestos de mão e comandos de voz. Com ele, você pode pausar, retomar, pular músicas e ajustar o volume sem precisar tocar no seu dispositivo.

## 🎮 Gestos Disponíveis

### Controle por Gestos de Mão

| Dedo | Ação |
|------|------|
| Dedão | Play (Tocar música) |
| Indicador | Pause (Pausar música) |
| Mínimo (anular) | Aumentar Volume |
| Dedo do lado do mínimo | Diminuir Volume |

### Como usar os gestos
1. Mantenha apenas um dedo levantado por vez
2. Os outros dedos devem estar completamente fechados
3. Mantenha a mão parada por alguns segundos para que o sistema reconheça o gesto

### Comandos de Voz
- "Pausar música"
- "Tocar música"
- "Pular música"
- "Música anterior"
- "Aumentar volume"
- "Diminuir volume"

## 🛠️ Requisitos

- Python 3.8 ou superior
- Webcam
- Conta do Spotify

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/skipspot.git
cd skipspot
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure suas credenciais do Spotify:
   - Vá para o [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Crie uma nova aplicação
   - Copie o Client ID e Client Secret
   - Crie um arquivo `credentials.json` com o seguinte formato:
   ```json
   {
       "client_id": "seu_client_id",
       "client_secret": "seu_client_secret",
       "redirect_uri": "http://localhost:8080"
   }
   ```

4. Execute o programa:
```bash
python skipspot.py
```

## 🎮 Como Usar

1. Execute o programa:
```bash
python skipspot.py
```

2. Escolha uma opção:
   - 1: Iniciar reconhecimento de gestos
   - 2: Reconhecer comando de voz
   - 'q': Sair

3. Para gestos de mão:
   - Faça os gestos com apenas um dedo levantado
   - Mantenha a mão parada por alguns segundos
   - O sistema tem um cooldown de 1 segundo entre cada ação

4. Para comandos de voz:
   - Diga um dos comandos listados acima
   - O sistema continuará ouvindo até você dizer "sair"

## 📝 Notas Importantes

- Mantenha a mão na frente da câmera
- Faça os gestos lentamente e mantenha-os por alguns segundos
- O sistema tem um cooldown de 1 segundo entre cada ação
- Você pode alternar entre controle por gestos e controle por voz a qualquer momento

## 📱 Suporte

Se encontrar algum problema ou tiver sugestões, por favor, abra uma issue no repositório.

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

---

Desenvolvido por Ricardo Barbosa

[github](https://github.com/ricardobarbosrr)

[linkedin](https://www.linkedin.com/in/ricardobarbosrr/)
