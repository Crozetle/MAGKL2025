import os
import re
import base64
import requests
import markdown2

VAULT_PATH = "./Anki"  # путь к Obsidian Vault
ANKI_CONNECT_URL = "http://127.0.0.1:8765"

def markdown_to_html(text: str) -> str:
    html = markdown2.markdown(text, extras=[
        "tables",
        "break-on-newline",
        "fenced-code-blocks",
        "strike"
    ])
    return html

def convert_tables_to_html(text):
    lines = text.split('\n')
    output = []
    table_block = []
    inside_table = False

    def is_table_line(line):
        return re.match(r'^\s*\|.*\|\s*$', line)

    for line in lines + ['']:
        if is_table_line(line):
            table_block.append(line)
            inside_table = True
        else:
            if inside_table:
                html = parse_markdown_table(table_block)
                output.append(html)
                table_block = []
                inside_table = False
            output.append(line)

    return '\n'.join(output)

def parse_markdown_table(lines):
    def split_row(row):
        return [cell.strip() for cell in row.strip('|').split('|')]

    if len(lines) < 2:
        return '\n'.join(lines)

    header = split_row(lines[0])
    rows = [split_row(row) for row in lines[2:]]

    html = ['<table border="1">']
    html.append('<thead><tr>' + ''.join(f'<th>{cell}</th>' for cell in header) + '</tr></thead>')
    html.append('<tbody>')
    for row in rows:
        html.append('<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>')
    html.append('</tbody></table>')

    return '\n'.join(html)

def invoke(action, params):
    response = requests.post(ANKI_CONNECT_URL, json={
        "action": action,
        "version": 6,
        "params": params
    })
    return response.json()

def create_deck(deck_name):
    res = invoke("createDeck", {"deck": deck_name})
    if res.get("error") is None:
        print(f"Колода создана: {deck_name}")
    elif "exists" not in res["error"]:
        print(f"Ошибка создания колоды: {res['error']}")

def extract_and_upload_images(text, note_dir):
    img_pattern_obsidian = re.compile(r"!\[\[(.+?)\]\]")
    img_pattern_md = re.compile(r"!\[.*?\]\((.+?)\)")

    images = set(img_pattern_obsidian.findall(text)) | set(img_pattern_md.findall(text))

    for img_name in images:
        img_path = os.path.join("./БД", img_name)  # путь к изображениям
        if not os.path.isfile(img_path):
            print(f"Картинка не найдена: {img_path}")
            continue

        with open(img_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')

        filename = os.path.basename(img_name)
        res = invoke("storeMediaFile", {
            "filename": filename,
            "data": img_data
        })
        if res.get("error"):
            print(f"Ошибка загрузки картинки {filename}: {res['error']}")
        else:
            print(f"Картинка загружена: {filename}")

        text = re.sub(r"!\[\[" + re.escape(img_name) + r"\]\]", f'<img src="{filename}">', text)
        text = re.sub(r'!\[.*?\]\(' + re.escape(img_name) + r'\)', f'<img src="{filename}">', text)

    return text

def convert_latex_to_mathjax(text):
    # $$ формулы → \[...\]
    text = re.sub(r"\$\$(.*?)\$\$", r"\\[\1\\]", text, flags=re.DOTALL)
    # $ формулы → \(...\)
    text = re.sub(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", r"\\(\1\\)", text)
    return text

def convert_markdown_to_html(text):
    text = convert_tables_to_html(text)
    # Блоки кода ```...``` → <pre><code>
    text = re.sub(r"```(.*?)```", r"<pre><code>\1</code></pre>", text, flags=re.DOTALL)

    # Жирный текст **text** и __text__
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.*?)__", r"<strong>\1</strong>", text)

    # Курсив *text* и _text_
    text = re.sub(r"(?<!\*)\*(?!\*)(.*?)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"(?<!_)_(?!_)(.*?)_(?!_)", r"<em>\1</em>", text)

    # Списки - item / * item / + item
    lines = text.split("\n")
    in_list = False
    html_lines = []

    for line in lines:
        if re.match(r"^\s*[-*+]\s+", line):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            item = re.sub(r"^\s*[-*+]\s+", "", line)
            html_lines.append(f"<li>{item}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(line)

    if in_list:
        html_lines.append("</ul>")

    text = "\n".join(html_lines)

    # Переводы строк → <br>
    text = text.replace("\n", "<br>")



    return text

def parse_notes(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    yaml_match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL | re.MULTILINE)
    deck = "Default"
    tags = []
    if yaml_match:
        yaml_text = yaml_match.group(1)
        deck_match = re.search(r"anki-deck:\s*(\S+)", yaml_text)
        tags_match = re.search(r"anki-tags:\s*\[(.*?)\]", yaml_text)
        if deck_match:
            deck = deck_match.group(1)
        if tags_match:
            tags = [tag.strip() for tag in tags_match.group(1).split(",")]

    pattern = re.compile(r"## Вопрос\s*(.*?)\s*## Ответ\s*(.*?)(?=---|$)", re.DOTALL)
    cards = []
    note_dir = os.path.dirname(filepath)
    for match in pattern.finditer(text):
        question = match.group(1).strip()
        answer = match.group(2).strip()

        question = markdown_to_html(question)
        answer = markdown_to_html(answer)
        
        question = extract_and_upload_images(question, note_dir)
        answer = extract_and_upload_images(answer, note_dir)

        question = convert_latex_to_mathjax(question)
        answer = convert_latex_to_mathjax(answer)

        cards.append({
            "deckName": deck,
            "modelName": "Простая",  # Убедись, что такая модель существует
            "fields": {
                "Front": question,
                "Back": answer
            },
            "tags": tags
        })

    return cards

def add_note(note):
    result = invoke("addNote", {"note": note})
    if result.get("error") is None:
        print(f"✅ Добавлена карточка: {note['fields']['Front'][:30]}...")
    else:
        print(f"❌ Ошибка при добавлении: {result['error']}")

def main():
    for root, dirs, files in os.walk(VAULT_PATH):
        for file in files:
            if file.endswith(".md"):
                path = os.path.join(root, file)
                notes = parse_notes(path)
                for note in notes:
                    create_deck(note["deckName"])
                    add_note(note)

if __name__ == "__main__":
    main()
