import os, sys, time, base64, random, colorsys, subprocess, requests
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HORAS = [8, 11, 14, 17, 20]  # hora de Florida
IG_TOKEN = os.environ["IG_TOKEN"]
IG_USER_ID = os.environ["IG_USER_ID"]
OPENAI_KEY = os.environ["OPENAI_API_KEY"]
REPO = os.environ["GITHUB_REPOSITORY"]
API = "https://graph.facebook.com/v21.0"
MARCA = "@frases_brava_24k"
W, H = 1080, 1350

ahora = datetime.now(ZoneInfo("America/New_York"))
if os.environ.get("FORZAR") != "si" and ahora.hour not in HORAS:
    print("No es hora de publicar:", ahora.strftime("%I:%M %p"))
    sys.exit(0)

# ---------------- FRASE ----------------
anteriores = []
if os.path.exists("frases.txt"):
    anteriores = open("frases.txt", encoding="utf-8").read().splitlines()[-60:]

instrucciones = (
    "Escribe en español UNA sola frase corta y original de calle, del bajo mundo, "
    "con sabiduría real de la calle: lealtad, respeto, traición, falsos amigos, "
    "hambre de salir adelante, la familia, el barrio, aprender a golpes. "
    "Lenguaje de calle latino, crudo y auténtico, pero sin hacer apología de la "
    "violencia, las armas ni las drogas, para que Instagram no la censure. "
    "Máximo 20 palabras. Sin comillas, sin hashtags, sin emojis. "
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

# ---------------- FONDO CON IA ----------------
ESCENAS = [
    "a dark wet city street at night with neon reflections",
    "a black luxury car parked in an alley with stacks of cash on the hood",
    "gold chains and gold bars on a dark wooden table, dramatic light",
    "a brick wall with red paint dripping like graffiti, moody light",
    "an empty basketball court in the hood at dusk, chain-link fence",
    "a lowrider car under a streetlight at night, smoke in the air",
    "stacks of hundred dollar bills on a dark marble table",
    "a rainy back alley with a single flickering streetlight",
    "a city skyline at night seen from a rooftop, cinematic",
    "a graffiti covered subway tunnel with dramatic shadows",
    "a gold watch and cash on a black leather car seat",
    "an old concrete wall with dark red paint splashes and cracks",
    "a corner store at night with neon signs in a latino neighborhood",
    "a matte black sports car in an underground parking garage",
    "a stairwell in an old apartment building with harsh light",
    "a pile of gold coins glowing in darkness",
    "a street corner in the barrio at sunset, palm trees silhouettes",
    "a dark room with a single light bulb and money on the table",
    "train tracks at night with fog and red lights",
    "a vintage muscle car on an empty highway at night",
    "a wall covered in torn posters and red spray paint",
    "a chess board with gold pieces in dramatic dark lighting",
    "a fire escape in a city alley at night, rain falling",
    "a briefcase full of cash on a car hood, night city behind",
    "a dark bridge over a river with city lights",
    "a cracked mirror on a grimy wall, red neon light",
    "a motorcycle parked on a wet street under neon lights",
    "a black and gold abstract smoke background, luxury mood",
    "an old boxing gym with a hanging heavy bag, gritty light",
    "a dark street mural of a lion in gold and red paint",
]

def fondo_ia():
    escena = random.choice(ESCENAS)
    prompt = (f"Photorealistic, cinematic, dark and moody: {escena}. "
              "Vertical composition. No people's faces, no text, no letters, no logos, no weapons.")
    print("Escena:", escena)
    r = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {OPENAI_KEY}"},
        json={"model": "dall-e-3", "prompt": prompt, "size": "1024x1792",
              "response_format": "b64_json", "n": 1},
        timeout=120,
    )
    r.raise_for_status()
    datos = base64.b64decode(r.json()["data"][0]["b64_json"])
    img = Image.open(BytesIO(datos)).convert("RGB")
    escala = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * escala) + 1, int(img.height * escala) + 1))
    x = (img.width - W) // 2
    y = (img.height - H) // 2
    return img.crop((x, y, x + W, y + H))

def fondo_color():
    def color(v):
        rgb = colorsys.hsv_to_rgb(random.random(), random.uniform(0.5, 1), v)
        return tuple(int(c * 255) for c in rgb)
    mascara = Image.linear_gradient("L").resize((W, H))
    return Image.composite(Image.new("RGB", (W, H), color(0.45)),
                           Image.new("RGB", (W, H), color(0.08)), mascara)

try:
    img = fondo_ia()
except Exception as e:
    print("Falló la imagen de IA, uso color:", e)
    img = fondo_color()

# oscurecer para que se lea la frase
img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), 0.45)
d = ImageDraw.Draw(img)

# ---------------- TEXTO ----------------
NEGRITA = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FINA = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
MARGEN = 90
ANCHO_MAX = W - 2 * MARGEN

def partir(texto, fuente):
    lineas, actual = [], ""
    for p in texto.split():
        prueba = (actual + " " + p).strip()
        if d.textlength(prueba, font=fuente) <= ANCHO_MAX:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas

texto = frase.upper()
tam = 84
while True:
    fuente = ImageFont.truetype(NEGRITA, tam)
    lineas = partir(texto, fuente)
    cabe_ancho = all(d.textlength(l, font=fuente) <= ANCHO_MAX for l in lineas)
    alto = len(lineas) * int(tam * 1.3)
    if (cabe_ancho and alto < H * 0.6) or tam <= 32:
        break
    tam -= 4

y = (H - alto) // 2
for linea in lineas:
    ancho = d.textlength(linea, font=fuente)
    d.text(((W - ancho) / 2, y), linea, font=fuente, fill="white",
           stroke_width=3, stroke_fill="black")
    y += int(tam * 1.3)

# ---------------- MARCA DE AGUA ----------------
capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dc = ImageDraw.Draw(capa)
pie = ImageFont.truetype(FINA, 36)
ancho_marca = dc.textlength(MARCA, font=pie)
dc.text(((W - ancho_marca) / 2, H - 100), MARCA, font=pie, fill=(255, 255, 255, 230))
img = Image.alpha_composite(img.convert("RGBA"), capa).convert("RGB")

# ---------------- GUARDAR Y SUBIR ----------------
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

# ---------------- PUBLICAR EN INSTAGRAM ----------------
url = f"https://raw.githubusercontent.com/{REPO}/main/imagenes/{nombre}"
caption = frase + "\n\n#frases #frasesdecalle #calle #realidad #lealtad #barrio #motivacion"

r = requests.post(f"{API}/{IG_USER_ID}/media",
                  data={"image_url": url, "caption": caption, "access_token": IG_TOKEN})
print(r.json())
r.raise_for_status()
contenedor = r.json()["id"]
time.sleep(10)

r = requests.post(f"{API}/{IG_USER_ID}/media_publish",
                  data={"creation_id": contenedor, "access_token": IG_TOKEN})
print(r.json())
r.raise_for_status()
print("¡Publicada!")
