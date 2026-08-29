"""
hacar_deploy/tests/test_connection_v2.py (draf — belum ditempatkan resmi)
=============================================================================
Client uji koneksi TCP ke buoy aux_vcu (ESP32) — mem-parsing protokol
telemetri gaya NMEA 0183 dengan checksum XOR.

PENGGANTI test_connection.py (v1): v1 hanya mencetak byte mentah yang
tiba tanpa mengurai apa pun. Skrip ini mengurai frame NMEA-style, memvalidasi
checksum, dan mendekode sentence GDAT2 (General Data Telemetry) ke nilai
bertipe & bersatuan.

STATUS SUMBER PROTOKOL — TERVERIFIKASI SEBAGIAN (2026-07-24)
--------------------------------------------------------------
Dokumen protokol asli ("TELEMETRY PROTOCOL") ternyata memuat DUA kesalahan
pada bagian ilustrasi/contohnya (bukan pada definisi "Format:"-nya), yang
sudah dikonfirmasi terhadap satu paket sungguhan dari buoy 1:

  paket nyata: $GDAT2,4219999A,40533333,0,0,0,0,0,0,0,0,0,71*66

  1. Jumlah field: KONFIRMED 12 field (ulRaw[0..9] + seq + cnt), SESUAI
     baris "Format:" di dokumen. Contoh 10-field di dokumen SALAH/tidak
     representatif — bukan mode kedua yang perlu didukung, hanya kesalahan
     penulisan contoh. `decode_gdat2()` TETAP menerima mode-10 sebagai
     fallback toleran (lihat kode), tapi mode-12 kini status TERVERIFIKASI,
     bukan lagi dugaan.
  2. Checksum: KONFIRMED — XOR seluruh byte ANTARA '$' dan '*' (keduanya
     TIDAK diikutkan) cocok persis dengan checksum device (0x66 == 0x66
     pada paket contoh di atas). Contoh checksum '*2F' di dokumen asli
     SALAH HITUNG, bukan indikasi algoritma XOR-nya berbeda.
  3. Bit-cast IEEE-754 big-endian juga terverifikasi masuk akal: 0x4219999A
     -> 38.4 dan 0x40533333 -> 3.3 (dua field pertama). Contoh dokumen
     "42.5°C = 0x42280000" tetap SALAH (0x42280000 sebenarnya 42.0, bukan
     42.5) — kemungkinan salah ketik penulis dokumen (0x422A0000 yang benar
     untuk 42.5), belum dikonfirmasi ke pembuat protokol.

PETA FIELD BERUBAH (firmware 2026-07-27) — BACA SEBELUM MEMBANDINGKAN
--------------------------------------------------------------------
Firmware menambah `depth_temp_c` dan MENGGESER seluruh field sesudahnya;
`cpu_temp_c` hilang. Peta lama vs baru:

    lama (≤ 2026-07-24)          baru (≥ 2026-07-27, dipakai sekarang)
    0 cpu_temp_c                 0 leak_v
    1 leak_v                     1 voltage_v
    2 voltage_v                  2 depth_m
    3 depth_m                    3 depth_temp_c      <- BARU
    4 digital_io                 4 roll_deg
    5 roll_deg                   5 pitch_deg
    6 pitch_deg                  6 yaw_deg
    7 yaw_deg                    7 altimeter_dist_mm
    8 altimeter_dist_mm          8 altimeter_conf_pct
    9 altimeter_conf_pct         9 digital_io

Akibatnya paket contoh 2026-07-24 di atas TIDAK boleh dibaca dengan peta
baru: 0x4219999A yang dulu "suhu CPU 38,4 °C" kini akan terbaca
`leak_v = 38,4 V` — masih di dalam rentang wajar, jadi TIDAK akan
tertangkap penjaga rentang. Contoh itu dipertahankan hanya sebagai bukti
framing/checksum, bukan bukti nilai per-besaran.

Skrip ini TIDAK lagi menyalin peta field; ia meng-IMPOR
`_GDAT2_NAMA` / `_GDAT2_FLOAT_IDX` / `RENTANG_WAJAR` dari
`core/sensor_link.py`. Pergeseran berikutnya cukup disunting di satu
tempat, dan uji ini ikut bergeser sendiri — penyebab bug kelas ini
adalah dua salinan peta yang menyimpang diam-diam.

  Yang BELUM terverifikasi: pada peta BARU belum ada satu pun paket nyata
  yang tersedia, jadi tidak ada satu besaran pun yang punya bukti nilai
  nonzero masuk akal. Pada peta lama hanya dua field pertama yang pernah
  nonzero; sisanya nol — belum jelas apakah karena buoy belum
  terendam/sensor belum aktif, atau firmware memang belum mengisinya.
  JANGAN anggap nol berarti "field ini terverifikasi berfungsi".

  Field ulRaw[8] dan ulRaw[9] (jarak altimeter & confidence) menurut catatan
  "encoding notes" TETAP diserialkan sebagai 8-hex-digit meski isinya
  integer bulat, namun contoh paket memuat "123" (3 digit, bukan
  "0000007b"). Parser di bawah menerima hex dengan panjang berapa pun
  (di-pad ke kiri) — bukan berarti format ini sudah dianggap benar,
  hanya supaya parser tidak gagal total pada satu variasi encoding.

  IEEE-754: field yang didokumentasikan sebagai float (leak, voltage, depth,
  depth_temp, roll, pitch, yaw) di-bitcast big-endian 32-bit sesuai
  contoh (0x42280000 = 42.5). Field lain (digital I/O, altimeter dist,
  altimeter conf) diperlakukan sebagai integer biasa, KARENA dokumen tidak
  menyebutnya IEEE-754 float — hanya menyebut ulRaw SECARA UMUM "even when
  carrying integer data" diserialkan 8-hex-digit, yang konsisten dengan
  representasi integer (bukan float) untuk ketiga field itu.

ALAMAT BUOY
-----------
4 buoy @ port 8080, dibedakan oktet ke-3 IP (.110/.120/.130/.140).
Operator menyatakan HANYA buoy 1 (.110) yang aktif saat ini — buoy 2-4
sengaja DINONAKTIFKAN (bukan dihapus) di BUOY_IPS di bawah, supaya
tinggal di-uncomment saat buoy itu online, tanpa perlu mengingat lagi
skema pengalamatannya.

Jalankan:
    python test_connection_v2.py                  # buoy 1, cetak terurai
    python test_connection_v2.py --buoy 1 --raw    # cetak baris mentah saja
    python test_connection_v2.py --host 192.168.3.199 --port 8080
    python test_connection_v2.py --n-frames 20     # berhenti setelah 20 GDAT2 valid
=============================================================================
"""

