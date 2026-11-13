import os, sys, time, random, subprocess, textwrap, requests
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

HORAS = [8, 11, 14, 17, 20]  # 8am, 11am, 2pm, 5pm, 8pm hora de Florida
IG_TOKEN = os.environ["IG_TOKEN"]
IG_USER_ID = os.environ["IG_USER_ID"]
OPENAI_KEY = os.environ["OPENAI_API_KEY"]
REPO = os.environ["GITHUB_REPOSITORY"]
API = "https://graph.facebook.com/v21.0"

ahora = datetime.now(ZoneInfo("America/New_York"))
if os.environ.get("FORZAR") != "si" and ahora.hour not in HORAS:
    print("No es hora de publicar:", ahora.strftime("%I:%M %p"))
    sys.exit(0)

anteriores = []
if os.path.exists("frases.txt"):
    anteriores = open("frases.txt", encoding="utf-8").read().splitlines()[-60:]

instrucciones = (
    "Escribe en español UNA sola frase corta y original de calle, del bajo mundo, "
    "con sabiduría real de la calle: lealtad, respeto, traición, falsos amigos, "
    "hambre de salir adelante, la familia, el barrio, aprender a golpes. "
    "Lenguaje de calle latino, crudo y auténtico, pero sin hacer apología de la "
    "violencia, las armas ni las drogas, para que Instagram no la censure. "
    "Máximo 25 palabras. Sin comillas, sin hashtags, sin emojis. "
    "No repitas ni parafrasees ninguna de estas:\n" + "\n".join(anteriores)
)
r = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {OPENAI_KEY}"},
    json={"model": "gpt-4o-mini", "temperature": 1.0,
          "messages": [{"role": "user", "content": instrucciones}]},
    timeout=60,
)
r.raise_for_status()
frase = r.json()["choices"][0]["message"]["content"].strip().strip('"“”')
print("Frase:", frase)

W, H = 1080, 1350
fondos = [((15, 15, 15), (60, 10, 10)), ((10, 10, 10), (40, 40, 40)),
          ((5, 5, 20), (70, 50, 0)), ((20, 0, 0), (0, 0, 0))]
c1, c2 = random.choice(fondos)
img = Image.new("RGB", (W, H))
d = ImageDraw.Draw(img)
for y in range(H):
    t = y / H
    d.line([(0, y), (W, y)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))

ruta_fuente = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
tam = 72
while True:
    fuente = ImageFont.truetype(ruta_fuente, tam)
    lineas = textwrap.wrap(frase.upper(), width=max(10, int(1700 / tam)))
    alto = len(lineas) * int(tam * 1.3)
    if alto < H * 0.6 or tam <= 40:
        break
    tam -= 4

y = (H - alto) // 2
for linea in lineas:
    ancho = d.textlength(linea, font=fuente)
    d.text(((W - ancho) / 2, y), linea, font=fuente, fill="white",
           stroke_width=2, stroke_fill="black")
    y += int(tam * 1.3)

pie = ImageFont.truetype(ruta_fuente, 34)
marca = "@frases_brava_24k"
d.text(((W - d.textlength(marca, font=pie)) / 2, H - 110), marca, font=pie, fill=(200, 160, 40))

os.makedirs("imagenes", exist_ok=True)
nombre = ahora.strftime("%Y%m%d_%H%M") + ".jpg"
img.save(f"imagenes/{nombre}", "JPEG", quality=92)
with open("frases.txt", "a", encoding="utf-8") as f:
    f.write(frase + "\n")

subprocess.run(["git", "config", "user.name", "bot"], check=True)
subprocess.run(["git", "config", "user.email", "bot@users.noreply.github.com"], check=True)
subprocess.run(["git", "add", "imagenes", "frases.txt"], check=True)
subprocess.run(["git", "commit", "-m", f"Frase {nombre}"], check=True)
subprocess.run(["git", "push"], check=True)
time.sleep(20)

url = f"https://raw.githubusercontent.com/{REPO}/main/imagenes/{nombre}"
texto = frase + "\n\n#frases #frasesdecalle #calle #realidad #lealtad #barrio #motivacion"
r = requests.post(f"{API}/{IG_USER_ID}/media",
                  data={"image_url": url, "caption": texto, "access_token": IG_TOKEN})
print(r.json())
r.raise_for_status()
contenedor = r.json()["id"]

time.sleep(10)
r = requests.post(f"{API}/{IG_USER_ID}/media_publish",
                  data={"creation_id": contenedor, "access_token": IG_TOKEN})
print(r.json())
r.raise_for_status()
print("¡Publicada!")
