# Ejercicio #2

Para ejecutar el script se deben pasar por parametro el path al archivo verilog que se quiere procesar (input_file_path) y opcionalmente el directorio donde se quieren guardar los archivos 
de salida (OUT_DIR).

  `python3 ej2.py input_file_path -out_dir OUT_DIR`

Por ejemplo:

  `python3 ej2.py input/testcase.v -out_dir output/`

Si, no se utiliza el parametro OUT_DIR, el script guarda los archivos de salida en el directorio local del script.

  `python3 ej2.py input/testcase.v`


Para ejecutar el test de este ejercicio usar el siguiente comando:

  `python3 ej2_test.py`

