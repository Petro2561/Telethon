import io
from pathlib import Path
import zipfile
import rarfile


async def extract_rar_to_dir(rar_bytes: io.BytesIO, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    rar_bytes.seek(0)
    extracted = 0
    try:
        with zipfile.ZipFile(rar_bytes) as zf:
            for name in zf.namelist():
                if name.endswith("/"):
                    continue
                data = zf.read(name)
                (output_dir / Path(name).name).write_bytes(data)
                extracted += 1
            print("После ZIP-распаковки получили:", [p.name for p in output_dir.iterdir()])
            return int(extracted/2)
    except zipfile.BadZipFile:
        pass

    with rarfile.RarFile(rar_bytes) as rf:
        for info in rf.infolist():
            name = Path(info.filename).name
            with rf.open(info) as f_in:
                data = f_in.read()
            (output_dir / name).write_bytes(data)
            extracted += 1
        return int(extracted/2)
