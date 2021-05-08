import os

def files_compare(path_file_a,path_file_b):
    with open(path_file_a, 'r') as file_a:
        with open(path_file_b, 'r') as file_b:
            lines_a = file_a.readlines()
            lines_b = file_b.readlines()
            print (f'lines_a: {len(lines_a)}, lines_b: {len(lines_b)} ')
            if lines_a == lines_b:
                return True
            else:
                for i in range(len(lines_a)):
                    a=lines_a[i]
                    b=lines_b[i]
                    if a!=b:
                        print (f'Linea: {i+1}')
                        print (f'Archivo a: {a}')
                        print (f'Archivo b: {b}')
                return False


if __name__ == "__main__":
    print ('ejecutar script')
    os.system("python3 ej2.py testcase.v -out_dir output/")

    assert files_compare('output/memdump0.mem', 'expected/memdump0.mem')
    assert files_compare('output/mod_testcase.v', 'expected/expected.v')



    print('Test OK')