import os
import sys

# Порог в байтах (50 МБ)
SIZE_LIMIT = 50 * 1024 * 1024


def find_large_files(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                size = os.path.getsize(file_path)
                if size > SIZE_LIMIT:
                    print(f"{file_path} — {size / (1024 * 1024):.2f} MB")
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