# Aplicação OCR

Uma aplicação de Reconhecimento Óptico de Caracteres (OCR) construída com Streamlit que pode extrair texto, tabelas e imagens de arquivos PDF e imagem.

## Funcionalidades

- **Suporte Multi-formato**: Processa arquivos PDF, PNG, JPG e JPEG
- **Múltiplos Tipos de Extração**:
  - Extração de texto
  - Extração de tabelas (com saída HTML)
  - Extração de imagens de documentos
  - Classificação inteligente de conteúdo
- **Processamento Página por Página**: Manipula PDFs com múltiplas páginas (até 10 páginas)
- **Download de Resultados**: Exporte conteúdo extraído em vários formatos
- **Interface Moderna**: Interface limpa em Streamlit com capacidade de visualização

## Pré-requisitos

### Dependências do Sistema

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Windows:**
Baixe e instale o poppler de: https://github.com/oschwartz10612/poppler-windows/releases/
Adicione o diretório `bin` ao PATH do seu sistema.

### Versão do Python
- Python 3.12 ou superior

## Instalação

1. **Clone o repositório:**
```bash
git clone https://github.com/SamuelBaptista/videos.git
cd codigos/ocr
```

2. **Crie um ambiente virtual:**
```bash
python -m venv venv

# No Linux/macOS:
source venv/bin/activate

# No Windows:
venv\Scripts\activate
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

## Variáveis de Ambiente

Crie um arquivo `.env` no diretório do projeto com as seguintes variáveis:

```env
# Mistral API Key
MISTRAL_API_KEY=sua_chave_api_mistral_aqui

# Anthropic API Key
ANTHROPIC_API_KEY=sua_chave_api_anthropic_aqui

# OpenAI API Key
OPENAI_API_KEY=sua_chave_api_openai_aqui

# Credenciais AWS (para Textract)
AWS_ACCESS_KEY_ID=sua_chave_acesso_aws
AWS_SECRET_ACCESS_KEY=sua_chave_secreta_aws
AWS_DEFAULT_REGION=us-east-2
```

### Obtendo as Chaves de API:

1. **Chave API Mistral AI**: Cadastre-se em https://mistral.ai/ e obtenha sua chave da API
2. **Chave API Anthropic**: Cadastre-se em https://www.anthropic.com/ e obtenha sua chave da API
3. **Chave API OpenAI**: Cadastre-se em https://platform.openai.com/ e obtenha sua chave da API
4. **Credenciais AWS**: Crie uma conta AWS e obtenha credenciais com permissões para Textract

## Estrutura do Projeto

```
codigos/ocr/
├── app.py              # Aplicação principal Streamlit
├── functions.py        # Funções de processamento OCR
├── prompts.py         # Prompts OCR
├── requirements.txt   # Dependências Python
├── .env              # Variáveis de ambiente (criar este arquivo)
└── README.md         # Este arquivo
```

## Atualizando o Arquivo de Prompts

Atualize o arquivo `prompts.py` com seus prompts OCR:

```python
OCR_CLASSIFICATION = """
Seu prompt de classificação aqui...
"""

OCR_PROMPT = """
Seu prompt de extração de texto aqui...
"""

OCR_TABLES = """
Seu prompt de extração de tabelas aqui...
"""
```

## Executando a Aplicação

1. **Certifique-se de que todas as dependências estão instaladas e as variáveis de ambiente configuradas**

2. **Execute a aplicação Streamlit:**
```bash
streamlit run app.py
```

3. **Acesse a aplicação:**
   - A aplicação abrirá automaticamente no seu navegador padrão
   - Se não abrir, navegue para: http://localhost:8501

## Como Usar

1. **Faça Upload de um Documento**: Clique no carregador de arquivos e selecione um arquivo PDF ou imagem
2. **Processar**: Clique no botão "Processar Documento"
3. **Ver Resultados**: 
   - Para documentos com múltiplas páginas, selecione a página que deseja visualizar
   - O conteúdo extraído será exibido com opções de download
4. **Download**: Use os botões de download para salvar texto, tabelas ou imagens extraídas

## Funcionalidades em Detalhes

### Classificação de Conteúdo
A aplicação classifica automaticamente cada página para determinar que tipo de conteúdo extrair:
- Conteúdo de texto
- Instruções
- Tabelas
- Imagens

### Métodos de Extração
- **Texto/Instruções**: Usa o Claude da Anthropic para extração precisa de texto
- **Tabelas**: Extrai e formata tabelas como HTML
- **Imagens**: Usa OCR da Mistral para extração de imagens

### Limitações
- Máximo de 10 páginas por documento PDF
- Logotipos e assinaturas não são considerados como imagens extraíveis
- O tempo de processamento depende da complexidade do documento e do tempo de resposta da API

## Solução de Problemas

### Problemas Comuns:

1. **Erro "poppler não encontrado"**:
   - Certifique-se de que poppler-utils está instalado no seu sistema
   - Reinicie seu terminal após a instalação

2. **Erros de Chave API**:
   - Verifique se suas chaves API estão corretamente configuradas no arquivo .env
   - Verifique se suas chaves API têm as permissões necessárias

3. **Erros do AWS Textract**:
   - Verifique se as credenciais AWS estão corretas
   - Certifique-se de que sua conta AWS tem permissões para Textract
   - Verifique a região AWS
