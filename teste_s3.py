import boto3

# Conecta no Floci local usando as credenciais fictícias da prática
s3 = boto3.client(
    "s3",
    endpoint_url="http://127.0.0.1:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)

BUCKET = "telemetria-lab"

# 1. Cria o bucket
s3.create_bucket(Bucket=BUCKET)
print(f"Bucket '{BUCKET}' criado!")

# 2. Faz upload do JSON LoRa
s3.upload_file("medicao.json", BUCKET, "estacao-01/medicao.json")
print("Upload de estacao-01/medicao.json concluído!")

# 3. Lista os objetos no bucket
resp = s3.list_objects_v2(Bucket=BUCKET, Prefix="estacao-01/")
print("Arquivos encontrados:", [obj["Key"] for obj in resp.get("Contents", [])])

# 4. Baixa de volta para conferir
s3.download_file(BUCKET, "estacao-01/medicao.json", "baixado.json")
print("Download concluído como 'baixado.json'!")