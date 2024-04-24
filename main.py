from typing import Union  # Import tipe data Union untuk mendukung tipe data yang berbeda
from fastapi import FastAPI, Response, Request, HTTPException  # Import modul FastAPI dan komponennya
from fastapi.middleware.cors import CORSMiddleware  # Import middleware CORS
import sqlite3  # Import modul SQLite untuk berinteraksi dengan database

app = FastAPI()  # Inisialisasi aplikasi FastAPI

# Mengaktifkan CORS (Cross-Origin Resource Sharing) Middleware untuk mengizinkan akses lintas domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint untuk halaman awal
@app.get("/")
def read_root():
    return {"Hello": "World"}

# Endpoint untuk mengambil data mahasiswa berdasarkan NIM
@app.get("/mahasiswa/{nim}")
def ambil_mhs(nim: str):
    return {"nama": "Budi Martami"}

# Endpoint alternatif untuk mengambil data mahasiswa berdasarkan NIM
@app.get("/mahasiswa2/{nim}")
def ambil_mhs2(nim: str):
    return {"nama": "Budi Martami 2"}

# Endpoint untuk mendapatkan daftar mahasiswa berdasarkan ID provinsi dan angkatan
@app.get("/daftar_mhs/")
def daftar_mhs(id_prov: str, angkatan: str):
    return {"query": f"idprov: {id_prov}; angkatan: {angkatan}", "data": [{"nim": "1234"}, {"nim": "1235"}]}

# Endpoint untuk inisialisasi database
@app.get("/init/")
def init_db():
    try:
        DB_NAME = "upi.db"
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        create_table = """CREATE TABLE mahasiswa(
            ID          INTEGER PRIMARY KEY AUTOINCREMENT,
            nim         TEXT            NOT NULL,
            nama        TEXT            NOT NULL,
            id_prov     TEXT            NOT NULL,
            angkatan    TEXT            NOT NULL,
            tinggi_badan  INTEGER
        )  
        """
        cur.execute(create_table)
        con.commit
    except:
        return ({"status": "terjadi error"})
    finally:
        con.close()

    return ({"status": "ok, db dan tabel berhasil dicreate"})

# Mendefinisikan model data untuk mahasiswa
from pydantic import BaseModel
from typing import Optional

class Mhs(BaseModel):
    nim: str
    nama: str
    id_prov: str
    angkatan: str
    tinggi_badan: Optional[int] = None  # yang boleh null hanya ini

# Endpoint untuk menambahkan data mahasiswa
@app.post("/tambah_mhs/", response_model=Mhs, status_code=201)
def tambah_mhs(m: Mhs, response: Response, request: Request):
    try:
        DB_NAME = "upi.db"
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        # Hanya untuk test, rawal sql injection, gunakan spt SQLAlchemy
        cur.execute("""insert into mahasiswa (nim,nama,id_prov,angkatan,tinggi_badan) 
                        values ("{}","{}","{}","{}",{})""".format(m.nim, m.nama, m.id_prov, m.angkatan, m.tinggi_badan))
        con.commit()
    except:
        print("oioi error")
        return ({"status": "terjadi error"})
    finally:
        con.close()
    response.headers["Location"] = "/mahasiswa/{}".format(m.nim)
    print(m.nim)
    print(m.nama)
    print(m.angkatan)

    return m

# Endpoint untuk menampilkan semua data mahasiswa
@app.get("/tampilkan_semua_mhs/")
def tampil_semua_mhs():
    try:
        DB_NAME = "upi.db"
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        recs = []
        for row in cur.execute("select * from mahasiswa"):
            recs.append(row)
    except:
        return ({"status": "terjadi error"})
    finally:
        con.close()
    return {"data": recs}

from fastapi.encoders import jsonable_encoder

# Endpoint untuk mengupdate data mahasiswa menggunakan metode PUT
@app.put("/update_mhs_put/{nim}", response_model=Mhs)
def update_mhs_put(response: Response, nim: str, m: Mhs):
    try:
        DB_NAME = "upi.db"
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute("select * from mahasiswa where nim = ?", (nim,))
        existing_item = cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Terjadi exception: {}".format(str(e)))

    if existing_item:
        print(m.tinggi_badan)
        cur.execute("update mahasiswa set nama = ?, id_prov = ?, angkatan=?, tinggi_badan=? where nim=?",
                    (m.nama, m.id_prov, m.angkatan, m.tinggi_badan, nim))
        con.commit()
        response.headers["location"] = "/mahasiswa/{}".format(m.nim)
    else:
        print("item not found")
        raise HTTPException(status_code=404, detail="Item Not Found")

    con.close()
    return m

# Mendefinisikan model data untuk patching data mahasiswa
class MhsPatch(BaseModel):
    nama: str = "kosong"
    id_prov: str = "kosong"
    angkatan: str = "kosong"
    tinggi_badan: Optional[int] = -9999  # yang boleh null hanya ini

# Endpoint untuk mengupdate data mahasiswa menggunakan metode PATCH
@app.patch("/update_mhs_patch/{nim}", response_model=MhsPatch)
def update_mhs_patch(response: Response, nim: str, m: MhsPatch):
    try:
        print(str(m))
        DB_NAME = "upi.db"
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute("select * from mahasiswa where nim = ?", (nim,))
        existing_item = cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Terjadi exception: {}".format(str(e)))

    if existing_item:
        sqlstr = "update mahasiswa set "
        if m.nama != "kosong":
            if m.nama is not None:
                sqlstr = sqlstr + " nama = '{}' ,".format(m.nama)
            else:
                sqlstr = sqlstr + " nama = null ,"

        if m.angkatan != "kosong":
            if m.angkatan is not None:
                sqlstr = sqlstr + " angkatan = '{}' ,".format(m.angkatan)
            else:
                sqlstr = sqlstr + " angkatan = null ,"

        if m.id_prov != "kosong":
            if m.id_prov is not None:
                sqlstr = sqlstr + " id_prov = '{}' ,".format(m.id_prov)
            else:
                sqlstr = sqlstr + " id_prov = null, "

        if m.tinggi_badan != -9999:
            if m.tinggi_badan is not None:
                sqlstr = sqlstr + " tinggi_badan = {} ,".format(m.tinggi_badan)
            else:
                sqlstr = sqlstr + " tinggi_badan = null ,"

        sqlstr = sqlstr[:-1] + " where nim='{}' ".format(nim)
        print(sqlstr)
        try:
            cur.execute(sqlstr)
            con.commit()
            response.headers["location"] = "/mahasixswa/{}".format(nim)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Terjadi exception: {}".format(str(e)))

    else:
        raise HTTPException(status_code=404, detail="Item Not Found")

    con.close()
    return m

# Endpoint untuk menghapus data mahasiswa
@app.delete("/delete_mhs/{nim}")
def delete_mhs(nim: str):
    try:
        DB_NAME = "upi.db"
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        sqlstr = "delete from mahasiswa  where nim='{}'".format(nim)
        print(sqlstr)  # debug
        cur.execute(sqlstr)
        con.commit()
    except:
        return ({"status": "terjadi error"})
    finally:
        con.close()

    return {"status": "ok"}