from __future__ import annotations

import argparse
import socket
import struct
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Alamat buoy
# ---------------------------------------------------------------------------
PORT = 8080

# Buoy 1 terverifikasi aktif (dipakai test_connection.py v1). Buoy 2-4
# TIDAK di-uncomment di sini secara sengaja -- alamatnya belum dikonfirmasi
# online, dan menambahkannya "kalau-kalau" bisa membuat skrip mencoba
# menyambung ke buoy yang belum siap lalu timeout diam-diam.
BUOY_IPS: Dict[int, str] = {
    1: "192.168.3.110",
    # 2: "192.168.3.120",   # buoy 2 -- uncomment saat online & terverifikasi
    # 3: "192.168.3.130",   # buoy 3 -- uncomment saat online & terverifikasi
    # 4: "192.168.3.140",   # buoy 4 -- uncomment saat online & terverifikasi
}

MAX_FRAME_CHARS = 128   # batas dari spesifikasi; frame lebih panjang dicurigai


# ---------------------------------------------------------------------------
# Kesalahan khusus -- dipisah dari ValueError generik supaya pemanggil bisa
# membedakan "frame rusak/tidak lengkap" dari "checksum tidak cocok" dari
# "bukan GDAT2 sama sekali", tanpa mem-parsing ulang pesan galat.
# ---------------------------------------------------------------------------

