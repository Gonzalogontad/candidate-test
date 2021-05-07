from nmigen import *
from nmigen_cocotb import run
import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
from random import getrandbits


##La clase Stream crea un record(un grupo de señales) 
##con un layout que se define en su constructor
class Stream(Record):
    def __init__(self, width, **kwargs):
        Record.__init__ (self, [
                        ('data', signed(width)), 
                        ('valid', 1), 
                        ('ready', 1)], 
                        **kwargs)

    def accepted(self):
        return self.valid & self.ready
    
    class Driver:
        def __init__(self, clk, dut, prefix):
            self.clk = clk
            self.data = getattr(dut, prefix + 'data')
            self.valid = getattr(dut, prefix + 'valid')
            self.ready = getattr(dut, prefix + 'ready')

        async def send(self, data):
            self.valid <= 1
            for d in data:
                self.data <= d
                await RisingEdge(self.clk)
                while self.ready.value == 0:
                    await RisingEdge(self.clk)
            self.valid <= 0

        async def recv(self, count):
            self.ready <= 1
            data = []
            for _ in range(count):
                await RisingEdge(self.clk)
                while self.valid.value == 0:
                    await RisingEdge(self.clk)
                data.append(self.data.value.integer)
            self.ready <= 0
            return data
        
        async def control_send(self, valid, data):
            self.valid <= valid
            self.data <= data
            await RisingEdge(self.clk)
            
        async def control_recv(self, ready):
            self.ready <= ready
            await RisingEdge(self.clk)
        
        #Devuelve el estado de todos las señales
        async def read_all(self):
            return (self.ready.value.integer, self.valid.value.integer, self.data.value.integer)
        


class Adder(Elaboratable):
    def __init__(self, width):
        self.a = Stream(width, name='a')
        self.b = Stream(width, name='b')
        self.r = Stream(width+1, name='r')

    def elaborate(self, platform):
        m = Module()    #Creo el modulo
        
        #Obtengo los dominios
        sync = m.d.sync
        comb = m.d.comb 

        with m.If(self.r.accepted()):   #Dato anterior ya fue aceptado
            sync += self.r.valid.eq(0)  #y quito valid para calcular uno nuevo
        
        with m.If(self.a.accepted()& self.b.accepted()):   #Ambos datos de entrada deben ser validos
            sync += [
                self.r.data.eq(self.a.data + self.b.data), #para calcular el dato de salida
                self.r.valid.eq(1) 
            ]
        
        #Puedo leer un dato nuevo (pasar a ready) solo si no hay dato de salida valido o 
        #o si el dato de salida anterior ya fue leido.
        comb += self.a.ready.eq((~self.r.valid) | (self.r.accepted()))
        comb += self.b.ready.eq((~self.r.valid) | (self.r.accepted()))

        return m


#Generador de pulso inicial de clock y reset
async def init_test(dut):
    cocotb.fork(Clock(dut.clk, 10, 'ns').start())
    dut.rst <= 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst <= 0

#Funcion para convertir numeros signados de bitLegth bits a enteros signados
def getSignedNumber(number, bitLength):
    mask = (2 ** bitLength) - 1
    if number & (1 << (bitLength - 1)):
        return number | ~mask
    else:
        return number & mask

#Test de rafaga de datos
@cocotb.test()
async def burst(dut):
    await init_test(dut)
        
    stream_input_a = Stream.Driver(dut.clk, dut, 'a__')
    stream_input_b = Stream.Driver(dut.clk, dut, 'b__')
    stream_output = Stream.Driver(dut.clk, dut, 'r__')

    N = 100
    width = len(dut.a__data)
    
    #Generar datos random de entrada y los resultados esperados para el test 
    data_a = [getrandbits(width) for _ in range(N)]
    data_b = [getrandbits(width) for _ in range(N)]
    
    #Calculo los valores esperados como enteros signados
    expected = [(getSignedNumber(data_a[i],width) + getSignedNumber(data_b[i],width)) for i in range (N)] 
    cocotb.fork(stream_input_a.send(data_a))    #Schedule a coroutine to be run concurrently.
    cocotb.fork(stream_input_b.send(data_b))
    
    recved = await stream_output.recv(N)
    recved_signed = [getSignedNumber(rec,width+1) for rec in recved] #Convierto los resultados en enteros signados  
    
    #Evaluacion de resultados
    assert recved_signed == expected

