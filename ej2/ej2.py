import re
from pathlib import Path
import argparse

input_file_path= 'testcase.v'

#Devuelve el primer elemento de un iterable
#Se usa para el ordenamiento por clave
def first_element(iter):
    return int(iter[0])

#Recibe los datos 'data' con la estructura xxx[x] = 8'hxx;
#y guarda en el archivo 'file_name' ordenados
#'reverse hace un ordenamiento inverso
def save_mem_data(data, reverse, file_name, dir):
    
    data_pattern = r'    \S*\[(\S*)\] = 8\'\S(\S*);\n*'
    matches = re.findall(data_pattern,data) #Obtengo una matriz de datos

    if len(matches)==0:
        return False #Si no encontro datos no creo el archivo

    matches.sort(key=first_element,reverse=reverse) #Ordenamiento
    
    #Escritura de archivo
    try:    
        with open(f'{dir}{file_name}', 'w') as f:
            for value in matches:
                f.write(value[1]+'\n')
    except FileNotFoundError as FNFE:
        print (f'No se encontro diretorio de salida: {dir}')
        raise FNFE 

    return True

def verilog_data_dump (input_file_path, output_file_path):
    created_files=[]

    if len(output_file_path)>0:     
        if not output_file_path[-1]=='/': #Si el path no tiene '/' al final se la agrego
            output_file_path += '/'

    #Leo el archivo verilog
    try:
        with open(input_file_path,'r') as f:
            verilog_str=f.read()

            #obtengo el nombre del archivo verilog
            my_file = Path(input_file_path)
            verilog_filename = my_file.parts[-1]
    #Si no encuentro el archivo se detiene el programa
    except FileNotFoundError as FNFE:
        print (f'No se encontro el archivo: {input_file_path}')
        raise FNFE 
    
    #Reconocimiento de los bloques de memoria a guardar
    pattern = r'  reg \[(.*)\] (\S*) \[(.*)\];\n(  initial begin\n((    \S*\[\S*\] = \S*;\n)*)  end\n)'
    matches = re.findall(pattern,verilog_str)
    matches_count=0 #Numero de bloqued de memoria capturados
    
    for match in matches: 
        readmem_string=f'  $readmemh("memdump{matches_count}.mem", {match[1]});\n'
        mem_file_name = f'memdump{matches_count}.mem'
        
        #En cada coincidencia si hay datos los guardo en un archivo memdumpX
        if save_mem_data(match[4], False, mem_file_name,output_file_path) == True:
            matches_count+=1
            created_files.append(mem_file_name)
            #Reemplazo el bloque de datos por la linea readmemh
            # en el string del archivo verilog de salida.
            verilog_str = verilog_str.replace(match[3],readmem_string, 1)
        
    #Creo el archivo verilog de salida solo si hubieron coincidencia
    #Se le agrega el prefijo mod_ al nombre original
    if (matches_count>0):
        out = output_file_path+'mod_'+verilog_filename
        with open(out, 'w') as f:
            f.write(verilog_str)
        created_files.append(out)
        print ('Archivos creados:')
        for created_file in created_files:
            print (f'--{created_file}')
    else:
        print('No se encontraron datos para guardar')

    return len(created_files)



if __name__ == "__main__":

    #Capturo argumento de la terminal
    parser = argparse.ArgumentParser() 
    parser.add_argument('input_file_path', type=str, help='Path al achivo \".v\" a procesar') 
    parser.add_argument('-out_dir', type=str, help='Directorio de los archivos de salida. ADVERTENCIA: Sobreescribe si ya existe.', default='') 
    args = parser.parse_args()

    #Ejecuto el script
    verilog_data_dump (args.input_file_path, args.out_dir)
    

