import requests
import streamlit as st
 
# =====================================================================
# CREDENCIALES CLOUD CORPORATIVAS (GOOGLE FIREBASE)
# =====================================================================
API_KEY_FIREBASE = "AIzaSyD8DMID7FFGdBEor0Wmiw7yOqVBZbWSe20"
AUTH_DOMAIN_FIREBASE = "dadimac-62fd6.firebaseapp.com"

# RUTAS OFICIALES REPARADAS DE GOOGLE IDENTITY TOOLKIT
URL_SIGN_IN = f"https://googleapis.com{API_KEY_FIREBASE}"
URL_SIGN_UP = f"https://googleapis.com{API_KEY_FIREBASE}"
URL_PASSWORD_RESET = f"https://googleapis.com{API_KEY_FIREBASE}"

def inicializar_sesion():
    """Mantiene la persistencia del estado de autenticación en la nube"""
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.usuario_email = None
        st.session_state.pantalla_actual = "login"

def enviar_correo_restablecimiento(email):
    """Dispara un correo electrónico automatizado de recuperación de clave vía Firebase Auth"""
    payload = {
        "requestType": "PASSWORD_RESET",
        "email": email
    }
    try:
        respuesta = requests.post(URL_PASSWORD_RESET, json=payload)
        datos = respuesta.json()
        if respuesta.status_code == 200:
            return True, f"📩 Enlace enviado a **{email}**. Revisa tu bandeja de entrada o spam para restablecer tu contraseña."
        else:
            error_msg = datos.get("error", {}).get("message", "Error desconocido")
            return False, f"⚠️ Error de Firebase: {error_msg}"
    except Exception as e:
        return False, f"❌ Error de red: {str(e)}"

def registrar_usuario_firebase(email, password):
    """Inscribe un nuevo operador contable en tu base de datos de Firebase"""
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    try:
        respuesta = requests.post(URL_SIGN_UP, json=payload)
        datos = respuesta.json()
        if respuesta.status_code == 200:
            return True, "🎉 Cuenta registrada con éxito."
        else:
            error_msg = datos.get("error", {}).get("message", "Error al registrar")
            if error_msg == "EMAIL_EXISTS":
                error_msg = "Este correo electrónico ya está registrado."
            return False, f"⚠️ {error_msg}"
    except Exception as e:
        return False, f"❌ Error de red: {str(e)}"

def validar_usuario_firebase(email, password):
    """Valida el inicio de sesión contra los servidores en la nube de Firebase"""
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    try:
        respuesta = requests.post(URL_SIGN_IN, json=payload)
        datos = respuesta.json()
        if respuesta.status_code == 200:
            return True, datos.get("email")
        else:
            error_msg = datos.get("error", {}).get("message", "Error de acceso")
            if error_msg in ["EMAIL_NOT_FOUND", "INVALID_PASSWORD", "INVALID_LOGIN_CREDENTIALS"]:
                error_msg = "Credenciales incorrectas o inválidas."
            return False, f"⚠️ {error_msg}"
    except Exception as e:
        return False, f"❌ Error de red: {str(e)}"

def login_sidebar():
    """Despliega la pasarela de control de identidad en la barra lateral"""
    inicializar_sesion()
    
    if not st.session_state.autenticado:
        if st.session_state.pantalla_actual == "login":
            st.sidebar.header("🔐 Acceso DaDiMAC (Firebase Cloud)")
            email = st.sidebar.text_input("Correo electrónico:", key="auth_email").strip().lower()
            password = st.sidebar.text_input("Contraseña:", type="password", key="auth_pass")
            
            col_btn1, col_btn2 = st.sidebar.columns(2)
            with col_btn1:
                if st.sidebar.button("🔓 Entrar"):
                    if email and password:
                        exito, email_retornado = validar_usuario_firebase(email, password)
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
                
        elif st.session_state.pantalla_actual == "registro":
            st.sidebar.header("📝 Registro de Auditor")
            nuevo_email = st.sidebar.text_input("Correo corporativo:", key="reg_email").strip().lower()
            nueva_pass = st.sidebar.text_input("Asigna una Contraseña (mín. 6 caracteres):", type="password", key="reg_pass")
            
            if st.sidebar.button("💾 Crear Cuenta"):
                if nuevo_email and len(nueva_pass) >= 6:
                    exito, msg = registrar_usuario_firebase(nuevo_email, nueva_pass)
                    if exito:
                        st.sidebar.success(msg)
                        st.session_state.pantalla_actual = "login"
                        st.rerun()
                    else:
                        st.sidebar.error(msg)
                else:
                    st.sidebar.error("⚠️ El correo es obligatorio y la contraseña debe tener 6 caracteres o más.")
                    
            if st.sidebar.button("⬅️ Volver al Login"):
                st.session_state.pantalla_actual = "login"
                st.rerun()
                
        elif st.session_state.pantalla_actual == "recuperar":
            st.sidebar.header("🔄 Restablecer Clave")
            email_recup = st.sidebar.text_input("Introduce tu Correo registrado:", key="rec_email_input").strip().lower()
            
            if st.sidebar.button("🚀 Enviar Enlace Seguro"):
                if email_recup:
                    exito, mensaje = enviar_correo_restablecimiento(email_recup)
                    if exito:
                        st.sidebar.info(mensaje)
                    else:
                        st.sidebar.error(mensaje)
                else:
                    st.sidebar.error("⚠️ Escribe tu correo.")
                    
            if st.sidebar.button("⬅️ Volver al Login"):
                st.session_state.pantalla_actual = "login"
                st.rerun()
                
        return False
    else:
        st.sidebar.success(f"👤 Sesión Activa\n{st.session_state.usuario_email}")
        st.sidebar.caption("🔒 Autenticación en la Nube vía Firebase")
        if st.sidebar.button("🔒 Cerrar Sesión"):
            st.session_state.autenticado = False
            st.session_state.usuario_email = None
            st.session_state.pantalla_actual = "login"
            st.rerun()
        return True
