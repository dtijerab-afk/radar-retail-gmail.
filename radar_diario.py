import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# 1. Credenciales seguras desde GitHub Secrets
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")
DESTINO_EMAIL = os.environ.get("DESTINO_EMAIL", GMAIL_USER)

# Fecha actual en hora de Colombia (UTC-5)
colombia_tz = timezone(timedelta(hours=-5))
hoy = datetime.now(colombia_tz).strftime("%d/%m/%Y")

def generar_reporte_html():
    """Consulta Gemini con Google Search Grounding para obtener noticias y enlaces reales de hoy."""
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
    Hoy es {hoy} en Barranquilla, Colombia.
    Usa búsqueda en Google para redactar un informe ejecutivo diario en HTML limpio (solo el contenido interior del <body>, con estilos inline profesionales de fondo oscuro #0b1528, texto claro #f1f5f9 y botones celestes #38bdf8 para abrir cada enlace).

    Incluye 3 secciones claras con hechos REALES y recientes (últimas 24-48 horas):
    1. RETAIL COLOMBIA & BARRANQUILLA (3 noticias clave: D1, Ara, Ísimo, Olímpica, Éxito, DANE o Fenalco) + recuadro breve de "Impacto para el Jefe de Operaciones".
    2. RETAIL VENEZUELA & M&A (2 noticias reales de fusiones, adquisiciones, ANSA o expansión de cadenas colombianas en Venezuela).
    3. VACANTES SENIOR BARRANQUILLA (2 ofertas activas en retail, operaciones o dirección comercial > $7.000.000 COP en Barranquilla).

    REGLAS ESTRICTAS:
    - Cada noticia y vacante DEBE incluir un botón o enlace HTML (<a href="URL_REAL" target="_blank">) con la URL exacta y verificada de la fuente encontrada.
    - NO inventes enlaces ni fechas. Si un día no hay novedad en una sección, indícalo brevemente.
    - Devuelve únicamente código HTML válido sin bloques de markdown (```html).
    """

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            temperature=0.2,
        ),
    )

    contenido = response.text.strip()
    # Limpia delimitadores de markdown si el modelo los incluyó
    if contenido.startswith("```"):
        contenido = contenido.split("\n", 1)[1]
    if contenido.endswith("```"):
        contenido = contenido.rsplit("```", 1)[0]
    return contenido.strip()

def enviar_gmail(html_cuerpo):
    """Envía el reporte ejecutivo por Gmail usando SMTP SSL (puerto 465)."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 Radar Retail Barranquilla & M&A — {hoy} (6:00 PM)"
    msg["From"] = f"Radar Retail Bot <{GMAIL_USER}>"
    msg["To"] = DESTINO_EMAIL

    html_completo = f"""
    <!DOCTYPE html>
    <html lang="es">
    <body style="margin:0;padding:16px;background-color:#070d19;color:#f1f5f9;font-family:Arial,Helvetica,sans-serif;">
      <div style="max-width:680px;margin:0 auto;background:#0b1528;border:1px solid #162644;border-radius:14px;padding:20px;">
        <div style="border-bottom:1px solid #162644;padding-bottom:12px;margin-bottom:16px;">
          <h1 style="margin:0;font-size:20px;color:#38bdf8;">Radar Retail Colombia &amp; Venezuela</h1>
          <p style="margin:4px 0 0 0;font-size:12px;color:#94a3b8;">Cierre Diario 6:00 PM · {hoy} · Enfoque Barranquilla &amp; M&amp;A</p>
        </div>
        {html_cuerpo}
        <p style="margin-top:20px;padding-top:12px;border-top:1px solid #162644;font-size:11px;color:#64748b;">
          Enviado automáticamente por tu Bot Radar Retail (GitHub Actions + Gemini Search).
        </p>
      </div>
    </body>
    </html>
    """

    msg.attach(MIMEText("Abre este correo en un cliente compatible con HTML para ver tu Radar Retail.", "plain", "utf-8"))
    msg.attach(MIMEText(html_completo, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, [DESTINO_EMAIL], msg.as_string())
    print(f"Reporte enviado correctamente a {DESTINO_EMAIL}")

if __name__ == "__main__":
    html_reporte = generar_reporte_html()
    enviar_gmail(html_reporte)
