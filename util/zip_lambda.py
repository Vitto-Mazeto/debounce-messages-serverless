import os
import zipfile

# Caminho do diretório atual (onde os .py estão soltos)
root_dir = os.getcwd()

# Percorre cada arquivo no diretório raiz
for file_name in os.listdir(root_dir):
    file_path = os.path.join(root_dir, file_name)

    # Verifica se é um arquivo .py
    if os.path.isfile(file_path) and file_name.endswith(".py"):
        # Nome do zip será o nome do arquivo .py (sem extensão)
        zip_filename = os.path.join(root_dir, f"{os.path.splitext(file_name)[0]}.zip")

        # Cria o arquivo zip e adiciona o arquivo renomeado como lambda_function.py
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(file_path, "lambda_function.py")

        print(f"{zip_filename} criado com sucesso!")

print("Processo finalizado!")
