# 🎬 Fast Cut - Sistema de Geração Automática de Cortes

Sistema inteligente que baixa vídeos de canais autorizados do YouTube e gera automaticamente cortes otimizados para **YouTube Shorts**, **TikTok** e **Instagram Reels**.

## 📋 Características

- ✅ **100% Gratuito** - Não usa APIs pagas
- 🤖 **Totalmente Automático** - Identifica os melhores momentos para corte
- 📱 **Multi-plataforma** - Otimiza para YouTube Shorts, TikTok e Instagram
- 🎯 **Inteligente** - Analisa áudio, vídeo e detecta momentos de alta energia
- 🔒 **Seguro** - Apenas canais autorizados via variáveis de ambiente
- ⚡ **Rápido** - Usa FFmpeg para processamento eficiente
- 🧪 **Qualidade** - Sistema de linting e validação automática

## 🚀 Instalação Rápida

```bash
# Clone o projeto
git clone <seu-repositorio>
cd fast-cut

# Configuração automática
python scripts/setup.py

# Configure os canais no .env
cp env_example.txt .env
# Edite o .env com seus canais autorizados

# Execute um teste
make run-test
```

## 🛠️ Comandos de Desenvolvimento

```bash
# Configuração inicial
make install-dev        # Instala dependências de desenvolvimento
make setup-hooks        # Configura pre-commit hooks

# Qualidade de código
make format             # Formata código (black + isort)
make lint               # Executa linting (flake8)
make type-check         # Verifica tipos (mypy)
make check              # Executa todas as verificações

# Execução
make run                # Executa o sistema
make run-test           # Testa o sistema
make run-channels       # Lista canais configurados

# Limpeza
make clean              # Remove arquivos temporários
```

## ⚙️ Configuração

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
```

## 📁 Nova Estrutura do Projeto

```
fast-cut/
├── src/fast_cut/           # Código fonte principal
│   ├── core/              # Módulos principais
│   │   ├── config.py      # Configurações
│   │   ├── types.py       # Tipos e estruturas
│   │   └── system.py      # Sistema principal
│   ├── services/          # Serviços especializados
│   │   ├── downloader.py  # Download de vídeos
│   │   ├── analyzer.py    # Análise de vídeos
│   │   └── cutter.py      # Corte e otimização
│   └── utils/             # Utilitários
│       └── ffmpeg.py      # Utilitários FFmpeg
├── scripts/               # Scripts de automação
│   ├── setup.py          # Configuração inicial
│   └── validate.py       # Validação de código
├── pyproject.toml         # Configuração do projeto
├── .pre-commit-config.yaml # Hooks de pre-commit
└── Makefile              # Comandos de desenvolvimento
```

## 🧠 Princípios de Código Limpo Aplicados

### ✅ DRY (Don't Repeat Yourself)
- Configurações centralizadas em `Config`
- Utilitários reutilizáveis em `utils/`
- Tipos compartilhados em `types.py`

### ✅ KISS (Keep It Simple, Stupid)
- Funções com responsabilidade única
- Interfaces claras e simples
- Código autoexplicativo

### ✅ Lei de Curly
- Cada classe tem uma responsabilidade específica
- Separação clara entre serviços, configuração e tipos

### ✅ YAGNI (You Aren't Gonna Need It)
- Removidos recursos não utilizados
- Foco apenas no essencial

### ✅ Regra do Escoteiro
- Código mais limpo e organizado
- Estrutura melhorada
- Documentação clara

## 🔒 Travas de Qualidade

### Pre-commit Hooks
- **Black**: Formatação automática
- **isort**: Organização de imports
- **Flake8**: Linting
- **MyPy**: Verificação de tipos

### Validação Contínua
```bash
# Executa todas as validações
python scripts/validate.py

# Ou usando make
make check
```

### Tipagem Forte
- Todas as funções tipadas
- Uso de dataclasses para estruturas
- Validação com MyPy

## 📖 Como Usar

### Execução Básica
```bash
# Sistema completo
python main.py

# Máximo 3 vídeos por canal
python main.py --max-videos 3

# Usar vídeos existentes
python main.py --skip-download

# Listar canais
python main.py --list-channels

# Teste do sistema
python main.py --test
```

### Com Make
```bash
make run                # Execução normal
make run-test           # Teste
make run-channels       # Lista canais
```

## 🎯 Limites de Duração

- **YouTube Shorts**: Máximo 60 segundos (9:16)
- **TikTok**: 15-60 segundos (9:16)
- **Instagram Reels**: 15-60 segundos (9:16)

## 📊 Exemplo de Saída

```
🎬 SISTEMA FAST CUT - GERADOR AUTOMÁTICO DE CORTES
============================================================
✅ Configuração validada:
   Canais: 2
   Duração dos clipes: 15s-60s
   Clipes por vídeo: 3

🔽 ETAPA 1: DOWNLOAD DE VÍDEOS
----------------------------------------
📺 Processando canal: UC_x5XG1OV2P6uZZ5FSM9Ttw
🔍 Buscando vídeos do canal: UC_x5XG1OV2P6uZZ5FSM9Ttw
⬇️  Baixando: Como fazer vídeos virais
✅ Vídeo baixado: Como_fazer_videos_virais.mp4
✅ Download concluído: 3 vídeos

🔍 ETAPA 2: ANÁLISE E GERAÇÃO DE CORTES
----------------------------------------
📹 Processando 1/3: Como_fazer_videos_virais.mp4
🔍 Analisando: Como_fazer_videos_virais.mp4
✂️  3 clipes encontrados
✂️  Processando clipe 1/3
✅ Otimizado para youtube_shorts: Como_fazer_videos_virais_clip_1_youtube_shorts.mp4
✅ 9 clipes gerados

📊 RELATÓRIO FINAL
============================================================
⏱️  Tempo de execução: 0:03:45
📥 Vídeos baixados: 3
🔍 Vídeos analisados: 3
✂️  Total de clipes: 27

📱 CLIPES POR PLATAFORMA:
  Youtube Shorts: 9 clipes
  Tiktok: 9 clipes
  Instagram Reels: 9 clipes

📈 Taxa de sucesso: 100.0%
🎯 Clipes salvos em: output
============================================================
```

## 🔧 Desenvolvimento

### Configuração do Ambiente
```bash
# Instalar em modo desenvolvimento
pip install -e ".[dev]"

# Configurar hooks
pre-commit install

# Executar validações
make check
```

### Estrutura de Commits
O projeto usa pre-commit hooks que garantem:
- Código formatado (Black)
- Imports organizados (isort)
- Linting aprovado (Flake8)
- Tipos verificados (MyPy)

## ⚠️ Aviso Legal

- Use apenas com canais autorizados
- Respeite direitos autorais
- Teste antes de usar em produção
- Sistema fornecido "como está"

## 🤝 Contribuições

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

O sistema de pre-commit garantirá que seu código atende aos padrões de qualidade.