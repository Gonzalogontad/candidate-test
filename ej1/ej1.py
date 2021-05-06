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
                        ('data', width), 
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



async def init_test(dut):
    cocotb.fork(Clock(dut.clk, 10, 'ns').start())
    dut.rst <= 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst <= 0


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
    expected = [(data_a[i] + data_b[i]) for i in range (N)]
    
    #Uso los drivers para generar las señales de prueba con los datos generados
    cocotb.fork(stream_input_a.send(data_a))    
    cocotb.fork(stream_input_b.send(data_b))
    recved = await stream_output.recv(N)
    
    #Evaluacion de resultados
    assert recved == expected


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