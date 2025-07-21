import os

def parse_questions(file_path):
    questions = []
    current_discipline = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("Дисциплина - "):
                current_discipline = line.replace("Дисциплина - ", "")
            elif line[0].isdigit() and '.' in line.split()[0]:
                question_text = line.split('.', 1)[1].strip()
                questions.append({
                    'discipline': current_discipline,
                    'text': question_text
                })
    return questions

def generate_md_files(questions, template_path, output_dir, direction_name):
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    total_questions = len(questions)
    os.makedirs(output_dir, exist_ok=True)

    for idx, q in enumerate(questions):
        prev_idx = (idx - 1) % total_questions
        next_idx = (idx + 1) % total_questions
        
        prev_file = f"{prev_idx + 1:03d}.md"
        next_file = f"{next_idx + 1:03d}.md"
        current_file = f"{idx + 1:03d}.md"
        
        content = template
        content = content.replace("Discipline:", f"Discipline: {q['discipline']}")
        content = content.replace("Direction:", f"Direction:\n  - \"[[{direction_name}]]\"")
        content = content.replace("Название файла предыдущего вопроса", prev_file)
        content = content.replace("Название следующего вопроса", next_file)
        
        question_header = "## Вопрос"
        content = content.replace(
            f"{question_header}\n", 
            f"{question_header}\n\n{q['text']}\n"
        )
        
        with open(os.path.join(output_dir, current_file), 'w', encoding='utf-8') as f:
            f.write(content)

def find_and_process_all_questions(base_dir, template_path):
    for root, dirs, files in os.walk(base_dir):
        if "Список вопросов.txt" in files:
            questions_file = os.path.join(root, "Список вопросов.txt")
            direction_name = os.path.basename(root)
            output_dir = os.path.join(root, "Вопросы")
            
            questions = parse_questions(questions_file)
            generate_md_files(questions, template_path, output_dir, direction_name)
            print(f"[✓] {len(questions)} вопросов обработано для папки: {direction_name}")

if __name__ == "__main__":
    BASE_DIR = "ПШ"  # текущая папка
    TEMPLATE_FILE = "Шаблоны/Шаблон вопроса.md"
    
    find_and_process_all_questions(BASE_DIR, TEMPLATE_FILE)
