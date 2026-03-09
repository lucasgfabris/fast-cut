# Python Video Cuts

![GitHub repo size](https://img.shields.io/github/repo-size/lucasgfabris/python-video-cuts?style=for-the-badge)
![GitHub language count](https://img.shields.io/github/languages/count/lucasgfabris/python-video-cuts?style=for-the-badge)

> Sistema inteligente que baixa videos de canais autorizados do YouTube e gera automaticamente cortes otimizados para YouTube Shorts, TikTok e Instagram Reels. Analisa audio e video para identificar os melhores momentos.

<img src="imagem.png" alt="Python Video Cuts">

### Ajustes e melhorias

O projeto ainda esta em desenvolvimento e as proximas atualizacoes serao voltadas para as seguintes tarefas:

- [x] Download paralelo via yt-dlp
- [x] Analise de audio e video (librosa, OpenCV)
- [x] Corte e otimizacao com FFmpeg
- [x] Legendas automaticas com faster-whisper
- [ ] Interface grafica
- [ ] Suporte a mais plataformas

## Pre-requisitos

Antes de comecar, verifique se voce atendeu aos seguintes requisitos:

- Python 3.11 ou superior
- FFmpeg instalado no sistema (ou use `scripts/install_ffmpeg.py` no Windows)
- Node.js/npm (opcional, para scripts do package.json)

## Instalando

Para instalar o Python Video Cuts, siga estas etapas:

```bash
git clone https://github.com/lucasgfabris/python-video-cuts.git
cd python-video-cuts
python scripts/setup.py
cp .env.example .env
```

Edite o `.env` com os IDs dos canais autorizados:

```env
AUTHORIZED_CHANNELS=UC_x5XG1OV2P6uZZ5FSM9Ttw,UCrAav_9B-1za5hFPfq5Vx-w
MIN_CLIP_DURATION=15
MAX_CLIP_DURATION=60
CLIPS_PER_VIDEO=3
```

## Usando

Para usar o Python Video Cuts, siga estas etapas:

```bash
# Sistema completo
python main.py

# Maximo 3 videos por canal
python main.py --max-videos 3

# Processar um video especifico
python main.py --video "https://www.youtube.com/watch?v=VIDEO_ID"

# Listar canais configurados
python main.py --list-channels

# Teste do sistema
python main.py --test
```

### Limites de Duracao

| Plataforma | Duracao | Formato |
|------------|---------|---------|
| YouTube Shorts | Max 60s | 9:16 |
| TikTok | 15-60s | 9:16 |
| Instagram Reels | 15-60s | 9:16 |

### Plataformas Customizadas

Crie um arquivo `platforms.json` para adicionar novas plataformas:

```json
{
    "twitter_video": {
        "resolution": [1280, 720],
        "fps": 30,
        "format": "mp4",
        "max_duration": 140
    }
}
```

## Tecnologias

| Categoria | Tecnologias |
|-----------|-------------|
| Linguagem | Python 3.11+ |
| Download | yt-dlp |
| Processamento | FFmpeg, OpenCV, MoviePy |
| Analise de audio | librosa |
| Transcricao | faster-whisper |
| Qualidade | black, isort, flake8, mypy, pytest |

## Estrutura do Projeto

```
python-video-cuts/
├── main.py                     # Entry point (CLI)
├── src/fast_cut/
│   ├── core/                   # Nucleo do sistema
│   │   ├── config.py           # Configuracao
│   │   ├── protocols.py        # Interfaces dos servicos
│   │   ├── system.py           # Facade + factory
│   │   └── pipeline.py         # Orquestracao do fluxo
│   ├── services/               # Implementacoes
│   │   ├── downloader.py       # Download via yt-dlp
│   │   ├── analyzer.py         # Analise de audio/video
│   │   └── cutter.py           # Corte com FFmpeg
│   └── utils/
│       └── ffmpeg.py           # Utilitarios FFmpeg
└── tests/                      # Testes unitarios
```

## Contribuindo

Para contribuir com Python Video Cuts, siga estas etapas:

1. Bifurque este repositorio.
2. Crie um branch: `git checkout -b <nome_branch>`.
3. Faca suas alteracoes e confirme-as: `git commit -m '<mensagem_commit>'`
4. Envie para o branch original: `git push origin <nome_branch>`
5. Crie a solicitacao de pull.

O sistema de pre-commit garantira que seu codigo atende aos padroes de qualidade.

## Aviso Legal

- Use apenas com canais autorizados
- Respeite direitos autorais
- Sistema fornecido "como esta"

## Licenca

Esse projeto esta sob licenca MIT.