class NmeaFrameError(ValueError):
    """Frame tidak berbentuk NMEA yang sah (tanpa '$'/'*', dsb)."""


class NmeaChecksumError(ValueError):
    """Frame berbentuk sah tetapi checksum XOR tidak cocok."""


# ---------------------------------------------------------------------------
# Framing + checksum NMEA-0183-style
# ---------------------------------------------------------------------------

def nmea_checksum(payload: str) -> int:
    """
    XOR 8-bit seluruh byte ASCII `payload` (isi ANTARA '$' dan '*',
    keduanya TIDAK diikutkan -- konvensi NMEA 0183 standar).
    """
    cs = 0
    for b in payload.encode("ascii", errors="strict"):
        cs ^= b
    return cs & 0xFF


def parse_nmea_frame(line: str) -> Tuple[str, List[str]]:
    """
    Urai satu baris frame `$XXXXX,f1,...,fN*HH` -> (sentence_id, [f1..fN]).

    Memvalidasi:
      - diawali '$'
      - mengandung '*' diikuti tepat 2 digit hex
      - checksum XOR cocok
      - panjang frame <= MAX_FRAME_CHARS (peringatan, bukan penolakan --
        batas ini dari spesifikasi, belum tentu ditegakkan pengirim)

    Raises
    ------
    NmeaFrameError     -- bentuk frame tidak sah
    NmeaChecksumError   -- checksum tidak cocok
    """
    raw = line.strip("\r\n")
    if len(raw) > MAX_FRAME_CHARS:
        print(f"[WARN] frame {len(raw)} char > batas spesifikasi "
              f"{MAX_FRAME_CHARS} char: {raw[:40]}...", file=sys.stderr)

    if not raw.startswith("$"):
        raise NmeaFrameError(f"tidak diawali '$': {raw[:40]!r}")
    if "*" not in raw:
        raise NmeaFrameError(f"tidak ada '*' checksum: {raw[:40]!r}")

    body, _, chk_str = raw[1:].rpartition("*")
    if len(chk_str) != 2:
        raise NmeaFrameError(
            f"checksum bukan 2 digit hex: {chk_str!r} (frame: {raw[:40]!r})")
    try:
        chk_expected = int(chk_str, 16)
    except ValueError:
        raise NmeaFrameError(f"checksum bukan hex sah: {chk_str!r}")

    chk_actual = nmea_checksum(body)
    if chk_actual != chk_expected:
        raise NmeaChecksumError(
            f"checksum tak cocok: dapat {chk_actual:02X}, "
            f"harap {chk_expected:02X} (frame: {raw[:60]!r})")

    fields = body.split(",")
    if not fields or not fields[0]:
        raise NmeaFrameError(f"sentence ID kosong: {raw[:40]!r}")
    sentence_id, rest = fields[0], fields[1:]
    return sentence_id, rest


# ---------------------------------------------------------------------------
# Dekode nilai
# ---------------------------------------------------------------------------

def hex_to_f32(h: str) -> float:
    """Bit-cast string hex (big-endian, di-pad kiri ke 8 digit) -> float32."""
    h = h.strip()
    if not h:
        raise ValueError("hex kosong")
    h = h.rjust(8, "0")
    if len(h) != 8:
        raise ValueError(f"hex float harus <=8 digit, dapat {len(h)}: {h!r}")
    return struct.unpack(">f", bytes.fromhex(h))[0]


def hex_to_int(h: str) -> int:
    """Hex (panjang berapa pun) -> int. Lihat catatan header soal ulRaw[8]/[9]."""
    h = h.strip()
    if not h:
        raise ValueError("hex kosong")
    return int(h, 16)


