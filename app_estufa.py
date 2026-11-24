import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import time
import plotly.express as px
import boto3
from datetime import datetime

# 1. Configuração da Página
st.set_page_config(
    page_title="Telemetria IoT", 
    page_icon="🌱", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# Ocultar menu padrão do Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 2. Inicializa a flag de controle de acesso
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# =========================================================
# TELA DE LOGIN 
# =========================================================
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.write("")
        st.write("")
        st.title("🔒 Acesso Restrito")
        st.markdown("**Laboratório**")
        
        with st.form("form_login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            btn_entrar = st.form_submit_button("Entrar", use_container_width=True)
            
            if btn_entrar:
                if usuario == "admin" and senha == "admin":
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("⚠️ Credenciais inválidas.")
    
    st.stop() 

# =========================================================
# CONFIGURAÇÃO S3 (FLOCI LOCAL)
# =========================================================
BUCKET_S3 = "telemetria-lab"

@st.cache_resource
def iniciar_s3():
    return boto3.client(
        "s3",
        endpoint_url="http://127.0.0.1:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
    )

cliente_s3 = iniciar_s3()

def salvar_no_s3(df_dados):
    try:
        cliente_s3.create_bucket(Bucket=BUCKET_S3)
    except Exception:
        pass  # Bucket já existe

    nome_chave = f"estufa/telemetria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    payload = {
        "estacao": "estufa-principal",
        "total_amostras": len(df_dados),
        "amostras": df_dados.to_dict(orient="records"),
    }
    conteudo_json = json.dumps(payload, ensure_ascii=False, indent=2)
    cliente_s3.put_object(
        Bucket=BUCKET_S3,
        Key=nome_chave,
        Body=conteudo_json.encode("utf-8"),
        ContentType="application/json",
    )
    return nome_chave

# =========================================================
# CONFIGURAÇÃO MQTT E MEMÓRIA
# =========================================================
@st.cache_resource
def obter_caixa_de_correio():
    return []

caixa_de_correio = obter_caixa_de_correio()

if 'historico' not in st.session_state:
    st.session_state.historico = pd.DataFrame(
        columns=["timestamp", "dht22_temp_c", "dht22_umidade_pct", "ldr_lux", "bateria_pct"]
    )
if 'alerta_h_ativo' not in st.session_state:
    st.session_state.alerta_h_ativo = False
if 'alerta_t_ativo' not in st.session_state:
    st.session_state.alerta_t_ativo = False

def ao_receber_mensagem(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        caixa_de_correio.append(payload)
    except:
        pass

@st.cache_resource
def iniciar_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = ao_receber_mensagem
    client.connect("broker.hivemq.com", 1883, 60) 
    client.subscribe("empresa/produto/estufa/telemetria")
    client.loop_start()
    return client

cliente_mqtt = iniciar_mqtt()

# =========================================================
# BARRA LATERAL (FERRAMENTAS E LOGOUT)
# =========================================================
with st.sidebar:
    if st.button("Desconectar (Logout) 🔒", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()
        
    st.divider()
    st.subheader("Parâmetros de Alerta")
    limite_temp = st.slider("Teto Térmico (°C)", min_value=20.0, max_value=40.0, value=28.0, step=0.5)
    limite_umi = st.slider("Piso Hídrico (%)", min_value=20.0, max_value=80.0, value=40.0, step=1.0)
    
    st.divider()
    st.subheader("Controle Manual")
    if st.button("Ligar Bomba 💧", use_container_width=True):
        payload_bomba = json.dumps({"comando": "LIGAR_BOMBA", "origem": "manual"})
        cliente_mqtt.publish("empresa/produto/estufa/comandos", payload_bomba)
        st.toast("Comando de Irrigação enviado!", icon="✅")
        
    if st.button("Ligar Ventoinha 🌬️", use_container_width=True):
        payload_ventoinha = json.dumps({"comando": "LIGAR_VENTOINHA", "origem": "manual"})
        cliente_mqtt.publish("empresa/produto/estufa/comandos", payload_ventoinha)
        st.toast("Comando de Ventilação enviado!", icon="✅")

    st.divider()
    st.subheader("Exportar Dados")
    if not st.session_state.historico.empty:
        csv = st.session_state.historico.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descarregar CSV (.csv)",
            data=csv,
            file_name='dados_estufa_litel.csv',
            mime='text/csv',
            use_container_width=True
        )
    else:
        st.info("A aguardar dados do sensor...")

    st.divider()
    st.subheader("☁️ Nuvem S3 (Floci)")
    if not st.session_state.historico.empty:
        if st.button("Salvar Snapshot no S3", use_container_width=True):
            try:
                chave_salva = salvar_no_s3(st.session_state.historico)
                st.toast(f"Salvo no S3: {chave_salva}", icon="☁️")
            except Exception as e:
                st.error(f"Erro ao conectar no Floci: {e}")

    with st.expander("Arquivos no Bucket"):
        try:
            resp = cliente_s3.list_objects_v2(Bucket=BUCKET_S3, Prefix="estufa/")
            arquivos = [obj["Key"] for obj in resp.get("Contents", [])]
            if arquivos:
                for arq in arquivos:
                    st.code(arq, language=None)
            else:
                st.caption("Nenhum snapshot salvo ainda.")
        except Exception:
            st.warning("Floci offline na porta 4566.")

# =========================================================
# DASHBOARD PRINCIPAL
# =========================================================
st.title("🌱 Plataforma de Telemetria IoT")
st.markdown("Monitorização assíncrona, controle bidirecional e análise do microclima.")

if len(caixa_de_correio) > 0:
    mensagens_recebidas = caixa_de_correio.copy()
    caixa_de_correio.clear()
    
    if len(mensagens_recebidas) > 0:
        novos_dados = pd.DataFrame(mensagens_recebidas)
        st.session_state.historico = pd.concat(
            [st.session_state.historico, novos_dados], ignore_index=True
        ).tail(100)

if not st.session_state.historico.empty:
    df = st.session_state.historico.copy()
    atual = df.iloc[-1]
    
    delta_temp = round(atual['dht22_temp_c'] - df.iloc[-2]['dht22_temp_c'], 2) if len(df) > 1 else 0
    delta_umi = round(atual['dht22_umidade_pct'] - df.iloc[-2]['dht22_umidade_pct'], 2) if len(df) > 1 else 0
    
    st.subheader("Indicadores em Tempo Real")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Temperatura", f"{atual['dht22_temp_c']} °C", f"{delta_temp} °C", delta_color="inverse")
    with col2:
        st.metric("Umidade Relativa", f"{atual['dht22_umidade_pct']} %", f"{delta_umi} %")
    with col3:
        st.metric("Iluminação Solar", f"{atual['ldr_lux']} Lux")
    with col4:
        st.metric("Integridade do Hardware (Bateria)", f"{atual['bateria_pct']} %")
        st.progress(atual['bateria_pct'] / 100.0)

    espaco_alertas = st.empty()
    with espaco_alertas.container():
        if atual['dht22_umidade_pct'] < limite_umi:
            st.error(f"💧 **ALERTA HÍDRICO:** Umidade crítica (abaixo de {limite_umi}%). Enviando comando: `LIGAR_BOMBA`")
            if not st.session_state.alerta_h_ativo:
                st.toast("Sistema de Irrigação Acionado!", icon="💧")
                st.session_state.alerta_h_ativo = True
        else:
            st.session_state.alerta_h_ativo = False

        if atual['dht22_temp_c'] > limite_temp:
            st.error(f"🔥 **ALERTA TÉRMICO:** Temperatura crítica (acima de {limite_temp}°C). Enviando comando: `LIGAR_VENTOINHA`")
            if not st.session_state.alerta_t_ativo:
                st.toast("Sistema de Ventilação Acionado!", icon="🌬️")
                st.session_state.alerta_t_ativo = True
        else:
            st.session_state.alerta_t_ativo = False
    
    st.divider()
    
    aba1, aba2 = st.tabs(["📊 Análise Térmica e Hídrica", "⚡ Energia e Luminosidade"])
    
    with aba1:
        fig_clima = px.line(
            df, x="timestamp", y=["dht22_temp_c", "dht22_umidade_pct"],
            labels={"value": "Medição", "timestamp": "Horário", "variable": "Sensor"},
            color_discrete_sequence=["#FF5733", "#339FFF"]
        )
        fig_clima.update_layout(hovermode="x unified", legend_title_text='')
        st.plotly_chart(fig_clima, use_container_width=True)
        
    with aba2:
        col_esq, col_dir = st.columns(2)
        with col_esq:
            fig_luz = px.area(
                df, x="timestamp", y="ldr_lux", title="Série Espectral (Lux)", color_discrete_sequence=["#FFC300"]
            )
            st.plotly_chart(fig_luz, use_container_width=True)
            
        with col_dir:
            fig_bat = px.line(
                df, x="timestamp", y="bateria_pct", title="Curva de Descarga (%)", color_discrete_sequence=["#28B463"]
            )
            fig_bat.update_layout(yaxis_range=[0, 105]) 
            st.plotly_chart(fig_bat, use_container_width=True)
else:
    with st.spinner("A Sincronizar com o Broker MQTT..."):
        time.sleep(1)

time.sleep(1)
st.rerun()