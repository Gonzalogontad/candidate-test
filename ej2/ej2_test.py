import os
from pathlib import Path
#Excepción para el test
class TestFail (Exception):
    pass


#Comparacion linea a linea de los archivos 'path_file_a' y 'path_file_b'
def files_compare(path_file_a,path_file_b):
    with open(path_file_a, 'r') as file_a , open(path_file_b, 'r') as file_b:
        #Leo ambos archivos
        lines_a = file_a.readlines()    
        lines_b = file_b.readlines()
        len_a = len(lines_a)
        len_b = len(lines_b)
        
        #Comparo ambos archivos
        if lines_a != lines_b:
            for i in range(len_a if len_a < len_b else len_b):
                a=lines_a[i]
                b=lines_b[i]
                if a!=b:
                    print (f'Error en linea: {i+1}')
                    print (f'Archivo a: {a}')
                    print (f'Archivo b: {b}')
            raise TestFail (f'Falla de test. Archivo: {path_file_a}') 
        

if __name__ == "__main__":
    #TEST 1
    print ('\n\n***Test 1***')
    print ('***Archivo verilog con una sola lista de asignacion de memoria***\n')
    results = []
    os.system("python3 ej2.py input/testcase.v -out_dir output/")
    #Evaluo resultados
    files_compare('output/memdump0.mem', 'input/exp_memdump0.mem')
    files_compare('output/mod_testcase.v', 'input/exp_testcase.v')
    #Si llega a este punto es porque los resultados son correctos
    print ('Test 1: Pass')
    

    #TEST 2
    print ('\n\n***Test 2***')
    print ('***Archivo verilog con multiples listas de asignasion de memoria***\n')
    results = []
    os.system("python3 ej2.py input/testcase2.v -out_dir output/")
    #Evaluo resultados
    files_compare('output/memdump0.mem', 'input/exp_memdump0.mem')
    files_compare('output/memdump1.mem', 'input/exp_memdump1.mem')
    files_compare('output/memdump2.mem', 'input/exp_memdump2.mem')
    files_compare('output/mod_testcase2.v', 'input/exp_testcase2.v')
    #Si llega a este punto es porque los resultados son correctos
    print ('Test 2: Pass')


    #TEST 3
    print ('\n\n***Test 3***')
    print ('***Archivo verilog sin datos***\n')

    output_file_path = 'output/mod_testcase3.v'
    output_file = Path(output_file_path)
    #Si el archivo de salida existe, lo elimino
    if output_file.is_file():
        os.remove(output_file_path)

    os.system("python3 ej2.py input/testcase3.v -out_dir output/")

    #Verifico que no se cree el archivo de salida
    if output_file.is_file():
        raise TestFail(f'Falla de test. Archivo: {output_file_path}')
    #Si llega a este punto es porque los resultados son correctos
    print ('Test 3: Pass\n')