# ---------------------------------------------------------------------------
# Sentence GDAT2 (ID=37) -- General Data Telemetry
# ---------------------------------------------------------------------------

# Field float (bitcast IEEE-754) vs integer biasa, sesuai dokumen protokol --
# lihat catatan "IEEE-754" di header modul untuk alasan pembagian ini.
# Peta field DIIMPOR dari aplikasi, tidak disalin.
#
# Versi sebelumnya menyalin petanya ke sini, dan saat firmware menambah
# `depth_temp_c` (spesifikasi 2026-07-27) peta di aplikasi berubah
# sementara peta di skrip uji tidak. Akibatnya bukan galat melainkan
# NILAI YANG SALAH TEMPAT: seluruh field bergeser satu posisi dan
# `digital_io` pindah dari indeks 4 ke 9, sehingga roll terbaca sebagai
# depth_temp dan status motor terbaca dari altimeter — semuanya tetap
# tercetak rapi dengan satuan yang benar.
#
# Peta yang disalin akan menyimpang lagi pada revisi firmware berikutnya.
# Mengimpornya membuat skrip uji ini mustahil ketinggalan.
try:
    from hacar_deploy.core.sensor_link import (GDAT2_VERSI,
                                               RENTANG_WAJAR,
                                               _GDAT2_FLOAT_IDX,
                                               _GDAT2_NAMA)
except ImportError:                                        # pragma: no cover
    import sys as _s
    from pathlib import Path as _P
    _s.path.insert(0, str(_P(__file__).resolve().parents[2]))
    from hacar_deploy.core.sensor_link import (GDAT2_VERSI,
                                               RENTANG_WAJAR,
                                               _GDAT2_FLOAT_IDX,
                                               _GDAT2_NAMA)

_IDX = {nama: i for i, nama in enumerate(_GDAT2_NAMA)}


@dataclass
class Gdat2Frame:
    """
    Satu paket GDAT2 terdekode.

    Nilai disimpan dalam `nilai` (nama -> angka) yang dibangun dari peta
    aplikasi, bukan sebagai atribut tetap. Atribut tetap memaksa berkas ini
    disunting tiap kali firmware menambah field — dan itulah yang membuat
    `depth_temp_c` sempat terlewat.
    """
    nilai: Dict[str, float]
    seq: Optional[int]          # None bila paket mode-10 (lihat field_mode)
    cnt: int
    field_mode: str             # '12' (ulRaw+seq+cnt) atau '10' (ulRaw saja)
    n_fields_seen: int
    raw_fields: List[str] = field(default_factory=list)

    def __getattr__(self, nama):
        """Akses gaya lama `g.depth_m` tetap bekerja."""
        try:
            return object.__getattribute__(self, 'nilai')[nama]
        except KeyError:
            raise AttributeError(nama) from None

    @property
    def digital_io(self) -> int:
        return int(self.nilai.get('digital_io', 0))

    @property
    def motor_open(self) -> bool:
        return bool(self.digital_io & 0b01)

    @property
    def motor_close(self) -> bool:
        return bool(self.digital_io & 0b10)

    def tak_wajar(self) -> List[str]:
        """Field di luar rentang fisis — memakai ambang aplikasi."""
        buruk = []
        for nama, (lo, hi) in RENTANG_WAJAR.items():
            v = self.nilai.get(nama)
            if v is None:
                continue
            if not (lo <= float(v) <= hi):
                buruk.append(f'{nama}={float(v):g} (wajar {lo:g}..{hi:g})')
        return buruk


