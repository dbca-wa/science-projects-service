import os
import re

class FileCleaner:
    def __init__(self):
        pass

    def extract_base_name_and_index(self, file_name):
        # Use regular expression to extract base name and index from the file name
        match = re.match(r'^(.+?)(?:_(\d+))?(\.pdf)?$', file_name)
        if match:
            base_name, index, extension = match.groups()
            # If the index is None, set it to 0
            index = int(index) if index else 0
            return f"{base_name}{extension}", index
        else:
            # If no match, return the file name as base name and index 0
            return file_name, 0

    def clean_files(self, directory):
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist.")
            return

        # Check if the directory is empty
        if not os.listdir(directory):
            print(f"Directory {directory} is empty.")
            return

        subfolders = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
        print(subfolders)
        for subfolder in subfolders:
            subfolder_path = os.path.join(directory, subfolder)
            pdf_files_in_subfolder = [f for f in os.listdir(subfolder_path) if f.endswith(".pdf")]
            print(f'Subfolder Path: {subfolder_path}')
            print(f'Subfolder PDFS: {pdf_files_in_subfolder}')

            pdf_base_names = {}

            for pdf in pdf_files_in_subfolder:
                # Extract the base name and index from the file name
                base_name, index = self.extract_base_name_and_index(pdf)

                if base_name in pdf_base_names:
                    # If the current file has a higher index, update the entry
                    if index > pdf_base_names[base_name][1]:
                        pdf_base_names[base_name] = (pdf, index)
                else:
                    pdf_base_names[base_name] = (pdf, index)

            # Remove files that are not the one with the highest index
            print("Checking pdfs against pdf_base_names")
            print(pdf_base_names)

            pdf_files_copy = pdf_files_in_subfolder.copy()

            for pdf in pdf_files_copy:
                base_name, index = self.extract_base_name_and_index(pdf)
                if pdf != pdf_base_names[base_name][0]:
                    print(f'{pdf} is not {pdf_base_names[base_name][0]}')
                    print('removing pdf')
                    file_to_remove = os.path.join(subfolder_path, pdf)
                    try:
                        print(f"Before removing file: {file_to_remove}")
                        os.remove(file_to_remove)
                        print(f"After removing file: {file_to_remove}")

                    except Exception as e:
                        print(f"Error removing file {file_to_remove}: {e}")

if __name__ == "__main__":
    print("Initialising file cleaner")
    # Get the directory where the script is located
    script_directory = os.path.dirname(os.path.realpath(__file__))
    arar_path = os.path.join(script_directory, 'ararreports')
    doc_path = os.path.join(script_directory, 'documents')
    print(script_directory)
    print(arar_path)
    print(doc_path)
    
    cleaner = FileCleaner()
    print('cleaner start')
    cleaner.clean_files(arar_path)
    cleaner.clean_files(doc_path)
