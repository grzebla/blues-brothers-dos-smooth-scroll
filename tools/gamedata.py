"""Dane o obsługiwanym wydaniu The Blues Brothers (DOS, Titus 1991).

Wydanie: wersja angielska na dysk twardy, scrackowana przez TDT/TRSI
(RUNME.COM, INTRO.EXE, JOHN/OH/TERRY.SQZ pochodzą od crackerów).
Wszystkie sumy SHA-256 zweryfikowane na plikach z The-Blues-Brothers_DOS_EN.zip.
"""
import hashlib
import os

# nazwa: (rozmiar, sha256)
KNOWN_FILES = {
    '1.EXE': (196608, '769ee254b154a9444205524ec4b28a8147a372ac5b2cee2e25fcd83aa90d0add'),
    'AVTEGOU.SQV': (2685, '88d8d76f197160dec5f1f614a17eb95537004f158cad803ff1ebcd7b07dbf4c4'),
    'AVTENT.SQV': (2067, '3862870389d22df220bd6913a47b08edac2e004e9def844b66a50051abf4defa'),
    'AVTMAG.SQV': (3069, 'c58322fb78b9b158eb7d27fb1f26d0625433a6114554af608bc18a86999cc84f'),
    'AVTPRIS.SQV': (3219, '6179977757ab30587938ee6f4d257eadc48ae7c36d072736b04e027315c19c4d'),
    'AVTVILLE.SQV': (2113, '4cef021bae03c6f0a7144e97e32b9a63503b6ee5b8f48620b738ecd9797c5b5a'),
    'CHOIX.SQZ': (12557, '3e5bb89dc179b021e5018516d87d45091d9f6a854a06b224b61b55c890c1f559'),
    'CONCERT.BIN': (2560, '7de67ab61fd732ea24b4099e68850125d068345dfabc628207acb8dd7b15654c'),
    'CONCERT.CK1': (9487, 'd42caf2b60301cd74332bacf0eb02e4a0484d6e764ff0611566a7a79962fc1cf'),
    'CONCERT.CK2': (10229, '8d2322873aedee85af940f159704c204559e97ed8ec00a60e658fee87289faba'),
    'CONCERT.SQL': (4523, 'eb3aeff2e4799fb27184b88d9f5fb36ba47d860319c8227a1d012d4e16924cb3'),
    'DEMO1.BIN': (1024, '99e5ea79546293d6025142afdd275213e2ccf349ec733339661895267f560d6c'),
    'DEMO2.BIN': (1024, '046cdafc1979a73d84c52d07a0590ca500f8731cb8d498a86d1feae28f3b68a5'),
    'DEMO3.BIN': (1024, 'd5644ece357a1cc1a2acc5807042a24c5ce93cdf31599e7d8e4fa25ea1022194'),
    'EGOU.BIN': (2560, '7fdf48e615a1e45e7ddbc6a1c511a0b7f1ece80a7b832a96e7f915e577c6f2e2'),
    'EGOU.CK1': (13685, 'f1a910ee89bac7c47ae049ca89e7bb732fbfe2caae6d00adf5b6bc9c5a35afd0'),
    'EGOU.CK2': (12964, '5e932b35342af285be8d599c5827a780b88dff14807c4addc9b1010f180481ce'),
    'EGOU.SQL': (6746, '66a85d59459299ece4a252a2352044acb61ced3b9315c17f1e9854abac06a4f8'),
    'ENEMI1.SQV': (14619, '29ac326a89e6975e3266f67775b8a6035297be59cebb0cd597a1bb24a7d85b15'),
    'ENEMI2.SQV': (12952, '6f39c2a4ae06dd2a7e9cc6f8053026bf3aefa6b75cc739736f18af327f755ef9'),
    'ENEMI3.SQV': (11135, '8a681e114090f799acd066ee0689650f9968cab4419b45f1149e6a8389fd69e8'),
    'ENEMI4.SQV': (7957, 'a5165ec672ca147758e832348da950e0eb4e13a10df370b4ffeb1cdfb81410d4'),
    'ENEMI5.SQV': (12143, 'f3997e16b7a3f8594b6eabe2f654171c2d8fb7937b047b4cf5b5eaadd961d8e4'),
    'ENEMI6.SQV': (5108, 'f64c33ef8c393a004cbaaf91ddeb7ecb3f59e4c42a014cf2c45360060e6ef892'),
    'ENT.CK1': (13892, '52f248f8f195e47b7912403ad1026b4f9e83bc7d7901e209a910ac7383a4dc76'),
    'ENT.CK2': (10606, 'aa652759baa1606a66d33cc4893221ac222b64fba5f9a7f4d4ab9dc60706eb51'),
    'ENT.SQL': (5830, '7958d185aba7474107dce556c9a33ecdd07711656542b0adafac552fda5926dc'),
    'ENTREPOT.BIN': (2560, 'ae3e73eb5b0d0088eb253a3bda101aabd112b7ef429bbc843bea3487d84b7036'),
    'HARD.COM': (14, '17821199d08b8c74601ea199647bb7f4a0482b2e8b34a6ad12b79c97529c9aee'),
    'INSERT.SQZ': (4984, 'd98ba86535c3c2f989f8c01fd56f924c2dcafd031133110fa1702ada9d0611f9'),
    'INTER.SQZ': (22364, '2560ea27e0d47d478ba904a8a45f3186cb5ad96e49595d879ee8c844140e112c'),
    'INTRO.EXE': (16020, '41d8a6969d8932593b105f225cf3c69c5fd236e89b9190605262c91eebf1de61'),
    'JOHN.SQZ': (65822, 'c8ebd31ab0f2baa05ed18f96ca132bae20acf67ff040296561f12aceb6cbe577'),
    'MAG.CK1': (12633, '81211d28c9a4c9996c99a94e9151381c6000e2ccae728d411348b81771af735b'),
    'MAG.CK2': (13676, '00b9476c09a31dde166474f5555a485c5152cf95cc51ad2811d2f783cbd24699'),
    'MAG.SQL': (7154, '26ad729dcf0bef933955a8c833a178dfa87a812e74b4dfc6b4462fe4a9efcb49'),
    'MAGASIN.BIN': (2560, '72158766739aa3244bc05267144bf44d56003cdbb549a273f6fdc0d377140d79'),
    'OH.SQZ': (64000, 'c9ffd34fde5a681ccad2e185aa2e0a681b407a9275a535afff41099a792aac21'),
    'PRES.SQZ': (20180, '911bc83077f7006d1aa0b17ff260b29969f83227ccbc0e53e2e0318b643fbf89'),
    'PRISON.BIN': (2560, 'e3a733baf8a931068e7f024c70006a8588402612ae19ab4eebe34e2254e82867'),
    'PRISON.CK1': (15546, '314dfe146250efed30c422f8a0caa392e07667d6aebe2c547c08309a22f0fc2e'),
    'PRISON.CK2': (13194, '88e1b2bc7056d66c14907c10485332ea0162102066731a430e31362904e0a71d'),
    'PRISON.SQL': (7879, 'ef8334205b4ba5b1a3bcc91cf693b04f25a2331c821fe25b26097c7f466edc97'),
    'RUNME.COM': (1683, 'adf3cff695911c977adc6a920e500dbe117293bc3aae049024ee297aa7e86e15'),
    'SPRITE.SQV': (37622, '8f6222115f2675d4a755df217ba33f8d79faafcf65081ff87dccc8ad510cbb36'),
    'TERRY.SQZ': (4352, '22fe6709434b055ed28bd37814a128abc087329965f2e1a93cf881399dbfe314'),
    'VILLE.BIN': (2560, 'e970a667499b1b515e52a28a4baaac5fe1b91d8d692795b0221782742aa322fb'),
    'VILLE.CK1': (13178, '4afc66221259d36f13a39891847a5dac5cd512640fc4a0ebd70ef184a579d2d4'),
    'VILLE.CK2': (13534, '96eb406828e297562ed3a9a925d8c6c1de03a444ca40870669ede6d884bf8627'),
    'VILLE.SQL': (8955, '5de0b18cbb798b14a6721cd0312c31d30aa5eeb4269b6938193bdae05212e032'),
}

