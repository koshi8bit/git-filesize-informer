import os
import sys

# Порог в байтах (50 МБ)
SIZE_LIMIT = 50 * 1024 * 1024


def load_gitignore(folder_path):
    gitignore_path = os.path.join(folder_path, ".gitignore")
    ignored = set()

    if os.path.isfile(gitignore_path):
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        ignored.add(line)
        except Exception as e:
            print(f"Ошибка при чтении {gitignore_path}: {e}")

    return ignored


def is_ignored(file_name, rel_path, ignored_set):
    return file_name in ignored_set or rel_path in ignored_set


def find_large_files(folder_path):
    for root, dirs, files in os.walk(folder_path):
        ignored_set = load_gitignore(root)

        for file in files:
            file_path = os.path.join(root, file)

            try:
                size = os.path.getsize(file_path)

                if size > SIZE_LIMIT:
                    rel_path = os.path.relpath(file_path, root)

                    if not is_ignored(file, rel_path, ignored_set):
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