def decode_gdat2(fields: List[str]) -> Gdat2Frame:
    """
    Urai field GDAT2 (list string setelah 'GDAT2,') -> Gdat2Frame.

    Menerima 12 field (ulRaw[0..9] + seq + cnt) atau 10 field (ulRaw saja).
    Jumlah lain ditolak sebagai galat, bukan ditebak.
    """
    n = len(fields)
    if n == 12:
        ulraw, seq_s, cnt_s = fields[:10], fields[10], fields[11]
        mode = "12"
        cnt_val = hex_to_int(cnt_s)
    elif n == 10:
        ulraw, seq_s = fields, None
        mode = "10"
        cnt_val = 0
    else:
        raise NmeaFrameError(
            f"GDAT2 diharapkan 10 atau 12 field, dapat {n}: {fields}")

    nilai: Dict[str, float] = {}
    for i, h in enumerate(ulraw):
        if i >= len(_GDAT2_NAMA):
            break
        v = hex_to_f32(h) if i in _GDAT2_FLOAT_IDX else hex_to_int(h)
        nilai[_GDAT2_NAMA[i]] = v

    return Gdat2Frame(
        nilai=nilai,
        seq=(hex_to_int(seq_s) if seq_s is not None else None),
        cnt=cnt_val,
        field_mode=mode,
        n_fields_seen=n,
        raw_fields=list(fields),
    )


# Anotasi ekspektasi per-medium (uji-bangku udara vs deploy laut)
# ---------------------------------------------------------------------------
# Field yang WAJAR diam/nol di udara karena butuh kopling fisik ke air
# (tekanan hidrostatik, akustik) untuk berarti apa pun.
_QUIET_IN_AIR = {"depth_m", "altimeter_dist_mm", "altimeter_conf_pct"}

# Field yang HARUS tetap hidup terlepas medium -- kalau nol di udara,
# itu petunjuk wiring/firmware, BUKAN efek medium.
_ALWAYS_LIVE = {"leak_v", "voltage_v", "depth_temp_c",
                "roll_deg", "pitch_deg", "yaw_deg"}


def medium_annotations(g: Gdat2Frame, medium: Optional[str]) -> Dict[str, str]:
    """
    Beri catatan per-field sesuai medium uji ('air' | 'sea' | None).

    None -> tidak ada anotasi (perilaku lama, netral).
    'air' -> field di _QUIET_IN_AIR yang nol ditandai NORMAL, field di
             _ALWAYS_LIVE yang nol ditandai WASPADA (harusnya tetap hidup).
    'sea' -> semua field dianggap harus hidup; field di _QUIET_IN_AIR yang
             nol ditandai WASPADA (di laut seharusnya tidak nol terus).

    Returns
    -------
    dict nama_field -> teks anotasi pendek (field tanpa catatan tak muncul
    di dict, supaya pemanggil bisa `dict.get(nama, '')`).
    """
    if medium not in ("air", "sea"):
        return {}
    notes: Dict[str, str] = {}
    # Iterasi peta aplikasi, bukan daftar tetap: daftar tetap di sini akan
    # jadi salinan kedua yang menyimpang diam-diam tiap firmware bergeser.
    # digital_io dikecualikan -- nol padanya berarti "motor diam", bukan
    # "sensor mati", jadi aturan zero-is-suspicious tidak berlaku.
    vals = {n: v for n, v in g.nilai.items() if n != "digital_io"}
    for name, v in vals.items():
        is_zero = (v == 0)
        if medium == "air":
            if name in _QUIET_IN_AIR and is_zero:
                notes[name] = "normal: tidak bermakna di udara"
            elif name in _QUIET_IN_AIR and not is_zero:
                notes[name] = ("WASPADA: ada bacaan di udara -- cek validitas "
                               "(mungkin echo/derau palsu, bukan pengukuran nyata)")
            elif name in _ALWAYS_LIVE and is_zero:
                notes[name] = "WASPADA: field ini seharusnya hidup meski di udara"
        elif medium == "sea":
            if name in _QUIET_IN_AIR and is_zero:
                notes[name] = "WASPADA: di laut seharusnya tidak nol terus"
            elif name in _ALWAYS_LIVE and is_zero:
                notes[name] = "WASPADA: field ini seharusnya hidup"
    return notes


