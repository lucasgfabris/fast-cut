# Fast Cut - Sistema de Geração Automática de Cortes

Sistema inteligente que baixa vídeos de canais autorizados do YouTube e gera automaticamente cortes otimizados para **YouTube Shorts**, **TikTok** e **Instagram Reels**.

## Características

- **100% Gratuito** - Não usa APIs pagas
- **Totalmente Automático** - Identifica os melhores momentos para corte
- **Multi-plataforma** - Otimiza para YouTube Shorts, TikTok, Instagram Reels (e plataformas customizadas)
- **Inteligente** - Analisa áudio, vídeo e detecta momentos de alta energia
- **Seguro** - Apenas canais autorizados via variáveis de ambiente
- **Rápido** - Downloads e processamento paralelo via ThreadPoolExecutor
- **Cross-platform** - Funciona em Windows, Linux e macOS
- **Testável** - Arquitetura com DI, Protocols e 31 testes unitários
- **Extensível** - Plataformas configuráveis via JSON, serviços plugáveis via Protocols

## Instalação Rápida

```bash
# Clone o projeto
git clone <seu-repositorio>
cd fast-cut

# Configuração automática
python scripts/setup.py

# Configure os canais no .env
cp .env.example .env
# Edite o .env com seus canais autorizados

# Execute um teste
make run-test
```

## Comandos de Desenvolvimento

```bash
# Configuração inicial
make install-dev        # Instala dependências de desenvolvimento
make setup-hooks        # Configura pre-commit hooks

# Qualidade de código
make format             # Formata código (black + isort)
make lint               # Executa linting (flake8)
make type-check         # Verifica tipos (mypy)
make check              # Executa todas as verificações

# Testes
make test               # Executa testes unitários

# Execução
make run                # Executa o sistema
make run-test           # Testa o sistema
make run-channels       # Lista canais configurados

# Limpeza
make clean              # Remove arquivos temporários
make clear              # Limpa output/ e temp/
```

## Configuração

### Arquivo .env
```env
# Canais autorizados (obrigatório)
AUTHORIZED_CHANNELS=UC_x5XG1OV2P6uZZ5FSM9Ttw,UCrAav_9B-1za5hFPfq5Vx-w

# Configurações de corte
MIN_CLIP_DURATION=15
MAX_CLIP_DURATION=60
CLIPS_PER_VIDEO=3

# Configurações de análise
ENERGY_THRESHOLD=0.7
SILENCE_THRESHOLD=-40

# Plataformas customizadas (opcional)
# PLATFORMS_FILE=./platforms.json
```

### Plataformas Customizadas

Crie um arquivo `platforms.json` para adicionar novas plataformas sem alterar o código:

```json
{
    "youtube_shorts": {
        "resolution": [1080, 1920],
        "fps": 30,
        "format": "mp4",
        "max_duration": 60
    },
    "twitter_video": {
        "resolution": [1280, 720],
        "fps": 30,
        "format": "mp4",
        "max_duration": 140
    }
}
```

## Arquitetura

```
fast-cut/
├── main.py                     # Entry point (CLI)
├── src/fast_cut/
│   ├── core/                   # Núcleo do sistema
│   │   ├── config.py           # Config injetável (dataclass + from_env)
│   │   ├── types.py            # Tipos e estruturas de dados
│   │   ├── protocols.py        # Interfaces (Protocols) para serviços
│   │   ├── system.py           # Facade + factory create_system()
│   │   ├── pipeline.py         # PipelineOrchestrator (download→análise→corte)
│   │   ├── file_manager.py     # Gerenciamento de arquivos e diretórios
│   │   └── reporter.py         # Formatação de relatórios
│   ├── services/               # Implementações dos serviços
│   │   ├── downloader.py       # Download paralelo via yt-dlp
│   │   ├── analyzer.py         # Análise de áudio + visual (librosa, opencv)
│   │   └── cutter.py           # Corte e otimização (FFmpeg)
│   └── utils/
│       └── ffmpeg.py           # FFmpeg utils (cross-platform)
├── tests/
│   ├── conftest.py             # Fixtures compartilhadas
│   └── unit/                   # Testes unitários
│       ├── test_config.py
│       ├── test_types.py
│       ├── test_file_manager.py
│       └── test_pipeline.py
├── examples/
│   └── platforms.json          # Exemplo de plataformas customizadas
├── scripts/
│   ├── install_ffmpeg.py       # Instalação automática do FFmpeg
│   ├── setup.py                # Configuração inicial do projeto
│   └── validate.py             # Validação de qualidade do código
├── pyproject.toml
└── Makefile
```

### Diagrama de Dependências

```
main.py (CLI)
  └── FastCutSystem (facade)
        ├── PipelineOrchestrator (fluxo paralelo)
        │     ├── Downloader (Protocol) ← VideoDownloader
        │     ├── Analyzer (Protocol)   ← VideoAnalyzer
        │     └── Cutter (Protocol)     ← VideoCutter
        ├── FileManager (I/O)
        └── Reporter (output)
```

### Princípios Aplicados

- **Dependency Injection**: todos os serviços recebem Config por construtor
- **Protocols (interfaces)**: serviços implementam contratos definidos em `protocols.py`
- **Factory Pattern**: `create_system()` monta o sistema com implementações padrão
- **Facade**: `FastCutSystem` expõe API simples, delega para componentes internos
- **Logging estruturado**: `logging` em vez de `print()`, com níveis e formatação configuráveis
- **Processamento paralelo**: `ThreadPoolExecutor` para downloads e processamento de vídeos

## Como Usar

### Execução Básica
```bash
# Sistema completo
python main.py

# Máximo 3 vídeos por canal
python main.py --max-videos 3

# Usar vídeos existentes
python main.py --skip-download

# Processar um vídeo específico (link do YouTube)
python main.py --video "https://www.youtube.com/watch?v=VIDEO_ID"

# Ou processar um arquivo local
python main.py --video "caminho/do/video.mp4"

# Listar canais
python main.py --list-channels

# Teste do sistema
python main.py --test

# Limpar pastas output/ e temp/
python main.py --clear

# Log detalhado (debug)
python main.py --verbose
```

## Limites de Duração

- **YouTube Shorts**: Máximo 60 segundos (9:16)
- **TikTok**: 15-60 segundos (9:16)
- **Instagram Reels**: 15-60 segundos (9:16)

## Travas de Qualidade

### Pre-commit Hooks
- **Black**: Formatação automática
- **isort**: Organização de imports
- **Flake8**: Linting
- **MyPy**: Verificação de tipos

### Testes
```bash
# Executa testes unitários
python -m pytest tests/ -v

# Com cobertura
python -m pytest tests/ --cov=fast_cut
```

## Aviso Legal

- Use apenas com canais autorizados
- Respeite direitos autorais
- Teste antes de usar em produção
- Sistema fornecido "como está"

## Contribuições

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

O sistema de pre-commit garantirá que seu código atende aos padrões de qualidade.
