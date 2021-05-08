import os

#Comparacion linea a linea de los archivos 'path_file_a' y 'path_file_b'
def files_compare(path_file_a,path_file_b):
    with open(path_file_a, 'r') as file_a:
        with open(path_file_b, 'r') as file_b:
            #Leo ambos archivos
            lines_a = file_a.readlines()    
            lines_b = file_b.readlines()
            len_a = len(lines_a)
            len_b = len(lines_b)
            #print (f'lines_a: {len_a}, lines_b: {len_b} ')
            #Comparo ambos archivos
            if lines_a == lines_b:
                return f'Pass: {path_file_b}'
            #Si hay diferencias muestro las lineas con error
            else: 
                for i in range(len_a if len_a < len_b else len_b):
                    a=lines_a[i]
                    b=lines_b[i]
                    if a!=b:
                        print (f'Linea: {i+1}')
                        print (f'Archivo a: {a}')
                        print (f'Archivo b: {b}')
                return f'Fail: {path_file_b}'


if __name__ == "__main__":
    #TEST 1
    print ('\n\n***Test 1***')
    print ('\n***Archivo verilog con una sola lista de asignacion de memoria***\n')
    results = []
    os.system("python3 ej2.py input/testcase.v -out_dir output/")

    results.append(files_compare('output/memdump0.mem', 'input/exp_memdump0.mem'))
    results.append(files_compare('output/mod_testcase.v', 'input/exp_testcase.v'))
    for result in results:
        print(result)

    #TEST 2
    print ('\n\n***Test 2***')
    print ('\n***Archivo verilog con multiples listas de asignasion de memoria***\n')
    results = []
    os.system("python3 ej2.py input/testcase2.v -out_dir output/")

    results.append(files_compare('output/memdump0.mem', 'input/exp_memdump0.mem'))
    results.append(files_compare('output/memdump1.mem', 'input/exp_memdump1.mem'))
    results.append(files_compare('output/memdump2.mem', 'input/exp_memdump2.mem'))
    results.append(files_compare('output/mod_testcase2.v', 'input/exp_testcase2.v'))
    for result in results:
        print(result)

    #TEST 3
    print ('\n\n***Test 3***')
    print ('\n***Archivo verilog si datos***\n')
    os.system("python3 ej2.py input/testcase3.v -out_dir output/")