from nmigen import *
from nmigen_cocotb import run
import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
from random import getrandbits




class Stream(Record):
    ##La clase Stream crea un record(un grupo de señales) 
    ##con un layout que se define en su constructor
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
            #while self.ready.value == 0:
            #    await RisingEdge(self.clk)
            #await RisingEdge(self.clk)
            #self.valid <= 0
            return self.ready.value

        async def control_recv(self, ready):
            self.ready <= ready
            await RisingEdge(self.clk)
            #while self.valid.value == 0:
            #    await RisingEdge(self.clk)
            #await RisingEdge(self.clk)
            #self.ready <= 0
            return (self.valid.value.integer, self.data.value.integer)
        
        async def read_all(self):
            #await RisingEdge(self.clk)
            #await RisingEdge(self.clk)
            return (self.ready.value.integer, self.valid.value.integer, self.data.value.integer)
        


class Adder(Elaboratable):
    def __init__(self, width):
        self.a = Stream(width, name='a')
        self.b = Stream(width, name='b')
        self.r = Stream(width+1, name='r')

    def elaborate(self, platform):
        m = Module()    #Creo un modulo a elaborar
        
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
        
        #Puedo leer un dato nuevo (pasar a ready) solo si el no hay usa salida valida o 
        #o si el dato de salida anterior ya fue leido.
        comb += self.a.ready.eq((~self.r.valid) | (self.r.accepted()))
        comb += self.b.ready.eq((~self.r.valid) | (self.r.accepted()))

        return m


#Pulso inicial de clock
async def init_test(dut):
    cocotb.fork(Clock(dut.clk, 10, 'ns').start())
    dut.rst <= 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst <= 0

def getSignedNumber(number, bitLength):
    mask = (2 ** bitLength) - 1
    if number & (1 << (bitLength - 1)):
        return number | ~mask
    else:
        return number & mask

@cocotb.test()
async def burst(dut):
    await init_test(dut)
    
    
    stream_input_a = Stream.Driver(dut.clk, dut, 'a__')
    stream_input_b = Stream.Driver(dut.clk, dut, 'b__')
    stream_output = Stream.Driver(dut.clk, dut, 'r__')

    N = 100
    width = len(dut.a__data)
    #mask = int('1' * (width+1), 2)

    #Generar datos random de entrada y los resultados esperados para el test 
    data_a = [getrandbits(width) for _ in range(N)]
    data_b = [getrandbits(width) for _ in range(N)]
    
    #Calculo los valores esperados como enteros signados
    expected = [(getSignedNumber(data_a[i],width) + getSignedNumber(data_b[i],width)) for i in range (N)] 
    #expected = [(data_a[i]+ data_b[i]) for i in range (N)]
    #Generar las señales de prueba con los datos random
    cocotb.fork(stream_input_a.send(data_a))    #Schedule a coroutine to be run concurrently.
    cocotb.fork(stream_input_b.send(data_b))
    
    recved = await stream_output.recv(N)
    recved_signed = [getSignedNumber(rec,width+1) for rec in recved] #Convierto los resultados en enteros signados  
    
    #Evaluacion de resultados
    assert recved_signed == expected

@cocotb.test()
async def test_control_signals(dut):

    await init_test(dut)
        
    stream_input_a = Stream.Driver(dut.clk, dut, 'a__')
    stream_input_b = Stream.Driver(dut.clk, dut, 'b__')
    stream_output = Stream.Driver(dut.clk, dut, 'r__')

    width = len(dut.a__data)

    #Test de señales de control
    
    expected=[]
    data_a = getrandbits(width)
    data_b = getrandbits(width)
    out = (getSignedNumber(data_a,width) + getSignedNumber(data_b,width))
    received =[]
    
    for i in range (5):
        #Tabla de valores (Cambiar por listas)
        if i==0:
            valid_a = 1
            valid_b = 1
            ready_r = 1
            
        elif i==1:
            valid_a = 1
            valid_b = 1
            ready_r = 0
            expected.append({'valid_r':1,'ready_a':0,"ready_b":0, "data_r":out})
            data_a+=1
            data_b+=1
            
        elif i==2:
            valid_a = 0
            valid_b = 0
            ready_r = 1
            expected.append({'valid_r':1,'ready_a':1,"ready_b":1, "data_r":out})
            data_a+=1
            data_b+=1
            
        elif i==3:
            valid_a = 1
            valid_b = 1
            ready_r = 0
            expected.append({'valid_r':0,'ready_a':1,"ready_b":1, "data_r":out})
            data_a+=1
            data_b+=1
            out = (getSignedNumber(data_a,width) + getSignedNumber(data_b,width))
                        
        elif i==4:
            #Reenvio el caso 3, solo para poder leer el resultado
            expected.append({'valid_r':1,'ready_a':0,"ready_b":0, "data_r":out})
            
        rec={}
        #Envio los datos y señales de control
        cocotb.fork(stream_input_a.control_send(valid_a,data_a))    
        cocotb.fork(stream_input_b.control_send(valid_b,data_b))
        await stream_output.control_recv(ready_r)
        data_r = int()

        #Leo los resultados (caso 0 los descarto porque es del ciclo anterior)
        if i>0:
            (rec ['ready_a'],_,_)= await stream_input_a.read_all()
            (rec ['ready_b'],_,_)= await stream_input_b.read_all()
            (_,rec ['valid_r'],data_r)= await stream_output.read_all()
            rec ['data_r']=getSignedNumber(data_r,width+1)
            received.append (rec)
    print (received)
    print (expected)
    assert received == expected

    


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