# ---------------------------------------------------------------------------
# Pembaca baris ter-buffer dari socket TCP
# ---------------------------------------------------------------------------

class LineBufferedSocketReader:
    """
    TCP adalah aliran byte, bukan aliran pesan -- satu recv() bisa memuat
    setengah frame, satu frame utuh, atau beberapa frame sekaligus. Kelas
    ini menyangga byte mentah dan hanya menyerahkan baris yang SUDAH
    diakhiri CRLF, sesuai spesifikasi ("<CR><LF> -- CRLF line terminator").
    """

    def __init__(self, sock: socket.socket, chunk_size: int = 1024):
        self._sock = sock
        self._chunk_size = chunk_size
        self._buf = b""

    def readlines(self, timeout_s: Optional[float] = None) -> List[str]:
        """Baca sekali dari socket, kembalikan 0+ baris lengkap yang siap urai."""
        if timeout_s is not None:
            self._sock.settimeout(timeout_s)
        data = self._sock.recv(self._chunk_size)
        if not data:
            raise ConnectionError("koneksi ditutup peer (recv 0 byte)")
        self._buf += data

        lines: List[str] = []
        while b"\r\n" in self._buf:
            raw_line, self._buf = self._buf.split(b"\r\n", 1)
            try:
                lines.append(raw_line.decode("ascii"))
            except UnicodeDecodeError as exc:
                print(f"[WARN] baris bukan ASCII murni, dilewati: {exc}",
                      file=sys.stderr)
        return lines


# ---------------------------------------------------------------------------
# Loop utama
# ---------------------------------------------------------------------------

def _note(notes: Dict[str, str], name: str) -> str:
    txt = notes.get(name, "")
    return f"  <{txt}>" if txt else ""


def _fmt_frame(g: Gdat2Frame, medium: Optional[str] = None) -> str:
    peringatan = "" if g.field_mode == "12" else "  [mode-10, seq=None -- lihat catatan header]"
    notes = medium_annotations(g, medium)
    baris = [
        f"  bocor={g.nilai.get('leak_v', 0):5.2f}V{_note(notes,'leak_v')}",
        f"  tegangan={g.nilai.get('voltage_v', 0):5.2f}V"
        f"{_note(notes,'voltage_v')}",
        f"  kedalaman={g.nilai.get('depth_m', 0):6.2f}m"
        f"{_note(notes,'depth_m')}",
        f"  suhu_depth={g.nilai.get('depth_temp_c', 0):6.1f}C"
        f"{_note(notes,'depth_temp_c')}",
        f"  roll={g.nilai.get('roll_deg', 0):6.1f} deg"
        f"{_note(notes,'roll_deg')}",
        f"  pitch={g.nilai.get('pitch_deg', 0):6.1f} deg"
        f"{_note(notes,'pitch_deg')}",
        f"  yaw={g.nilai.get('yaw_deg', 0):6.1f} deg"
        f"{_note(notes,'yaw_deg')}",
        f"  motor(open={g.motor_open},close={g.motor_close})",
        f"  altimeter={int(g.nilai.get('altimeter_dist_mm', 0))}mm "
        f"(conf {int(g.nilai.get('altimeter_conf_pct', 0))}%)"
        + (_note(notes, "altimeter_dist_mm")
           or _note(notes, "altimeter_conf_pct")),
        f"  seq={g.seq}  cnt={g.cnt}{peringatan}",
    ]
    aneh = g.tak_wajar()
    if aneh:
        # Nilai di luar rentang fisis paling sering berarti PETA FIELD
        # yang bergeser, bukan sensor rusak: angkanya masuk akal untuk
        # besaran LAIN. Itu justru gejala yang paling mudah terlewat.
        baris.append("  ! di luar rentang fisis: " + "; ".join(aneh)
                     + "  <- curigai peta field bergeser>")
    return "\n".join(baris)


