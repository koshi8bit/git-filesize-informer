import os
import fnmatch
from pathlib import Path


def parse_gitignore(gitignore_path):
    """
    Парсит файл .gitignore и возвращает список паттернов для исключения
    """
    patterns = []
    if not os.path.exists(gitignore_path):
        return patterns

    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Пропускаем пустые строки и комментарии
                if not line or line.startswith('#'):
                    continue
                patterns.append(line)
    except (OSError, PermissionError):
        pass

    return patterns


def is_ignored(file_path, gitignore_patterns_dict, root_path):
    """
    Проверяет, должен ли файл быть проигнорирован по правилам .gitignore
    gitignore_patterns_dict: словарь, где ключ - путь к папке с .gitignore,
                             значение - список паттернов
    """
    if not gitignore_patterns_dict:
        return False

    # Получаем абсолютный путь к файлу
    abs_file_path = os.path.abspath(file_path)
    file_dir = os.path.dirname(abs_file_path)

    # Проверяем все .gitignore файлы, которые находятся в родительских директориях
    for gitignore_dir, patterns in sorted(gitignore_patterns_dict.items(),
                                          key=lambda x: len(x[0]), reverse=True):
        # Проверяем, находится ли файл в директории с .gitignore или в её поддиректориях
        if abs_file_path.startswith(gitignore_dir + os.sep) or abs_file_path == gitignore_dir:
            # Получаем относительный путь от папки с .gitignore
            rel_path = os.path.relpath(abs_file_path, gitignore_dir)
            rel_path = rel_path.replace('\\', '/')  # для Windows

            for pattern in patterns:
                # Пропускаем пустые паттерны
                if not pattern:
                    continue

                # Паттерны с / применяются от корня папки с .gitignore
                if pattern.startswith('/'):
                    # Убираем начальный слэш и проверяем
                    clean_pattern = pattern[1:]
                    if fnmatch.fnmatch(rel_path, clean_pattern):
                        return True
                # Паттерны без / применяются в любом месте
                else:
                    # Проверяем, не является ли паттерн директорией (заканчивается на /)
                    if pattern.endswith('/'):
                        # Это директория - проверяем, находится ли файл в этой директории
                        dir_pattern = pattern.rstrip('/')
                        if rel_path.startswith(dir_pattern + '/') or rel_path == dir_pattern:
                            return True
                    else:
                        # Проверяем относительный путь целиком
                        if fnmatch.fnmatch(rel_path, pattern):
                            return True
                        # Проверяем только имя файла
                        if fnmatch.fnmatch(os.path.basename(file_path), pattern):
                            return True
                        # Проверяем части пути
                        path_parts = rel_path.split('/')
                        for i in range(len(path_parts)):
                            if fnmatch.fnmatch('/'.join(path_parts[i:]), pattern):
                                return True

                        # Проверяем паттерны с ** (любая вложенность)
                        if '**' in pattern:
                            if fnmatch.fnmatch(rel_path, pattern):
                                return True

    return False


def collect_gitignore_patterns(directory):
    """
    Рекурсивно собирает все .gitignore файлы в директории и поддиректориях
    Возвращает словарь: {путь_к_папке_с_gitignore: [список_паттернов]}
    """
    gitignore_patterns = {}
    root_path = os.path.abspath(directory)

    for root, dirs, files in os.walk(root_path):
        # Пропускаем .git директорию
        if '.git' in dirs:
            dirs.remove('.git')

        # Проверяем наличие .gitignore в текущей папке
        gitignore_path = os.path.join(root, '.gitignore')
        patterns = parse_gitignore(gitignore_path)

        if patterns:
            gitignore_patterns[root] = patterns
            print(f"Найден .gitignore в {root} с {len(patterns)} паттернами")

    return gitignore_patterns


def find_large_files(directory, size_limit_mb=50):
    """
    Ищет файлы больше size_limit_mb MB в директории и поддиректориях
    """
    size_limit_bytes = size_limit_mb * 1024 * 1024
    root_path = os.path.abspath(directory)

    print(f"Поиск файлов больше {size_limit_mb} MB в: {root_path}")
    print("=" * 70)

    # Собираем все .gitignore файлы
    print("\nСбор .gitignore файлов...")
    gitignore_patterns = collect_gitignore_patterns(root_path)

    if gitignore_patterns:
        print(f"\nНайдено {len(gitignore_patterns)} .gitignore файлов")
    else:
        print("\n.gitignore файлы не найдены")

    print("\n" + "-" * 70)
    print(f"{'Размер':>12}  {'Файл'}")
    print("-" * 70)

    large_files_count = 0
    ignored_files_count = 0

    # Проходим по всем файлам
    for current_root, dirs, files in os.walk(root_path):
        # Пропускаем .git директорию
        if '.git' in dirs:
            dirs.remove('.git')

        for file in files:
            file_path = os.path.join(current_root, file)

            try:
                # Получаем размер файла
                size = os.path.getsize(file_path)

                # Проверяем размер
                if size > size_limit_bytes:
                    # Проверяем, не игнорируется ли файл
                    if not is_ignored(file_path, gitignore_patterns, root_path):
                        size_mb = size / (1024 * 1024)
                        print(f"{size_mb:10.2f} MB — {file_path}")
                        large_files_count += 1
                    else:
                        ignored_files_count += 1

            except (OSError, PermissionError):
                # Пропускаем файлы, к которым нет доступа
                continue

    print("-" * 70)
    print(f"\nРезультаты:")
    print(f"  Найдено больших файлов (не проигнорированных): {large_files_count}")
    if ignored_files_count > 0:
        print(f"  Проигнорировано (по .gitignore): {ignored_files_count}")


def main():
    """
    Основная функция программы
    """
    import sys

    # Проверяем аргументы командной строки
    if len(sys.argv) != 2:
        print("Использование: python script.py <путь_к_папке>")
        print("Пример: python find_large_files.py /home/user/project")
        sys.exit(1)

    directory = sys.argv[1]

    # Проверяем существование директории
    if not os.path.exists(directory):
        print(f"Ошибка: Директория '{directory}' не существует")
        sys.exit(1)

    if not os.path.isdir(directory):
        print(f"Ошибка: '{directory}' не является директорией")
        sys.exit(1)

    find_large_files(directory)


if __name__ == "__main__":
    main()