#Test de señales de control: Prueba una secuencia de entradas y compara los resultados
#con los valores esperados
@cocotb.test()
async def test_control_signals(dut):
    #Genero un ciclo de clock
    await init_test(dut)

    #Creo los         
    stream_input_a = Stream.Driver(dut.clk, dut, 'a__')
    stream_input_b = Stream.Driver(dut.clk, dut, 'b__')
    stream_output = Stream.Driver(dut.clk, dut, 'r__')

    width = len(dut.a__data)
    
    data_a = getrandbits(width)
    data_b = getrandbits(width)
    out = (getSignedNumber(data_a,width) + getSignedNumber(data_b,width))
    
    #Entradas
    valid_a =[   1    ,    1     ,    0     ,     1    ]
    valid_b =[   1    ,    1     ,    0     ,     1    ]
    ready_r =[   1    ,    0     ,    1     ,     0    ]
    data_a  =[ data_a , data_a+1 , data_a+2 , data_a+3 ]
    data_b  =[ data_b , data_b+1 , data_b+2 , data_b+3 ]
    
    #Resultados esperados
    exp_ready_a = [ 0 , 1 , 1 ,  0  ]
    exp_ready_b = [ 0 , 1 , 1 ,  0  ]
    exp_valid_r = [ 1 , 1 , 0 ,  1  ]
    exp_data_r  = [out,out,out,out+6]
    
    #Resultados
    rec_ready_a = [None]*len(data_a)
    rec_ready_b = [None]*len(data_a)
    rec_valid_r = [None]*len(data_a)
    rec_data_r  = [None]*len(data_a)
   
    for i in range (len(data_a)+1):
        j=i
        if i>=len(data_a):
            j=len(data_a)-1 #repito la ultima combinacion para leer el resultado

        rec={}

        #Envio los datos y señales de control
        cocotb.fork(stream_input_a.control_send(valid_a[j],data_a[j]))    
        cocotb.fork(stream_input_b.control_send(valid_b[j],data_b[j]))
        await stream_output.control_recv(ready_r[j])
        
        #Leo los resultados (caso 0 los descarto porque es resultado del ciclo anterior)
        if i>0:
            (rec_ready_a[i-1],_,_)= await stream_input_a.read_all()
            (rec_ready_b[i-1],_,_)= await stream_input_b.read_all()
            (_,rec_valid_r[i-1],rec_data_r[i-1])= await stream_output.read_all()
            rec_data_r[i-1]=getSignedNumber(rec_data_r[i-1], width+1)

    
    print (f'exp_ready_a:{exp_ready_a}')
    print (f'rec_ready_a:{rec_ready_a}')
    print (f'exp_ready_b:{exp_ready_b}')
    print (f'rec_ready_b:{rec_ready_b}')
    print (f'exp_valid_r:{exp_valid_r}')
    print (f'rec_valid_r:{rec_valid_r}')
    print (f'exp_data_r :{exp_data_r}')      
    print (f'rec_data_r :{rec_data_r}')
    
    #Evaluacion de resultados
    assert (exp_ready_a == rec_ready_a) &(exp_ready_b==rec_ready_b)&(exp_valid_r==rec_valid_r)&(exp_data_r==rec_data_r)

    


if __name__ == '__main__':
    core = Adder(5)
    run(
        core, 'ej1',
        ports=
        [
            *list(core.a.fields.values()),
            *list(core.b.fields.values()),
            *list(core.r.fields.values())
        ],
        vcd_file='adder.vcd'
    )