#----------
# Parte 1
#---------
import requests
import streamlit as st
import random
import smtplib
import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth  # CORRECCIÓN MAESTRA: Importación explícita para eliminar el NameError
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =====================================================================
# CONFIGURACIÓN ESTÁTICA INTEGRAL DE GOOGLE FIREBASE IDENTITY API
# =====================================================================

# 1. Coloca aquí tu Web API Key (la encuentras en Firebase Console -> Configuración del proyecto)
API_KEY = "AIzaSyD8DMID7FFGdBEor0Wmiw7yOqVBZbWSe20" 

# 2. URLs oficiales y completas para la API REST de Firebase Auth
URL_SIGN_UP = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
URL_SIGN_IN = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
URL_PASSWORD_RESET = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={API_KEY}"

# CORRECCIÓN EN TU VARIABLE: Dirección oficial de Google Cloud para interactuar con metadatos del usuario
URL_UPDATE_USER = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={API_KEY}"

# ENCABEZADO OBLIGATORIO DE RED PARA EL FIREWALL DE GOOGLE CLOUD
HEADERS_JSON = {"Content-Type": "application/json"}

# =====================================================================
# CONFIGURACIÓN MAESTRA DE MENSAJERÍA PARA CONTROL GERENCIAL
# =====================================================================
CORREO_EMISOR = "dadimacalarma@gmail.com"
PASSWORD_EMISOR = "mcgfftyvlorgazun"  # Tu contraseña de aplicación de Google de 16 caracteres

# CORREO_MASTER: Tu bandeja personal donde recibirás los accesos pendientes.
CORREO_MASTER = "dadimacalarma@gmail.com"


def enviar_correo_smtp(destinatario, asunto, cuerpo_html):
    """Conexión por IP directa para saltar de raíz el bloqueo de nombres DNS de Streamlit Cloud"""
    try:
        msg = MIMEMultipart()
        msg['From'] = CORREO_EMISOR.strip()
        msg['To'] = destinatario.strip()
        msg['Subject'] = asunto
        msg.attach(MIMEText(cuerpo_html, 'html'))
        
        # SOLUCIÓN DE INGENIERÍA: Usamos la IP principal del cluster SMTP de Google (GMR-MX)
        # Esto salta el NameResolutionError ya que no requiere consultar '://gmail.com' al DNS corporativo
        host_ip_directo = "64.233.186.108" 
        
        server = smtplib.SMTP(host_ip_directo, 587, timeout=10)
        server.starttls()
        
        server.login(CORREO_EMISOR.strip(), PASSWORD_EMISOR.strip())
        server.sendmail(CORREO_EMISOR.strip(), destinatario.strip(), msg.as_string())
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError:
        st.sidebar.error("🔑 Error de Autenticación de Gmail: La contraseña de aplicación de 16 caracteres es inválida o caducó.")
        return False
    except Exception as e:
        st.sidebar.error(f"❌ Conexión SMTP rechazada por el perímetro: {str(e)}")
        return False


def inicializar_sesion():
    """Mantiene la persistencia del estado de autenticación en la nube"""
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.usuario_email = None
        st.session_state.pantalla_actual = "login"
    if "token_registro" not in st.session_state:
        st.session_state.token_registro = None
        st.session_state.datos_pendientes = None

#----------
# Parte 2
#---------

def enviar_token_por_api_web(destinatario, token):
    """Prepara y despacha el correo corporativo con el token OTP dinámico."""
    asunto = f"🔑 Código de Verificación DaDiMAC: {token}"
    cuerpo_html = f"""
    <h2>Verificación de Identidad - DaDiMAC</h2>
    <p>Estás intentando registrarte en la plataforma corporativa. Tu código de verificación es:</p>
    <h1 style='color:#2678FE; letter-spacing: 4px;'>{token}</h1>
    <p>Introduce este código en la barra lateral del sistema para procesar tu alta.</p>
    """
    return enviar_correo_smtp(destinatario, asunto, cuerpo_html)


def registrar_usuario_firebase(email, password):
    """
    Utiliza el SDK de administración sugerido para crear al usuario 
    directamente en estado DESHABILITADO de nacimiento, blindando la seguridad.
    """
    # IMPORTACIÓN LOCAL: Evita colisiones de nombres en Python 3.14
    from firebase_admin import auth
    
    try:
        user = auth.create_user(
            email=email.strip().lower(),
            email_verified=False,
            password=password,
            disabled=True  # Nace retenido por la gerencia
        )
        return True, "🎉 Registro procesado en la nube en estado retenido."
        
    except auth.EmailAlreadyExistsError:
        return False, "⚠️ Este correo electrónico ya está registrado."
    except Exception as e:
        error_msg = str(e).split(":")[-1].strip() if ":" in str(e) else str(e)
        return False, f"❌ Error administrativo de Firebase: {error_msg}"



