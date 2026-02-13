import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from .config import Config
from .pipeline import process_pdf


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Split + Rename Certificados")
        self.geometry("980x420")
        self.pdf_path = tk.StringVar()
        self.vendor = tk.StringVar()
        self.out_dir = tk.StringVar(value=os.path.join(os.getcwd(), "salida_gui"))
        self.ocr_mode = tk.StringVar(value="auto")
        self.force_ocr = tk.BooleanVar(value=False)
        self.debug_mode = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Listo")
        self.running = False

        tk.Label(self, text="PDF").grid(row=0, column=0, sticky="w", padx=10, pady=8)
        tk.Entry(self, textvariable=self.pdf_path, width=90).grid(row=0, column=1, padx=8)
        tk.Button(self, text="Elegir", command=self.pick_pdf).grid(row=0, column=2)

        tk.Label(self, text="Vendor").grid(row=1, column=0, sticky="w", padx=10, pady=8)
        tk.Entry(self, textvariable=self.vendor, width=40).grid(row=1, column=1, sticky="w", padx=8)

        tk.Label(self, text="Salida").grid(row=2, column=0, sticky="w", padx=10, pady=8)
        tk.Entry(self, textvariable=self.out_dir, width=90).grid(row=2, column=1, padx=8)
        tk.Button(self, text="Cambiar", command=self.pick_out_dir).grid(row=2, column=2)

        lf = tk.LabelFrame(self, text="Opciones")
        lf.grid(row=3, column=0, columnspan=3, sticky="we", padx=10, pady=10)
        tk.Label(lf, text="OCR mode").grid(row=0, column=0, padx=8, pady=6)
        tk.OptionMenu(lf, self.ocr_mode, "auto", "none", "skip", "redo", "force").grid(row=0, column=1)
        tk.Checkbutton(lf, text="Forzar OCR siempre", variable=self.force_ocr).grid(row=0, column=2, padx=12)
        tk.Checkbutton(lf, text="Modo debug", variable=self.debug_mode).grid(row=0, column=3, padx=12)

        tk.Label(self, textvariable=self.status, fg="blue").grid(row=4, column=0, columnspan=2, sticky="w", padx=10)
        self.btn = tk.Button(self, text="Procesar", command=self.run_process, width=16, height=2)
        self.btn.grid(row=4, column=2, pady=8)

    def pick_pdf(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p:
            self.pdf_path.set(p)

    def pick_out_dir(self):
        p = filedialog.askdirectory()
        if p:
            self.out_dir.set(p)

    def set_status(self, msg: str):
        self.status.set(msg)
        self.update_idletasks()

    def _cfg(self) -> Config:
        return Config(ocr_mode=self.ocr_mode.get(), force_ocr_always=bool(self.force_ocr.get()), debug_mode=bool(self.debug_mode.get()))

    def _worker(self, pdf: str, vendor: str, out_dir: str, cfg: Config):
        try:
            outs = process_pdf(pdf, vendor, out_dir, cfg, status_cb=lambda m: self.after(0, self.set_status, m))
            self.after(0, self.set_status, "Terminado")
            self.after(0, lambda: messagebox.showinfo("OK", f"Generados {len(outs)} PDFs"))
        except Exception as e:
            self.after(0, self.set_status, "Error")
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.running = False
            self.after(0, lambda: self.btn.config(state="normal"))

    def run_process(self):
        if self.running:
            return
        pdf = self.pdf_path.get().strip()
        if not pdf or not os.path.exists(pdf):
            messagebox.showerror("Error", "Selecciona un PDF válido")
            return
        cfg = self._cfg()
        self.running = True
        self.btn.config(state="disabled")
        th = threading.Thread(target=self._worker, args=(pdf, self.vendor.get().strip(), self.out_dir.get().strip(), cfg), daemon=True)
        th.start()


def run_gui() -> None:
    app = App()
    app.mainloop()
