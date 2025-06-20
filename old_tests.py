import unittest
# from functions.get_files_info import get_files_info
# from functions.get_file_content import get_file_content
# from functions.write_file import write_file
from functions.run_python_file import run_python_file

class TestGetFilesInfo(unittest.TestCase):
    def setUp(self):
        # self.get_files_info = get_files_info
        # self.get_file_content = get_file_content
        # self.write_file = write_file
        self.run_python_file = run_python_file

    # def test_get_files_info(self):
    #     result = self.get_files_info("calculator", ".")
    #     print(result+"\n")
    #     result = self.get_files_info("calculator", "pkg")
    #     print(result+"\n")
    #     result = self.get_files_info("calculator", "/bin")
    #     print(result+"\n")
    #     result = self.get_files_info("calculator", "../")
    #     print(result+"\n")
    #     result = self.get_files_info("calculator", None)
    #     print(result+"\n")

    # def test_get_file_content(self):
    #     result = self.get_file_content("calculator", "lorem.txt")
    #     print(result+"\n")
    #     result = self.get_file_content("calculator", "main.py")
    #     print(result+"\n")
    #     result = self.get_file_content("calculator", "pkg/calculator.py")
    #     print(result+"\n")
    #     result = self.get_file_content("calculator", "/bin/cat")
    #     print(result+"\n")

    # def test_write_file(self):
    #     result = self.write_file("calculator", "lorem.txt", "wait, this isn't lorem ipsum")
    #     print(result+"\n")
    #     result = self.write_file("calculator", "pkg/morelorem.txt", "lorem ipsum dolor sit amet")
    #     print(result+"\n")
    #     result = self.write_file("calculator", "/tmp/temp.txt", "this should not be allowed")
    #     print(result+"\n")

    def test_run_python_file(self):
        result = self.run_python_file("calculator", "main.py")
        print(result+"\n")
        result = self.run_python_file("calculator", "tests.py")
        print(result+"\n")
        result = self.run_python_file("calculator", "../main.py")
        print(result+"\n")
        result = self.run_python_file("calculator", "nonexistent.py")
        print(result+"\n")
    
if __name__ == "__main__":
    unittest.main()