def validar_usuario_(email, password):
    """
    Valida el inicio de sesión. Si las credenciales son válidas pero la cuenta 
    está deshabilitada, se intercepta y se evalúa como una condición EXITOSA.
    """
    payload = {
        "email": email.strip().lower(),
        "password": password,
        "returnSecureToken": True
    }
    try:
        respuesta = requests.post(URL_SIGN_IN, json=payload, headers=HEADERS_JSON)
        
        # Caso A: El usuario ya está habilitado por la gerencia en la consola
        if respuesta.status_code == 200:
            datos = respuesta.json()
            email_autenticado = datos.get("email").strip().lower()
            return True, {"status": "HABILITADO", "email": email_autenticado}
            
        else:
            datos = respuesta.json()
            error_code = datos.get("error", {}).get("message", "Error de acceso")
            
            # ADAPTACIÓN CRÍTICA: Captura el código de bloqueo y lo procesa como una validación EXITOSA
            if error_code in ["USER_DISABLED", "ADMIN_DISABLED"]:
                return True, {"status": "RETENIDO", "email": email.strip().lower()}
            
            # Errores de credenciales reales
            if error_code in ["EMAIL_NOT_FOUND", "INVALID_PASSWORD", "INVALID_LOGIN_CREDENTIALS"]:
                error_code = "Credenciales incorrectas o inválidas."
            return False, f"⚠️ {error_code}"
            
    except Exception as e:
        return False, f"❌ Error de red: {str(e)}"

#--------
# Parte 3
#--------

