from flask import Flask, request, send_file
import pandas as pd
from fuzzywuzzy import fuzz
import os

app = Flask(__name__)

# Buat folder uploads jika belum ada
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Fungsi pengecekan tunggakan
def check_tunggakan(file_kendaraan_baru, file_tunggakan):
    data_kendaraan_baru = pd.read_excel(file_kendaraan_baru)
    data_tunggakan = pd.read_excel(file_tunggakan)

    # Normalisasi nama kolom
    data_kendaraan_baru.columns = data_kendaraan_baru.columns.str.upper()
    data_tunggakan.columns = data_tunggakan.columns.str.upper()

    # Pastikan hanya kolom yang diperlukan
    if not {'NOPOL', 'NAMA', 'ALAMAT', 'NIK'}.issubset(data_tunggakan.columns):
        return "Format file tunggakan salah!", 400

    data_tunggakan = data_tunggakan[['NOPOL', 'NAMA', 'ALAMAT', 'NIK']]

    hasil_pengecekan = []
    for _, kendaraan_baru in data_kendaraan_baru.iterrows():
        nama_baru, alamat_baru, nik_baru = kendaraan_baru["NAMA"], kendaraan_baru["ALAMAT"], kendaraan_baru["NIK"]
        ada_tunggakan = False

        for _, tunggakan in data_tunggakan.iterrows():
            match_count = sum([
                fuzz.ratio(nama_baru, tunggakan["NAMA"]) >= 80,
                fuzz.ratio(alamat_baru, tunggakan["ALAMAT"]) >= 80,
                str(nik_baru) == str(tunggakan["NIK"])
            ])

            if match_count >= 2:
                ada_tunggakan = True
                break

        hasil_pengecekan.append({
            "NOPOL": kendaraan_baru["NOPOL"],
            "NAMA": nama_baru,
            "ALAMAT": alamat_baru,
            "NIK": nik_baru,
            "STATUS": "ADA TUNGGAKAN" if ada_tunggakan else "TIDAK ADA TUNGGAKAN"
        })

    hasil_df = pd.DataFrame(hasil_pengecekan)
    output_file = os.path.join(UPLOAD_FOLDER, "Hasil_Pengecekan.xlsx")
    hasil_df.to_excel(output_file, index=False)
    return output_file

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file_kendaraan' not in request.files or 'file_tunggakan' not in request.files:
            return "File tidak ditemukan!", 400

        file_kendaraan_baru = request.files['file_kendaraan']
        file_tunggakan = request.files['file_tunggakan']

        if file_kendaraan_baru.filename == '' or file_tunggakan.filename == '':
            return "Nama file tidak boleh kosong!", 400

        kendaraan_path = os.path.join(UPLOAD_FOLDER, file_kendaraan_baru.filename)
        tunggakan_path = os.path.join(UPLOAD_FOLDER, file_tunggakan.filename)

        file_kendaraan_baru.save(kendaraan_path)
        file_tunggakan.save(tunggakan_path)

        hasil_file = check_tunggakan(kendaraan_path, tunggakan_path)
        return send_file(hasil_file, as_attachment=True)

    return '''
    <!doctype html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pengecekan Tunggakan Pajak</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin: 50px; }
            form { margin: 20px auto; width: 50%; padding: 20px; border: 1px solid #ccc; border-radius: 10px; }
            input, button { margin: 10px; padding: 10px; width: 80%; }
        </style>
    </head>
    <body>
        <h2>Pengecekan Tunggakan Pajak Kendaraan</h2>
        <form action="/" method="post" enctype="multipart/form-data">
            <label>Upload Data Kendaraan Baru:</label><br>
            <input type="file" name="file_kendaraan" required><br>
            <label>Upload Data Tunggakan Pajak:</label><br>
            <input type="file" name="file_tunggakan" required><br>
            <button type="submit">Cek Tunggakan</button>
        </form>
    </body>
    </html>
    '''

# Perbaiki kode untuk Railway (PORT otomatis)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