# pliki dodane przez grupę crackerską (cracktro) - gra z nich nie korzysta
CRACK_FILES = ['RUNME.COM', 'HARD.COM', 'INTRO.EXE', 'JOHN.SQZ', 'OH.SQZ', 'TERRY.SQZ']

LEVELS = [
    {'name': 'Sklep muzyczny', 'ck1': 'MAG.CK1', 'ck2': 'MAG.CK2', 'sql': 'MAG.SQL', 'bin': 'MAGASIN.BIN', 'avt': 'AVTMAG.SQV', 'enemies': 'ENEMI1.SQV'},
    {'name': 'Magazyn', 'ck1': 'ENT.CK1', 'ck2': 'ENT.CK2', 'sql': 'ENT.SQL', 'bin': 'ENTREPOT.BIN', 'avt': 'AVTENT.SQV', 'enemies': 'ENEMI2.SQV'},
    {'name': 'Więzienie', 'ck1': 'PRISON.CK1', 'ck2': 'PRISON.CK2', 'sql': 'PRISON.SQL', 'bin': 'PRISON.BIN', 'avt': 'AVTPRIS.SQV', 'enemies': 'ENEMI3.SQV'},
    {'name': 'Kanały', 'ck1': 'EGOU.CK1', 'ck2': 'EGOU.CK2', 'sql': 'EGOU.SQL', 'bin': 'EGOU.BIN', 'avt': 'AVTEGOU.SQV', 'enemies': 'ENEMI4.SQV'},
    {'name': 'Miasto (budowa)', 'ck1': 'VILLE.CK1', 'ck2': 'VILLE.CK2', 'sql': 'VILLE.SQL', 'bin': 'VILLE.BIN', 'avt': 'AVTVILLE.SQV', 'enemies': 'ENEMI5.SQV'},
    {'name': 'Koncert', 'ck1': 'CONCERT.CK1', 'ck2': 'CONCERT.CK2', 'sql': 'CONCERT.SQL', 'bin': 'CONCERT.BIN', 'avt': None, 'enemies': 'ENEMI6.SQV'},
]

