# Trabalho Prático Final — Versão Completa

Projeto Python para procurar caminhos entre cidades portuguesas com:
- Custo Uniforme
- Profundidade Limitada
- Procura Sôfrega
- A*
- OCR de matrícula para autenticação
- descrições de 3 atrações por cidade via LLM local (Ollama) com fallback local
- interface CLI e interface gráfica Streamlit
- histórico em JSON/CSV
- relatório automático em PDF
- testes automáticos

## Instalação

```bash
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\activate
pip install -r requirements.txt
```
Instalar Tesseract

Tentar instalar em:
- C:\Program Files\Tesseract-OCR\tesseract.exe
ou
- C:\Program Files (x86)\Tesseract-OCR\tesseract.exe

https://github.com/UB-Mannheim/tesseract/wiki

## Execução CLI

```bash
python app.py --plate AA-11-BB --origin Aveiro --goal Faro --algorithm all
python app.py --plate-image examples/plate_AA-11-BB.png --origin Aveiro --goal Faro --algorithm astar
python app.py --plate AA-11-BB --origin Braga --goal Faro --algorithm dls --depth-limit 10
python app.py --plate AA-11-BB --origin Aveiro --goal Faro --algorithm astar --generate-report
```

## Interface gráfica

```bash
streamlit run streamlit_app.py
```

## LLM local
Instalar o llama: https://ollama.com/library/llama3.1:8b

```bash
ollama pull llama3.1:8b
```
```bash
ollama run llama3.1:8b
```

O projeto tenta usar o Ollama em `http://localhost:11434`. Se não estiver disponível, usa descrições locais de fallback.

## OCR

O projeto tenta usar, por ordem:
1. easyocr
2. pytesseract
3. fallback por normalização e nome do ficheiro

## Histórico

As execuções ficam em:
- `history/search_history.json`
- `history/search_history.csv`

## Testes

```bash
pytest -q
```

## Nota

A heurística oficial do enunciado é apenas para `Faro`. Para outros destinos, o sistema usa heurística `0`.
