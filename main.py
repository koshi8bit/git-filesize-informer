import os
import sys
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

SIZE_LIMIT = 50 * 1024 * 1024


def load_gitignore_patterns(folder_path, base_path):
    gitignore_path = os.path.join(folder_path, ".gitignore")
    patterns = []

    if not os.path.isfile(gitignore_path):
        return patterns

    # относительный путь папки с gitignore
    rel_dir = os.path.relpath(folder_path, base_path)
    if rel_dir == ".":
        rel_dir = ""

    try:
        with open(gitignore_path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # если путь НЕ абсолютный (не начинается с /)
                if not line.startswith("/"):
                    if rel_dir:
                        line = f"{rel_dir}/{line}"
                else:
                    # убираем / → это путь от корня
                    line = line[1:]

                patterns.append(line)

    except Exception as e:
        print(f"Ошибка при чтении {gitignore_path}: {e}")

    return patterns


def find_large_files(folder_path):
    all_patterns = []

    for root, dirs, files in os.walk(folder_path):
        # добавляем паттерны текущей папки
        new_patterns = load_gitignore_patterns(root, folder_path)
        all_patterns.extend(new_patterns)

        spec = PathSpec.from_lines(GitWildMatchPattern, all_patterns)

        # 🔥 ВАЖНО: фильтруем директории (ускорение + как в git)
        dirs[:] = [
            d for d in dirs
            if not spec.match_file(
                os.path.relpath(os.path.join(root, d), folder_path).replace(os.sep, "/") + "/"
            )
        ]

        for file in files:
            file_path = os.path.join(root, file)

            try:
                size = os.path.getsize(file_path)

                if size > SIZE_LIMIT:
                    rel_path = os.path.relpath(file_path, folder_path)
                    rel_path = rel_path.replace(os.sep, "/")

                    if not spec.match_file(rel_path):
                        print(f"{size / (1024 * 1024):10.2f} MB — {file_path}")

            except Exception as e:
                print(f"Ошибка при обработке {file_path}: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python script.py <путь_к_папке>")
    else:
        folder = sys.argv[1]

        if os.path.isdir(folder):
            find_large_files(folder)
        else:
            print("Указанный путь не является папкой")