# ekrany pełnoekranowe ładowane funkcją 003A:07E4 (bitplany dekodowane pod +30000)
SCREEN_FILES = ['PRES.SQZ', 'CHOIX.SQZ', 'INTER.SQZ', 'INSERT.SQZ']
ILBM_FILES = SCREEN_FILES + [l['ck1'] for l in LEVELS] + [l['ck2'] for l in LEVELS]

# limity wynikające z kodu 1.EXE
SCREEN_ILBM_MAX = 30000       # obraz ILBM po dekompresji musi zmieścić się przed offsetem 30000
BUFFER_SIZE = 64000           # bufory alokowane funkcją 48h (0xFA0 paragrafów)
SPRITE_SQV_MAX = 64000        # SPRITE.SQV ładowany do bufora [0x885C]
MAX_DOS_OVERRUN = 1           # oryginalne pliki generują do 1 bajtu nadmiaru

# font cyfr 8x8, 4 płaszczyzny po 8 bajtów, cyfry 0-9 (offset w pliku 1.EXE)
DIGIT_FONT_FILE_OFFSET = 0xE4DA

# segment danych DGROUP: DS=0x0FC0, nagłówek MZ 0x2200 bajtów
EXE_HEADER_SIZE = 0x2200
EXE_DS_PARA = 0x0FC0


def ds_to_file(off):
    return EXE_HEADER_SIZE + EXE_DS_PARA * 16 + off


# Teksty w plikach wykonywalnych (offsety w pliku, rozmiar obszaru w bajtach)
EXE_TEXTS = [
    {'id': 'exe.video_error', 'file': '1.EXE', 'offset': ds_to_file(0x3388), 'size': 17},
    {'id': 'exe.out_of_memory', 'file': '1.EXE', 'offset': ds_to_file(0x3399), 'size': 19},
    {'id': 'exe.invalid_disk', 'file': '1.EXE', 'offset': ds_to_file(0x592A), 'size': 21},
    {'id': 'runme.line_groups', 'file': 'RUNME.COM', 'offset': 0x339, 'size': 58},
    {'id': 'runme.line_presents', 'file': 'RUNME.COM', 'offset': 0x376, 'size': 45},
    {'id': 'runme.line_title', 'file': 'RUNME.COM', 'offset': 0x3A6, 'size': 50},
    {'id': 'runme.line_ega', 'file': 'RUNME.COM', 'offset': 0x427, 'size': 38},
    {'id': 'runme.line_vga', 'file': 'RUNME.COM', 'offset': 0x450, 'size': 38},
    {'id': 'runme.line_intro', 'file': 'RUNME.COM', 'offset': 0x479, 'size': 52},
    {'id': 'runme.exit_message', 'file': 'RUNME.COM', 'offset': 0x55E, 'size': 30},
]


def sha256_file(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def identify(src):
    """Porównuje katalog z listą znanych plików."""
    res = {'files': {}, 'missing': [], 'mismatch': [], 'unknown': []}
    present = {n.upper(): n for n in os.listdir(src)} if os.path.isdir(src) else {}
    for name, (size, digest) in sorted(KNOWN_FILES.items()):
        real = present.get(name)
        if real is None:
            res['missing'].append(name)
            continue
        path = os.path.join(src, real)
        h = sha256_file(path)
        info = {'size': os.path.getsize(path), 'sha256': h, 'ok': h == digest,
                'origin': 'crack' if name in CRACK_FILES else 'titus'}
        res['files'][name] = info
        if h != digest:
            res['mismatch'].append(name)
    for up, real in present.items():
        if up not in KNOWN_FILES:
            res['unknown'].append(real)
    return res


def find_file(src, name):
    """Zwraca ścieżkę pliku niezależnie od wielkości liter."""
    for n in os.listdir(src):
        if n.upper() == name.upper():
            return os.path.join(src, n)
    raise FileNotFoundError(os.path.join(src, name))
