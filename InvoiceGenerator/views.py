from django.shortcuts import render
from xhtml2pdf import pisa
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from django.http import HttpResponse
from django.template.loader import get_template
from io import BytesIO
import tempfile
from django.conf import settings
import os



def index(request):
    return render(request, 'Form.html')  # Renderiza el template 'index.html'

def enviar_email(destinatario, archivo_adjunto):
    # Configura los detalles del servidor SMTP
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  # Puerto SMTP (usualmente 587 o 465 para SSL)
    smtp_user = 'joaquin.castilloh12@gmail.com'  # Correo electrónico del remitente
    smtp_password = 'nvse itqb miil tasu'  # Contraseña del correo electrónico del remitente

    # Configura el mensaje de correo electrónico
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = destinatario
    msg['Subject'] = 'Factura adjunta'

    # Adjunta el archivo PDF al mensaje de correo electrónico
    with open(archivo_adjunto, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(archivo_adjunto))
        msg.attach(part)

    # Establece la conexión con el servidor SMTP y envía el correo electrónico
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error al enviar el correo electrónico:", str(e))
        return False

def procesar_formulario(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '')
        apellido = request.POST.get('apellido', '')
        cedula = request.POST.get('cedula', '')
        email = request.POST.get('email', '')
        metodo = request.POST.get('metodo', '')

        # Generar el PDF
        pdf_content = generar_pdf(nombre, apellido, cedula, email, metodo)
        
        # Si se generó correctamente el PDF
        if pdf_content:
            # Crear un archivo temporal para guardar el PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                temp_pdf.write(pdf_content)
                temp_pdf_path = temp_pdf.name

            # Enviar el PDF adjunto por correo electrónico
            if enviar_email(email, temp_pdf_path):
                # Eliminar el archivo temporal después de enviar el correo
                os.unlink(temp_pdf_path)
                return HttpResponse('El PDF ha sido enviado por correo electrónico.')
            else:
                return HttpResponse('Error al enviar el correo electrónico.')
        else:
            return HttpResponse('Error al generar el PDF')
    else:
        return HttpResponse('El formulario no fue enviado.')


def generar_pdf(nombre, apellido, cedula, email, metodo):
    # Ruta de la plantilla HTML
    template_path = 'Factura.html'

    # Cargar la plantilla HTML
    template = get_template(template_path)

    # Renderizar la plantilla HTML con los datos del formulario
    html_string = template.render({'nombre': nombre, 'apellido': apellido, 'cedula': cedula, 'email': email, 'metodo': metodo})

    # Convertir HTML a PDF
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=pdf_file)

    # Verificar si la creación del PDF fue exitosa
    if not pisa_status.err:
        # Si no hay errores, devolver el contenido del PDF
        pdf_file.seek(0)
        return pdf_file.getvalue()
    else:
        # Si hay errores, devolver None
        return None