def run(host: str, port: int, raw_only: bool = False,
        n_frames: Optional[int] = None, verify_checksum: bool = True,
        medium: Optional[str] = None) -> None:
    print(f"Menyambung ke buoy {host}:{port} ...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print("Tersambung.")

    reader = LineBufferedSocketReader(sock)
    n_ok = 0
    n_err = 0
    t0 = time.time()

    try:
        while True:
            try:
                lines = reader.readlines(timeout_s=5.0)
            except socket.timeout:
                print(f"[WARN] tidak ada data {5.0:.0f}s -- masih menunggu...",
                      file=sys.stderr)
                continue

            for line in lines:
                if raw_only:
                    print(f"MENTAH: {line}")
                    continue
                try:
                    sentence_id, fields = parse_nmea_frame(line)
                except (NmeaFrameError, NmeaChecksumError) as exc:
                    n_err += 1
                    print(f"[GALAT] {exc}", file=sys.stderr)
                    continue

                if sentence_id != "GDAT2":
                    print(f"[INFO] sentence {sentence_id} belum didekode "
                          f"(hanya GDAT2 diimplementasikan) -- field mentah: {fields}")
                    continue

                try:
                    g = decode_gdat2(fields)
                except (NmeaFrameError, ValueError) as exc:
                    n_err += 1
                    print(f"[GALAT] gagal urai GDAT2: {exc}", file=sys.stderr)
                    continue

                n_ok += 1
                dt = time.time() - t0
                print(f"[{dt:7.2f}s] GDAT2 #{n_ok}")
                print(_fmt_frame(g, medium=medium))

                if n_frames is not None and n_ok >= n_frames:
                    print(f"\n{n_frames} frame GDAT2 valid tercapai -- berhenti.")
                    return

    except KeyboardInterrupt:
        print("\nDihentikan operator (Ctrl+C).")
    except ConnectionError as exc:
        print(f"[ERROR] {exc}")
    finally:
        sock.close()
        print(f"Socket ditutup. Ringkasan: {n_ok} frame valid, {n_err} galat.")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Uji koneksi + urai telemetri buoy aux_vcu (NMEA-style, GDAT2).")
    ap.add_argument("--buoy", type=int, choices=sorted(BUOY_IPS), default=1,
                    help=f"Nomor buoy terdaftar aktif ({sorted(BUOY_IPS)}). "
                         "Abaikan bila --host dipakai.")
    ap.add_argument("--host", type=str, default=None,
                    help="Override alamat IP langsung (mengabaikan --buoy).")
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--raw", action="store_true",
                    help="Cetak baris mentah saja, jangan urai (setara v1).")
    ap.add_argument("--n-frames", type=int, default=None,
                    help="Berhenti setelah sekian frame GDAT2 valid (default: tanpa batas).")
    ap.add_argument("--medium", choices=["air", "sea"], default=None,
                    help="Tandai konteks uji: 'air' (uji-bangku, depth/altimeter "
                         "wajar nol) atau 'sea' (deploy, semua field harus hidup). "
                         "Default: tanpa anotasi.")
    args = ap.parse_args()

    if args.host:
        host = args.host
    elif args.buoy in BUOY_IPS:
        host = BUOY_IPS[args.buoy]
    else:
        # Buoy dikenal secara skema (2-4) tapi sengaja dinonaktifkan di
        # BUOY_IPS -- pesan ini beda dari "buoy tak dikenal" supaya operator
        # tahu harus uncomment, bukan mengira nomor buoy salah ketik.
        print(f"[ERROR] Buoy {args.buoy} dikenal skema alamatnya "
              f"(192.168.3.{100 + args.buoy*10}) tapi belum di-uncomment di "
              f"BUOY_IPS -- aktifkan dulu setelah buoy itu terverifikasi online, "
              f"atau pakai --host langsung.")
        sys.exit(1)

    run(host, args.port, raw_only=args.raw, n_frames=args.n_frames,
        medium=args.medium)


if __name__ == "__main__":
    main()