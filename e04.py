import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import re
import os
import datetime 

class VLSIStudio:
    """
    Aplicacion de VLSI completa:
    - Configurar parametros del sumador
    - Generar codifo de Verilog parametrizable (modulo + testbench)
    - Guardar archivos
    - Compilacion con iverilog
    - simulacion con vvp
    - Mostrar resultados en consola
    """

    ARQUITECTURAS = ["ripple_carry", "carry_lookahead", "carry_select", "carry_save"]
    TIMESCALES    = ["1ns/1ps", "1ns/100ps", "10ns/1ns"]
    KEYWORDS      = (r'\b(module|endmodule|input|output|wire|reg|assign|'
                    r'parameter|always|begin|end|if|else|for|initial|'
                    r'posedge|negedge|integer|localparam)\b')
    def __init__(self, root):
        self.root = root
        self.root.title("VLSI Studio - Genrador de Sumadores")
        self.root.geometry("1000x600")
        self.dir_trabajo = tk.StringVar(value=os.getcwd())
        
        self._construir_ui()
    
    def _construir_ui(self):
        #Encabezado
        header = tk.Frame(self.root, bg="#313138", pady=8)
        header.pack(fill="x")
        tk.Label(header, text="VLSI Studio",
                 font=("Arial", 14, "bold"), bg="#313138", 
                 fg="#388EAF").pack(side="left", padx=15)
        tk.Label(header, text="Generador - Compilador - Simulador de Sumadores en Verilog",
                 font=("Arial", 9), bg="#313138", 
                 fg="#207759").pack(side="left")
         
        #Panel Izquierdo (Parametros + botones)
        izq = tk.Frame(self.root, bg="#313138", width=200)
        izq.pack(side="left",fill="y")
        izq.pack_propagate(False)
        self._construir_panel_izq(izq)

        #Panel derecho (editor + consola)
        der = tk.Frame(self.root)
        der.pack(side="left",fill="both", expand=True)
        self._construir_panel_der(der)

        #Barra de estado
        self.status = tk.StringVar(value="Listo. Configura los parámetros y presiona Generar.")
        tk.Label(self.root, textvariable=self.status,
                 anchor="w", bg="#263238", fg="#80CBC4",
                 font=("Arial", 9), pady=3).pack(fill="x", side="bottom")

    def _construir_panel_izq(self, parent):
        def sec(texto):
            tk.Label(parent, text=texto,
                 font=("Arial", 9, "bold"), bg="#313138", 
                 fg="#345C7F").pack(fill="x", padx=0, pady=(10, 2))
        def lbl(texto):
             tk.Label(parent, text=texto,
                 font=("Arial", 8), bg="#313138", 
                 fg="#EBDBDB").pack(fill="x", padx=12, pady=(4, 0))

        #Parametros del modulo
        sec(" Modulo ")
        
        lbl("Nombre: ")
        self.e_mod = self._entry_dark(parent, "adder")

        lbl("Bits (N): ")
        self.e_n = self._entry_dark(parent, "4")

        lbl("Arquitectura: ")
        self.var_arq = tk.StringVar(value=self.ARQUITECTURAS[0])
        ttk.Combobox(parent, textvariable=self.var_arq, 
                     values=self.ARQUITECTURAS,
                     width=17, state="readonly").pack(padx=12, anchor="w")
        
        #Parametros del test bench
        sec(" TESTBENCH ")

        lbl("Numero de pruebas: ")
        self.e_test = self._entry_dark(parent, "20")

        lbl("Timescale: ")
        self.var_ts = tk.StringVar(value=self.TIMESCALES[0])
        ttk.Combobox(parent,textvariable=self.var_ts, values=self.TIMESCALES,
                     state="readonly", width=12).pack(padx=12, anchor="w")
        
        #Carry in y archivo vcd
        self.var_cin = tk.BooleanVar(value=True)
        self.var_vcd = tk.BooleanVar(value=True)

        for var, txt in [(self.var_cin, " Carry in"),
             (self.var_vcd, " Generar VCD")]:
            tk.Checkbutton(parent, text=txt, variable=var,
                           bg="#263338", fg="#FFFFFF", 
                           selectcolor="#370012", 
                           activebackground="#263338", 
                           font=("Arial", 9)).pack(
                            anchor='w', padx=10, pady=2)
        #Directorio
        sec(" DIRECTORIO de SALIDA ")
        frame_dir = tk.Frame(parent,bg="#263338")
        frame_dir.pack(fill="x", padx=12, pady=5)
        tk.Entry(frame_dir, textvariable=self.dir_trabajo, 
                 width=20,  bg="#313138", fg="white", 
                 font=("courier", 8)).pack(side="left")
        tk.Button(frame_dir, text="...", command=self._sel_dir,
                  width=5).pack(side="left", padx=3)
        
        #Botones de accion
        sec(" ACCIONES ")
        acciones = [
            ("  Generar codigo",    "#43CE43", self._generar),
            (    "  Guardar archivo", "#4345B9", self._guardar_archivos),
            (    "  Compilar ", "#8F4147", self._compilar),
            (    "  Simular ", "#9D32B5", self._simular),
            (    "  Todo en uno", "#B4B117", self._todo_en_uno)
        ]
        for txt, color, cmd in acciones:
            tk.Button(parent, text=txt, command=cmd,
                      bg=color, fg="white", font=("Arial", 9),
                      pady=5, activebackground=color).pack(
                          fill="x", padx=12, pady=2)
    
    def _construir_panel_der(self, parent):
        self.nb = ttk.Notebook(parent)
        self.nb.pack(fill="both", expand=True, pady=5)

        self.txt = {}
        pestanias = [
            ("modulo", "modulo.v"),
            ("tb", "testbench.v"),
            ("consola", "Consola")
        ]
        for key, label in pestanias:
            frame = tk.Frame(self.nb, bg ="#1E1E1E")
            self.nb.add(frame, text=label)
            t = scrolledtext.ScrolledText(
                frame, font=('consolas', 10),
                bg ="#1E1E1E", fg="white",
                insertbackground="white")
            t.pack(fill="both", expand=True)
            self.txt[key] = t
        
        for key in ("modulo", "tb"):
            self._setup_tags(self.txt[key])

    #Generacion de codigo en verilog
    def _gen_modulo(self, nombre, n, cin, ts):
        cin_port = ",\n    input          cin" if cin else ""
        cin_expr = " + cin" if cin else ""
        fecha    = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"`timescale {ts}\n"
            f"// {'='*54}\n"
            f"// Módulo  : {nombre}\n"
            f"// Desc.   : Sumador combinacional parametrizable {n} bits\n"
            f"// Generado: {fecha}\n"
            f"// {'='*54}\n\n"
            f"module {nombre} #(\n"
            f"    parameter N = {n}\n"
            f")(\n"
            f"    input  [N-1:0] a,\n"
            f"    input  [N-1:0] b{cin_port},\n"
            f"    output [N-1:0] sum,\n"
            f"    output         cout\n"
            f");\n"
            f"    assign {{cout, sum}} = a + b{cin_expr};\n\n"
            f"endmodule\n"
        )

    def _gen_testbench(self, nombre, n, cin, vcd, ts, num_t):
        cin_d   = "\n    reg          cin;" if cin else ""
        cin_c   = "\n        .cin  (cin)," if cin else ""
        cin_r   = "\n            cin = $random % 2;" if cin else ""
        cin_sum = " + cin" if cin else ""
        vcd_blk = (f'\n        $dumpfile("tb_{nombre}.vcd");\n'
                   f'        $dumpvars(0, tb_{nombre});') if vcd else ""
        fecha   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"`timescale {ts}\n"
            f"// {'='*54}\n"
            f"// Testbench: tb_{nombre}\n"
            f"// DUT      : {nombre} ({n} bits)\n"
            f"// Generado : {fecha}\n"
            f"// {'='*54}\n\n"
            f"module tb_{nombre};\n"
            f"    parameter N         = {n};\n"
            f"    parameter NUM_TESTS = {num_t};\n\n"
            f"    reg  [N-1:0] a, b;{cin_d}\n"
            f"    wire [N-1:0] sum;\n"
            f"    wire         cout;\n"
            f"    integer i, errors, passed;\n\n"
            f"    {nombre} #(.N(N)) dut (\n"
            f"        .a    (a),\n"
            f"        .b    (b),{cin_c}\n"
            f"        .sum  (sum),\n"
            f"        .cout (cout)\n"
            f"    );\n\n"
            f"    initial begin{vcd_blk}\n"
            f"        errors = 0; passed = 0;\n"
            f'        $display("\\n=== {nombre} | N=%0d | Tests=%0d ===\\n", N, NUM_TESTS);\n\n'
            f"        for (i = 0; i < NUM_TESTS; i = i + 1) begin\n"
            f"            a = $random % (1 << N);\n"
            f"            b = $random % (1 << N);{cin_r}\n"
            f"            #10;\n"
            f"            if ({{cout, sum}} !== (a + b{cin_sum})) begin\n"
            f'                $display("  FAIL [%0d] a=%0d b=%0d", i, a, b);\n'
            f"                errors = errors + 1;\n"
            f"            end else passed = passed + 1;\n"
            f"        end\n\n"
            f"        if (errors == 0)\n"
            f'            $display("  PASS: %0d/%0d tests correctos.\\n", passed, NUM_TESTS);\n'
            f"        else\n"
            f'            $display("  FAIL: %0d errores de %0d tests.\\n", errors, NUM_TESTS);\n\n'
            f"        $finish;\n"
            f"    end\n\nendmodule\n"
        )
    
    #Acciones
    def _generar(self):
        nombre, n, num_t = self._get_params()
        if nombre is None:
            return
        cin = self.var_cin.get()
        vcd = self.var_vcd.get()
        ts  = self.var_ts.get()

        mod = self._gen_modulo(nombre, n, cin, ts)
        tb  = self._gen_testbench(nombre, n, cin, vcd, ts, num_t)

        for key, codigo in [("modulo", mod), ("tb", tb)]:
            self.txt[key].delete("1.0", tk.END)
            self.txt[key].insert("1.0", codigo)
            self._highlight(self.txt[key], nombre)
        self._log(f"[{datetime.datetime.now():%H:%M:%S}] Codigo generado: "
                  f"{nombre} ({n} bits, cin = {'si' if cin else 'no'})", "info")
        self._set_status(f"Codigo generado para {nombre} {n} bits")
        self.nb.select(0)
    
    def _guardar_archivos(self):
        nombre, n, _= self._get_params()
        if nombre is None:
            return
        contenido_mod = self.txt["modulo"].get("1.0", tk.END).strip()
        if not contenido_mod:
            messagebox.showerror("Aviso", "Primero genera el codigo (Generar codigo)")
            return
        d = self.dir_trabajo.get()
        os.makedirs(d, exist_ok=True)
        archivos = {
            os.path.join(d, f"{nombre}.v"): self.txt["modulo"].get("1.0", tk.END),
            os.path.join(d, f"tb_{nombre}.v"): self.txt["tb"].get("1.0", tk.END),
        }
        for path, contenido in archivos.items():
            with open(path,'w', encoding="utf-8") as f:
                f.write(contenido)
            self._log(f"    Guardado: {path}", "ok")
        self._set_status(f"Archivos guardados en {d}")
        self.nb.select(2)  #Mostrar en consola
    
    def _compilar(self):
        nombre, n, _ = self._get_params()
        if nombre is None:
            return

        d   = self.dir_trabajo.get()
        mod = os.path.join(d, f"{nombre}.v")
        tb  = os.path.join(d, f"tb_{nombre}.v")
        out = os.path.join(d, f"sim_{nombre}")

        if not os.path.exists(mod) or not os.path.exists(tb):
            messagebox.showerror("Error",
                                 "Archivos .v no encontrados.\n"
                                 "Primero ejecuta ' Guardar archivos'.")
            return

        messagebox.showinfo("AQUI DEBES GENERAR CAMBIOS\n", 
                            "La idea es que puedas compilar "
                            "con Icarus (iverilog) y "
                            "ModelSim (vsim)")
        
        
        #ESTE ES UN EJEMPLO DE COMO SERRIA LA COMPILACION CON iverilog
        #USTEDES TENDRAN QUE GENERAR EL CODIGO PARA vsim
        # cmd = ["iverilog", "-o", out, tb, mod]
        # self._log(f"\n$ {' '.join(cmd)}", "info")
        # threading.Thread(
        #     target=self._ejecutar_cmd,
        #     args=(cmd, d, f"sim_{nombre}"),
        #     daemon=True
        # ).start()
        # self.nb.select(2)

    def _simular(self):
        messagebox.showinfo("AQUI DEBES DE GENERAR TU CODIGO\n", 
                            "Cuando lo tengas borra esta linea!!")
    
    def _todo_en_uno(self):
        self._generar()
        # Pequeñas pausas para que la GUI se actualice entre pasos
        self.root.after(200,  self._guardar_archivos)
        self.root.after(400,  self._compilar)
        self.root.after(1800, self._simular)

    #Helpers
    def _get_params(self):
        nombre = self.e_mod.get().strip() or "adder"
        try:
            n = int(self.e_n.get())
            assert 1 <= n <= 64
        except (ValueError, AssertionError):
            messagebox.showerror("Error", "N debe ser un entero entre 1 y 64" )
            return None, None, None
        try:
            num_t = int(self.e_test.get())
            assert num_t > 0
        except (ValueError, AssertionError):
            num_t = 30
        return nombre, n, num_t
    
    def _log(self, msg, tag=None):
        def _write():
            self.txt["consola"].insert(tk.END, str(msg) + "\n", tag or "")
            self.txt["consola"].see(tk.END)
        self.root.after(0, _write)

    # Esta funcion me sirve para crear entradas de texto con un 
    # estilo oscuro consistente en toda la aplicacion.
    def _entry_dark(self, parent, default):
        e = tk.Entry(parent, width=18, bg="#37474F", fg="white",
                     insertbackground="white", relief="flat",
                     font=("Courier", 10))
        e.insert(0, default)
        e.pack(padx=12, pady=(0, 2), anchor="w")
        return e

    #Esta funcion me sirve para configurar los estilos de texto 
    # para diferentes tipos de tokens en el editor de código.
    def _setup_tags(self, w):
        w.tag_configure("keyword", foreground="#569CD6")
        w.tag_configure("comment", foreground="#6A9955",
                         font=("Courier New", 10, "italic"))
        w.tag_configure("number",  foreground="#B5CEA8")
        w.tag_configure("macro",   foreground="#C586C0")
        w.tag_configure("modname", foreground="#4EC9B0",
                         font=("Courier New", 10, "bold"))
        w.tag_configure("string",  foreground="#CE9178")
    
    # Esta función se encarga de resaltar la sintaxis del código 
    # Verilog en el widget de texto.
    def _highlight(self, widget, mod_name):
        content = widget.get("1.0", tk.END)
        for tag in ["keyword", "comment", "number", "macro", "modname", "string"]:
            widget.tag_remove(tag, "1.0", tk.END)

        patterns = [
            ("keyword", self.KEYWORDS),
            ("comment", r'//[^\n]*'),
            ("number",  r'\b\d+\'[bBhHoOdD][0-9a-fA-FxXzZ_]+|\b\d+\b'), #En esta linea se busca números en formato Verilog, incluyendo literales binarios, hexadecimales, octales y decimales.
                                                                        # [bBhHoOdD] esto indica el tipo de literal (binario, hexadecimal, octal o decimal), 
                                                                        # seguido de una secuencia de dígitos que pueden incluir guiones bajos para mejorar la legibilidad.
                                                                        # \b\d+\b busca números enteros simples que no estén seguidos por un literal de base.
            ("macro",   r'`\w+'),
            ("modname", rf'\b({re.escape(mod_name)}|tb_{re.escape(mod_name)}|dut)\b'),
            ("string",  r'"[^"]*"'),
        ]
        for tag, pattern in patterns:
            for m in re.finditer(pattern, content):
                s = f"1.0 + {m.start()} chars"
                e = f"1.0 + {m.end()} chars"
                widget.tag_add(tag, s, e)

    # Esta función es para seleccionar un directorio utilizando 
    # un cuadro de diálogo
    def _sel_dir(self):
        d = filedialog.askdirectory(title="Directorio de trabajo")
        if d:
            self.dir_trabajo.set(d)
    
    # Esta función es para actualizar la barra de estado en la parte 
    # inferior de la aplicación.
    def _set_status(self, msg):
        self.root.after(0, lambda: self.status.set(msg))
        # lambada es una función anónima que se ejecuta después 
        # de 0 milisegundos para actualizar el texto de la barra 
        # de estado con el mensaje proporcionado.



    # Esta es para ejecutar comandos externos como si fueran hilos 
    # separados (Threads) esta funcion les ayudara en la simulacion
    # usando un threading.Thread
    def _ejecutar_cmd(self, cmd, cwd, ejecutable_generado):
        """
        Ejecuta un comando externo en un hilo separado para no bloquear la GUI.
        Comunica resultados de vuelta al hilo principal vía root.after().
        """
        try:
            resultado = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=30
            )
            salida = resultado.stdout + resultado.stderr

            if salida.strip():
                self._log(salida)

            if resultado.returncode == 0:
                msg_ok = (f"  Ejecutable generado: {ejecutable_generado}"
                          if ejecutable_generado else "   Simulación completada")
                self._log(msg_ok, "ok")
                self._set_status(f" {cmd[0]} exitoso")
            else:
                self._log(f"   Error (código {resultado.returncode})", "error")
                self._set_status(f" Error en {cmd[0]}")

        except FileNotFoundError:
            self._log(
                f"   '{cmd[0]}' no encontrado en PATH.\n"
                f"     Instala Icarus Verilog: https://steveicarus.github.io/iverilog/",
                "error"
            )
            self._set_status(f" {cmd[0]} no instalado")

        except subprocess.TimeoutExpired:
            self._log("   Timeout: el proceso superó 30 segundos.", "error")
            self._set_status(" Timeout")

# nuestro main
# 
root = tk.Tk()
app = VLSIStudio(root)
root.mainloop() 