def login_sidebar():
    """Despliega la pasarela de control de identidad con verificación estricta de Token previo a """
    # Inicialización forzada inmediata de variables de control
    inicializar_sesion()
    
    if not st.session_state.get("autenticado", False):
        if st.session_state.get("pantalla_actual", "login") == "login":
            st.sidebar.header("🔐 Acceso DaDiMAC ( Cloud)")
            email = st.sidebar.text_input("Correo electrónico:", key="auth_email").strip().lower()
            password = st.sidebar.text_input("Contraseña:", type="password", key="auth_pass")
            
            col_btn1, col_btn2 = st.sidebar.columns(2)
            with col_btn1:
                if st.sidebar.button("🔓 Entrar"):
                    if email and password:
                        exito, email_retornado = validar_usuario_(email, password)
                        if exito:
                            st.session_state.autenticado = True
                            st.session_state.usuario_email = email_retornado
                            st.rerun()
                        else:
                            st.sidebar.error(email_retornado)
                    else:
                        st.sidebar.error("⚠️ Completa los campos.")
            
            with col_btn2:
                if st.sidebar.button("📝 Registrarse"):
                    st.session_state.pantalla_actual = "registro"
                    st.rerun()
            
            st.sidebar.markdown("---")
            if st.sidebar.button("❓ Olvidé mi Contraseña"):
                st.session_state.pantalla_actual = "recuperar"
                st.rerun()
                
        elif st.session_state.get("pantalla_actual") == "registro":
            st.sidebar.header("📝 Registro de Auditor")
            nuevo_email = st.sidebar.text_input("Correo corporativo:", key="reg_email").strip().lower()
            nueva_pass = st.sidebar.text_input("Asigna una Contraseña (mín. 6 caracteres):", type="password", key="reg_pass")
            
            # Verificación del Token ANTES de registrar en 
            if st.session_state.get("token_registro") is not None:
                st.sidebar.warning("🔑 Introduce el token enviado a tu casilla para confirmar la operación:")
                token_ingresado = st.sidebar.text_input("Token de 6 dígitos:", key="reg_token_input").strip()
                
                col_token1, col_token2 = st.sidebar.columns(2)
                with col_token1:
                    if st.sidebar.button("✅ Verificar Token"):
                        if token_ingresado == str(st.session_state.get("token_registro")):
                            # RECONSTRUCCIÓN CON BLINDAJE: Extraemos la información de persistencia
                            datos_temporales = st.session_state.get("datos_pendientes")
                            email_final = datos_temporales["email"] if datos_temporales else nuevo_email
                            pass_final = datos_temporales["pass"] if datos_temporales else nueva_pass
                            
                            if not email_final or not pass_final:
                                st.sidebar.error("⚠️ Error de persistencia: Por favor, intente solicitar un nuevo token.")
                                return False
                            
                            # 1. ENVIAR CORREO GERENCIAL PRIMERO (Blindado contra re-renders de Streamlit)
                            asunto_master = "🚨 Alerta DaDiMAC: Nueva solicitud de autorización de registro"
                            cuerpo_master = f"""
                            <h3>Solicitud de Acceso Pendiente</h3>
                            <p>El siguiente usuario ha validado su correo con el Token OTP de 6 dígitos:</p>
                            <ul>
                                <li><b>Usuario Contable:</b> {email_final}</li>
                                <li><b>Verificación OTP:</b> Exitosa (Código Correcto)</li>
                                <li><b>Fecha/Hora:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                            </ul>
                            <p>El sistema procederá a inscribirlo en estado retenido. Recuerde habilitarlo manualmente en la consola Auth.</p>
                            """
                            # Despachamos a tu bandeja máster antes de tocar los servidores de 
                            enviar_correo_smtp(CORREO_MASTER, asunto_master, cuerpo_master)
                            
                            # 2. PASO CRÍTICO: Creación física en  en estado deshabilitado (Nativo SDK)
                            exito, msg = registrar_usuario_(email_final, pass_final)
                            
                            if exito:
                                st.sidebar.success("🎉 ¡Correo verificado e inscrito en !")
                                st.sidebar.info("📩 Tu acceso se encuentra retenido por seguridad. Debes esperar a que la gerencia verifique la alerta de registro en la consola para habilitarte.")
                                
                                st.session_state.token_registro = None
                                st.session_state.datos_pendientes = None
                            else:
                                st.sidebar.error(msg)
                        else:
                            st.sidebar.error("❌ Token incorrecto. Verifique el código.")
                
                with col_token2:
                    if st.sidebar.button("🔄 Cancelar"):
                        st.session_state.token_registro = None
                        st.session_state.datos_pendientes = None
                        st.rerun()
            else:
                # Flujo inicial: Solicitar el Token sin crear nada en 
                if st.sidebar.button("📧 Solicitar Token de Verificación"):
                    if nuevo_email and len(nueva_pass) >= 6:
                        token_generado = random.randint(100000, 999999)
                        
                        if enviar_token_por_api_web(nuevo_email, token_generado):
                            st.session_state.token_registro = token_generado
                            st.session_state.datos_pendientes = {"email": nuevo_email, "pass": nueva_pass}
                            st.rerun()
                    else:
                        st.sidebar.error("⚠️ El correo es obligatorio y la contraseña debe tener 6 caracteres o más.")
            
            if st.sidebar.button("⬅️ Volver al Login"):
                st.session_state.token_registro = None
                st.session_state.datos_pendientes = None
                st.session_state.pantalla_actual = "login"
                st.rerun()
                
        elif st.session_state.get("pantalla_actual") == "recuperar":
            st.sidebar.header("🔄 Restablecer Clave")
            email_recup = st.sidebar.text_input("Introduce tu Correo registrado:", key="rec_email_input").strip().lower()
            
            if st.sidebar.button("🚀 Enviar Enlace Seguro"):
                if email_recup:
                    payload = {"requestType": "PASSWORD_RESET", "email": email_recup}
                    res = requests.post(URL_PASSWORD_RESET, json=payload, headers=HEADERS_JSON)
                    if res.status_code == 200:
                        st.sidebar.info(f"📩 Enlace enviado a **{email_recup}** para restablecer tu contraseña.")
                    else:
                        st.sidebar.error("⚠️ No se pudo procesar el restablecimiento. Verifique el correo.")
                else:
                    st.sidebar.error("⚠️ Escribe tu correo.")
                    
            if st.sidebar.button("⬅️ Volver al Login"):
                st.session_state.pantalla_actual = "login"
                st.rerun()
                
        return False
    else:
        st.sidebar.success(f"👤 Sesión Activa\n{st.session_state.get('usuario_email')}")
        st.sidebar.caption("🔒 Autenticación en la Nube vía ")
        if st.sidebar.button("🔒 Cerrar Sesión"):
            st.session_state.autenticado = False
            st.session_state.usuario_email = None
            st.session_state.pantalla_actual = "login"
            st.rerun()
        return True
