import re
import sys
import yaml


class ConfigLanguageError(Exception):
    """Ошибка синтаксиса или семантики в учебном конфигурационном языке."""
    pass


class Translator:
    def __init__(self):
        self.constants = {}  # Для хранения объявленных констант

    def parse(self, input_text):
        """Парсинг входного текста."""
        input_text = self.remove_comments(input_text)
        lines = input_text.splitlines()
        result = {}
        buffer = []  # Буфер для многострочного выражения
        in_multiline = False  # Флаг, обозначающий состояние многострочного выражения

        for line in lines:
            line = line.strip()
            if not line:
                continue  # Пропустить пустые строки

            if in_multiline:
                # Продолжение многострочного выражения
                buffer.append(line)
                if line.endswith('}') or line.endswith(']'):
                    in_multiline = False
                    combined = " ".join(buffer)
                    parsed = self.parse_expression(combined)
                    buffer = []  # Очистить буфер
                    if isinstance(parsed, dict):
                        result.update(parsed)
                    elif isinstance(parsed, list):
                        # Если это массив, выдаём ошибку, так как массив на верхнем уровне недопустим
                        raise ConfigLanguageError(f"Некорректное выражение: {combined}")
                continue

            if line.startswith("{") or line.startswith("["):
                # Начало многострочного выражения
                buffer.append(line)
                in_multiline = True
                continue

            if line.startswith("def"):
                self.parse_constant(line)
            elif line.startswith("^"):
                result.update(self.evaluate_constant(line))
            else:
                parsed = self.parse_expression(line)
                if isinstance(parsed, dict):
                    result.update(parsed)
                else:
                    raise ConfigLanguageError(f"Некорректная строка: {line}")
        return result

    def remove_comments(self, text):
        """Удаление однострочных и многострочных комментариев."""
        text = re.sub(r'%.*', '', text)  # Удаление однострочных комментариев
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)  # Удаление многострочных комментариев
        return text

    def parse_constant(self, line):
        """Парсинг объявления констант."""
        match = re.match(r'def\s+([_A-Za-z][_a-zA-Z0-9]*)\s*=\s*(.+);', line)
        if not match:
            raise ConfigLanguageError(f"Ошибка в объявлении константы: {line}")
        name, value = match.groups()
        value = self.parse_expression(value)
        self.constants[name] = value

    def evaluate_constant(self, line):
        """Вычисление значения константы."""
        match = re.match(r'\^([_A-Za-z][_a-zA-Z0-9]*)', line)
        if not match:
            raise ConfigLanguageError(f"Ошибка в вычислении константы: {line}")
        name = match.group(1)
        if name not in self.constants:
            raise ConfigLanguageError(f"Константа {name} не определена")
        return {name: self.constants[name]}

    def parse_expression(self, text):
        """Парсинг значений, массивов и словарей."""
        text = text.strip()
        if re.match(r'^\d+$', text):  # Число
            return int(text)
        elif text.startswith('"') and text.endswith('"'):  # Строка
            return text[1:-1]
        elif text.startswith('[') and text.endswith(']'):  # Массив
            return self.parse_array(text)
        elif text.startswith('{') and text.endswith('}'):  # Словарь
            return self.parse_dict(text)
        else:
            raise ConfigLanguageError(f"Некорректное выражение: {text}")

    def parse_array(self, text):
        """Парсинг массивов."""
        text = text[1:-1].strip()  # Убираем квадратные скобки
        if not text:  # Если массив пустой
            return []
        # Используем регэксп для корректного разбиения, учитывая вложенные структуры
        elements = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', text)
        return [self.parse_expression(el.strip()) for el in elements]

    def parse_dict(self, text):
        """Парсинг словарей."""
        text = text[1:-1].strip()  # Убираем фигурные скобки
        if not text:  # Если словарь пустой
            return {}
        # Разбиваем строки с учётом возможных вложенных конструкций
        items = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', text)
        result = {}
        for item in items:
            key_value = item.split('=', 1)
            if len(key_value) != 2:
                raise ConfigLanguageError(f"Некорректный элемент словаря: {item.strip()}")
            key = key_value[0].strip()
            value = self.parse_expression(key_value[1].strip())
            result[key] = value
        return result


def main():
    """Точка входа в программу."""
    translator = Translator()
    input_text = sys.stdin.read()  # Чтение из стандартного ввода
    try:
        parsed_result = translator.parse(input_text)
        yaml_output = yaml.dump(parsed_result, default_flow_style=False, allow_unicode=True)
        print(yaml_output)
    except ConfigLanguageError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
