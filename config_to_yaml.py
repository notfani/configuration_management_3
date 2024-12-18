import re
import yaml
import sys


class ConfigParser:
    def __init__(self):
        self.constants = {}

    def parse(self, text):
        # Удаляем комментарии
        text = self.remove_comments(text)
        print("После удаления комментариев:", text)  # Debug

        lines = text.splitlines()  # Разделяем текст на строки

        # Разбираем константы
        main_structure_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith("def"):  # Константа
                self.handle_constant_definition(line)
            elif line:  # Полезная строка
                main_structure_lines.append(line)

        # Если тело с данными осталось пустым, но есть константы, это разрешено
        main_structure = " ".join(main_structure_lines).strip()
        if not main_structure:  # Проверяем, пустое ли тело после обработки
            print("Нет структуры для парсинга, только константы определены.")  # Debug
            return None

        print("Структура для парсинга:", main_structure)  # Debug

        if main_structure.startswith("{") and main_structure.endswith("}"):
            return self.parse_dict(main_structure)
        else:
            raise SyntaxError(f"Invalid structure: {main_structure}")

    def remove_comments(self, text):
        # Удаляем однострочные комментарии (%)
        text = re.sub(r'%.*', '', text)
        # Удаляем многострочные комментарии (/* */)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        # Удаляем пустые строки
        text = "\n".join(line for line in text.splitlines() if line.strip())  # Убираем пустые строки
        return text.strip()

    def handle_constant_definition(self, line):
        # Разбираем определение константы
        match = re.match(r'def\s+([_A-Z][_a-zA-Z0-9]*)\s*=\s*(.+);', line)
        if match:
            name, value = match.groups()
            try:
                value = eval(value, {}, self.constants)  # Интерпретируем значение с учётом текущих констант
                self.constants[name] = value
                print(f"Определена константа: {name} = {value}")  # Debug
            except Exception as e:
                raise ValueError(f"Ошибка при обработке константы {name}: {e}")
        else:
            raise SyntaxError(f"Неверное определение константы: {line}")

    def resolve_constant(self, value):
        if value.startswith("^"):  # Если это ссылка на константу
            name = value[1:]
            if name in self.constants:
                resolved_value = self.constants[name]
                print(f"Константа {name} разрешена в значение {resolved_value}")  # Debug
                return resolved_value
            else:
                raise NameError(f"Константа {name} не определена")
        return eval(value, {}, self.constants)  # Если не константа, то интерпретируем как обычное значение

    def parse_dict(self, text):
        # Удаляем внешние фигурные скобки
        text = text[1:-1].strip()
        print("Разбираем словарь из текста:", text)  # Debug

        result = {}
        buffer = ""
        key = None
        depth = 0

        for char in text:
            if char == "," and depth == 0:  # Завершение пары ключ=значение
                key, value = self.process_pair(buffer)
                result[key] = value
                buffer = ""
            else:
                if char in "{[":  # Увеличиваем глубину для вложенных структур
                    depth += 1
                elif char in "}]":  # Уменьшаем глубину
                    depth -= 1
                buffer += char

        # Обрабатываем последнюю пару в строке
        if buffer.strip():
            key, value = self.process_pair(buffer)
            result[key] = value

        print("Разобранный словарь:", result)  # Debug
        return result

    def process_pair(self, pair_text):
        """Обрабатывает пару key = value."""
        key, value = pair_text.split("=", 1)  # Разделяем по первому знаку "="
        key = key.strip()
        value = value.strip()

        # Определяем тип значения и обрабатываем
        if value.startswith("{"):
            return key, self.parse_dict(value)  # Рекурсивный вызов парсера словаря
        elif value.startswith("["):
            return key, self.parse_list(value)  # Рекурсивный вызов парсера списка
        elif value.startswith("^"):
            return key, self.resolve_constant(value)  # Разрешение константы
        else:
            return key, eval(value, {}, self.constants)  # Простые значения или выражения

    def parse_list(self, text):
        # Удаляем внешние квадратные скобки
        text = text[1:-1].strip()
        print("Разбираем список из текста:", text)  # Debug

        items = [
            self.resolve_constant(item.strip()) if item.strip().startswith("^")
            else eval(item.strip(), {}, self.constants)
            for item in text.split(",") if item.strip()
        ]

        print("Разобранный список:", items)  # Debug
        return items


def main():
    if len(sys.argv) != 3:
        print("Usage: python config_to_yaml.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        with open(input_file, 'r') as infile:
            config_text = infile.read()

        parser = ConfigParser()
        parsed_data = parser.parse(config_text)
        print("Итоговый результат парсинга:", parsed_data)  # Debug

        with open(output_file, 'w') as outfile:
            yaml.dump(parsed_data, outfile)

        print(f"Конвертация в YAML успешно завершена. Файл сохранён: {output_file}")
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
